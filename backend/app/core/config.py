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
    receipts_dir: str = Field("app/data/receipts", env="RECEIPTS_DIR")
    invoices_dir: str = Field("app/data/invoices", env="INVOICES_DIR")

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
        Resolve a relative path (e.g., 'app/data/receipts/RCT-...pdf') from base_dir.
        Keeps forward slashes and strips leading slash to avoid absolute joins.
        """
        rel = relative_path.replace("\\", "/").lstrip("/")
        return str((Path(self.base_dir) / rel).resolve())

    def receipts_path(self) -> Path:
        """
        Returns the absolute Path to the receipts directory.
        """
        return (Path(self.base_dir) / self.receipts_dir).resolve()

    def invoices_path(self) -> Path:
        """
        Returns the absolute Path to the invoices directory.
        """
        return (Path(self.base_dir) / self.invoices_dir).resolve()


def validate_startup(s: Settings) -> None:
    """
    Validates critical runtime assumptions and prepares directories.
    Raises ValueError on misconfiguration to fail-fast at startup.
    """
    receipts_dir = s.receipts_path()
    invoices_dir = s.invoices_path()
    receipts_dir.mkdir(parents=True, exist_ok=True)
    invoices_dir.mkdir(parents=True, exist_ok=True)

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
