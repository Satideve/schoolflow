# backend/app/core/config.py

"""
Configuration for SchoolFlow using Pydantic BaseSettings.
"""
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env manually for dotenv-aware tools
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


class Settings(BaseSettings):
    # App
    app_name: str = "SchoolFlow"
    host: str = Field("0.0.0.0", env="APP_HOST")
    port: int = Field(8000, env="APP_PORT")

    # Database
    database_url: str = Field(..., env="DATABASE_URL")

    # JWT / Security
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")  
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")       

    # wkhtmltopdf: path to the binary inside the container
    wkhtmltopdf_cmd: str = Field("/usr/bin/wkhtmltopdf", env="WKHTMLTOPDF_CMD")      

    # SMTP (MailHog default)
    smtp_host: str = Field("localhost", env="SMTP_HOST")
    smtp_port: int = Field(1025, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    smtp_from: str = Field("school@schoolflow.local", env="SMTP_FROM")

    # Payment Providers
    provider_mode: str = Field("fake", env="PROVIDER_MODE")
    razorpay_key_id: Optional[str] = Field(None, env="RAZORPAY_KEY_ID")
    razorpay_key_secret: Optional[str] = Field(None, env="RAZORPAY_KEY_SECRET")      
    razorpay_webhook_secret: Optional[str] = Field(
        None, env="RAZORPAY_WEBHOOK_SECRET"
    )

    # Paths
    # Base dir should point to the backend root (…/backend)
    base_dir: Optional[str] = Field(None, env="BASE_DIR")
    # receipts_dir: str = Field("app/data/receipts", env="RECEIPTS_DIR")
    # invoices_dir: str = Field("app/data/invoices", env="INVOICES_DIR")

    receipts_dir: str = Field("data/receipts", env="RECEIPTS_DIR")
    invoices_dir: str = Field("data/invoices", env="INVOICES_DIR")

    # CORS
    cors_origins: List[str] = Field(default_factory=list, env="CORS_ORIGINS")        
    cors_allow_credentials: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        env="CORS_ALLOW_METHODS",
    )
    cors_allow_headers: List[str] = Field(
        default_factory=lambda: ["Authorization", "Content-Type"],
        env="CORS_ALLOW_HEADERS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # -------- Validators --------

    @field_validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        if not v or len(v.strip()) < 16:
            raise ValueError("SECRET_KEY must be set and at least 16 characters")    
        return v

    @field_validator("access_token_expire_minutes")
    def validate_token_expiry(cls, v: int) -> int:
        if v <= 0 or v > 1440:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 1440")
        return v

    @field_validator("base_dir")
    def validate_or_default_base_dir(cls, v: Optional[str]) -> str:
        default_backend = Path(__file__).resolve().parents[2]
        base = Path(v).resolve() if v else default_backend
        if not base.exists() or not base.is_dir():
            raise ValueError(f"BASE_DIR does not exist or is not a directory: {base}")
        if not (base / "app").exists():
            raise ValueError(f"BASE_DIR missing expected 'app' directory: {base}")   
        return str(base)

    @field_validator("cors_origins", mode="before")
    def parse_cors_origins(cls, v) -> List[str]:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @field_validator("cors_allow_methods", mode="before")
    def parse_cors_methods(cls, v) -> List[str]:
        if isinstance(v, str):
            return [s.strip().upper() for s in v.split(",") if s.strip()]
        return v

    @field_validator("cors_allow_headers", mode="before")
    def parse_cors_headers(cls, v) -> List[str]:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    # -------- Helpers --------

    def resolve_path(self, relative_path: str) -> str:
        """
        Normalize a stored path string to an absolute path.

        Accepts values that may be:
        - absolute paths (e.g. '/app/backend/app/data/receipts/REC-...pdf')
        - relative paths that start with 'app/' (legacy)
        - other relative paths

        Strategy:
        - If `relative_path` is falsy -> return resolved base_dir.
        - If `relative_path` is absolute -> return its normalized absolute path.     
        - Otherwise join with base_dir and prefer an existing candidate if found.    
        - Try a fallback removing a leading 'app/' segment.
        - As a last attempt, look for any suffix of the provided path that exists under base_dir.
        - Returns a (string) absolute path. Caller should still check file existence if needed.
        """
        # guard against None/empty
        if not relative_path:
            return str(Path(self.base_dir).resolve())

        # Normalize separators and avoid accidental absolute join
        rel = str(relative_path).replace("\\", "/")

        p = Path(rel)
        # If user stored an absolute path, prefer and normalize it.
        if p.is_absolute():
            try:
                return str(p.resolve())
            except Exception:
                # fallback to no-resolve if something odd happens
                return str(p)

        # At this point path is relative; use base_dir as root
        base = Path(self.base_dir).resolve()

        # Candidate 1: base + rel (strip any leading '/')
        candidate = (base / rel.lstrip("/"))
        try:
            cand_resolved = candidate.resolve()
        except Exception:
            # resolve(strict=False) available but keep safe fallback
            try:
                cand_resolved = candidate.resolve(strict=False)
            except Exception:
                cand_resolved = candidate

        if cand_resolved.exists():
            return str(cand_resolved)

        # Candidate 2: if stored path starts with 'app/', try without that segment   
        if rel.startswith("app/"):
            alt = (base / rel[4:].lstrip("/"))
            try:
                alt_resolved = alt.resolve()
            except Exception:
                try:
                    alt_resolved = alt.resolve(strict=False)
                except Exception:
                    alt_resolved = alt
            if alt_resolved.exists():
                return str(alt_resolved)

        # Candidate 3: try progressive suffixes of the provided relative path        
        # e.g., stored 'some/extra/app/data/invoices/INV-...' -> try to find suffix under base
        parts = [p for p in rel.split("/") if p]
        for i in range(len(parts)):
            suffix = "/".join(parts[i:])
            cand = (base / suffix)
            try:
                cand_res = cand.resolve()
            except Exception:
                try:
                    cand_res = cand.resolve(strict=False)
                except Exception:
                    cand_res = cand
            if cand_res.exists():
                return str(cand_res)

        # If we couldn't find an existing file, return the primary candidate (normalized)
        try:
            return str(candidate.resolve(strict=False))
        except Exception:
            return str(candidate)

    def receipts_path(self) -> Path:
        """
        Returns the absolute Path to the receipts directory.

        Preference order:
          1) If an external data root exists at parent(base_dir)/data, use that:
               parent(base_dir)/data/<receipts-directory-name>
             e.g. when base_dir=/app/backend -> /app/data/receipts
          2) Fallback to the configured path under base_dir:
               base_dir / receipts_dir (legacy behavior)
        """
        base = Path(self.base_dir).resolve()
        # external data root candidate (outside backend dir, useful for container volumes)
        external_candidate = (base.parent / "data" / Path(self.receipts_dir).name)
        try:
            # If external candidate exists or can be created, prefer it
            if external_candidate.exists():
                return external_candidate.resolve()
        except Exception:
            pass
        # Fallback: keep legacy behavior
        return (base / self.receipts_dir).resolve()

    def invoices_path(self) -> Path:
        """
        Returns the absolute Path to the invoices directory.

        Preference order:
          1) parent(base_dir)/data/invoices  (e.g. /app/data/invoices when base_dir=/app/backend)
          2) base_dir / invoices_dir (legacy behavior)
        """
        base = Path(self.base_dir).resolve()
        external_candidate = (base.parent / "data" / Path(self.invoices_dir).name)
        try:
            if external_candidate.exists():
                return external_candidate.resolve()
        except Exception:
            pass
        return (base / self.invoices_dir).resolve()


def validate_startup(s: Settings) -> None:
    """
    Validates critical runtime assumptions and prepares directories.
    Raises ValueError on misconfiguration to fail-fast at startup.
    """
    # Primary (legacy) dirs under base_dir
    receipts_dir = s.receipts_path()
    invoices_dir = s.invoices_path()

    # Ensure primary directories exist (this will create base_dir-based dirs if needed)
    receipts_dir.mkdir(parents=True, exist_ok=True)
    invoices_dir.mkdir(parents=True, exist_ok=True)

    # Also attempt to ensure the external /app/data style directories exist
    # Only attempt creation if parent(base_dir)/data is writable/exists
    base = Path(s.base_dir).resolve()
    external_data_root = base.parent / "data"
    try:
        external_data_root.mkdir(parents=True, exist_ok=True)
        # Create external invoices/receipts subdirs
        (external_data_root / Path(s.invoices_dir).name).mkdir(parents=True, exist_ok=True)
        (external_data_root / Path(s.receipts_dir).name).mkdir(parents=True, exist_ok=True)
    except Exception:
        # Not fatal — leave it to runtime code to handle missing dirs if permissions prevent creation.
        pass

    # Verify write/read health (temp file round-trip)
    for d in (receipts_dir, invoices_dir):
        probe = d / ".healthcheck.tmp"
        try:
            probe.write_text("ok", encoding="utf-8")
            if probe.read_text(encoding="utf-8") != "ok":
                raise ValueError(f"Volume read mismatch in {d}")
        finally:
            if probe.exists():
                probe.unlink()


settings = Settings()
validate_startup(settings)
