"""Configuration management."""
import os
from typing import Literal

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/sourcing_mcp")

    # Server
    MCP_SERVER_NAME: str = os.getenv("MCP_SERVER_NAME", "sourcing")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Storage
    STORAGE_BACKEND: Literal["local", "s3"] = os.getenv("STORAGE_BACKEND", "local")  # type: ignore
    STORAGE_LOCAL_PATH: str = os.getenv("STORAGE_LOCAL_PATH", "/tmp/sourcing-mcp/uploads")
    STORAGE_S3_BUCKET: str = os.getenv("STORAGE_S3_BUCKET", "")
    STORAGE_S3_REGION: str = os.getenv("STORAGE_S3_REGION", "us-west-2")

    # External Services
    FX_PROVIDER: str = os.getenv("FX_PROVIDER", "mock")
    FX_API_KEY: str = os.getenv("FX_API_KEY", "")

    VERIFICATION_PROVIDER: str = os.getenv("VERIFICATION_PROVIDER", "mock")

    # Communication
    WECOM_CORP_ID: str = os.getenv("WECOM_CORP_ID", "")
    WECOM_AGENT_ID: str = os.getenv("WECOM_AGENT_ID", "")
    WECOM_SECRET: str = os.getenv("WECOM_SECRET", "")

    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "43200"))

    # Rate limiting
    RFQ_DAILY_QUOTA: int = int(os.getenv("RFQ_DAILY_QUOTA", "5"))


config = Config()
