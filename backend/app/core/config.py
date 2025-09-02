# backend/app/core/config.py
"""
Configuration for SchoolFlow using Pydantic BaseSettings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, AnyUrl
from typing import Optional


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

    # wkhtmltopdf
    wkhtmltopdf_cmd: str = Field("", env="WKHTMLTOPDF_CMD")

    # SMTP (MailHog default)
    smtp_host: str = Field("localhost", env="SMTP_HOST")
    smtp_port: int = Field(1025, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    smtp_from: str = Field("school@schoolflow.local", env="SMTP_FROM")

    # Providers
    provider_mode: str = Field("fake", env="PROVIDER_MODE")
    razorpay_key_id: Optional[str] = Field(None, env="RAZORPAY_KEY_ID")
    razorpay_key_secret: Optional[str] = Field(None, env="RAZORPAY_KEY_SECRET")
    razorpay_webhook_secret: Optional[str] = Field(None, env="RAZORPAY_WEBHOOK_SECRET")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
