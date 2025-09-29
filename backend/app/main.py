# backend/app/main.py

"""
FastAPI app factory for SchoolFlow with custom Swagger UI to enable request snippets.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse
from app.core.config import settings
from app.core.logging import setup_logging
from app.db import session as dbsession

# Import the central API router aggregator
from app.api.v1.api import api_router


def create_app():
    setup_logging()

    # Disable default docs/redoc; mount custom Swagger UI with snippets plugin
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    # CORS: allow local dev tools to call the API (e.g., swagger UI, frontend)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include all versioned API routers
    app.include_router(api_router)

    # --- Custom OpenAPI: add Bearer token auth scheme for Swagger UI ---
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=settings.app_name,
            version="0.1.0",
            description="SchoolFlow API",
            routes=app.routes,
        )
        # Force spec to OpenAPI 3.0.0 for compatibility with this Swagger UI
        openapi_schema["openapi"] = "3.0.0"

        openapi_schema.setdefault("components", {})
        openapi_schema["components"].setdefault("securitySchemes", {})
        openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
        # Apply Bearer security globally so Swagger's Authorize button accepts a token
        openapi_schema["security"] = [{"BearerAuth": []}]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # --- Custom Swagger UI endpoint using swagger-ui-dist@4.18.2 via CDN ---
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui() -> HTMLResponse:
        original_html = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{settings.app_name} – API Docs",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.18.2/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.18.2/swagger-ui.css",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_ui_parameters={
                "requestSnippetsEnabled": True,
                "requestSnippets": {
                    "curl_powershell": True,
                },
            },
        )

        # Inject the initOAuth script and return a new HTMLResponse
        injected_html = original_html.body.replace(
            b"</body>",
            b"""
            <script>
              window.ui.initOAuth({
                usePkceWithAuthorizationCodeGrant: true
              });
            </script>
            </body>
            """
        )

        return HTMLResponse(content=injected_html, status_code=200)
    
    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    # attach DB engine/session for graceful shutdown if needed
    @app.on_event("startup")
    def startup_event():
        # Could start scheduler here
        pass

    @app.on_event("shutdown")
    def shutdown_event():
        dbsession.SessionLocal.remove()

    return app


app = create_app()
