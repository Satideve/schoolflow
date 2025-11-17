# C:\coding_projects\dev\schoolflow\backend\app\main.py

"""
FastAPI app factory for SchoolFlow with custom Swagger UI and static file mounts.
This modified version augments CORS origins at runtime to include a local frontend
origin for development (http://localhost:5173) if not already present.
It preserves all existing variable and function names and behaviour.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from uuid import uuid4
import os
from typing import List, Iterable, Union

from app.core.config import settings
from app.core.logging import setup_logging
from app.db import session as dbsession

# Import database models and engine for schema initialization
from app.db.base import load_all_models, Base
from app.db.session import engine

# Import the central API router aggregator
from app.api.v1.api import api_router


def _normalize_origins(origins: Union[Iterable[str], str, None]) -> List[str]:
    """
    Normalize various forms of settings.cors_origins into a list of strings.
    Accepts list/tuple of strings, single string, or None.
    """
    if origins is None:
        return []
    if isinstance(origins, (list, tuple)):
        return [str(x) for x in origins if x]
    # single string (comma separated?) — try to split on commas if present
    s = str(origins)
    if "," in s:
        return [p.strip() for p in s.split(",") if p.strip()]
    return [s] if s else []


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    # --- CORS setup (preserve settings but add local dev frontend origin safely) ---
    # Normalize the configured origins
    base_origins = _normalize_origins(settings.cors_origins)

    # Default local dev origin we want to support during frontend dev
    dev_origin = os.environ.get("DEV_FRONTEND_ORIGIN", "http://localhost:5173")

    # If dev origin is not already allowed, append it (without removing existing entries)
    if dev_origin and dev_origin not in base_origins:
        base_origins.append(dev_origin)

    # Keep the original settings' allow flags intact
    app.add_middleware(
        CORSMiddleware,
        allow_origins=base_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Request-ID Middleware: assign or propagate X-Request-ID
    @app.middleware("http")
    async def assign_request_id(request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    # Mount static directories for receipts and invoices
    app.mount(
        "/static/receipts",
        StaticFiles(directory=str(settings.receipts_path())),
        name="receipts",
    )
    app.mount(
        "/static/invoices",
        StaticFiles(directory=str(settings.invoices_path())),
        name="invoices",
    )

    # Include all versioned API routers
    app.include_router(api_router)

    # --- Custom OpenAPI: add Bearer token auth scheme ---
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=settings.app_name,
            version="0.1.0",
            description="SchoolFlow API",
            routes=app.routes,
        )
        openapi_schema["openapi"] = "3.0.0"

        components = openapi_schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }

        # Apply BearerAuth globally
        openapi_schema.setdefault("security", []).append({"BearerAuth": []})

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # --- Custom Swagger UI endpoint with PKCE support ---
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui() -> HTMLResponse:
        original_html = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{settings.app_name} – API Docs",
            swagger_js_url=(
                "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.18.2/"
                "swagger-ui-bundle.js"
            ),
            swagger_css_url=(
                "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.18.2/"
                "swagger-ui.css"
            ),
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_ui_parameters={
                "requestSnippetsEnabled": True,
                "requestSnippets": {"curl_powershell": True},
            },
        )

        injected = original_html.body.replace(
            b"</body>",
            b'''
            <script>
              window.ui.initOAuth({
                usePkceWithAuthorizationCodeGrant: true
              });
            </script>
            </body>
            ''',
        )

        return HTMLResponse(content=injected, status_code=200)

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    # Graceful startup: initialize DB schema for in-memory or file-based DB
    @app.on_event("startup")
    def on_startup():
        load_all_models()
        Base.metadata.create_all(bind=engine)

    # Graceful shutdown: remove DB sessions
    @app.on_event("shutdown")
    def on_shutdown():
        dbsession.SessionLocal.remove()

    return app


app = create_app()
