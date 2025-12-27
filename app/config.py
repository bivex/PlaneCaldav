# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-27T14:00:23
# Last Updated: 2025-12-27T14:05:45
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Configuration settings for CalPlaneBot."""

import secrets
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Import validation
from config.validation import validate_config


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env
    )

    # Application
    app_name: str = "CalPlaneBot"
    version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8765

    # Plane Configuration
    plane_base_url: str
    plane_api_token: str
    plane_workspace_slug: str = "default"

    # CalDAV Configuration
    caldav_url: str
    caldav_username: str
    caldav_password: str
    caldav_auth_type: str = "digest"  # "digest" or "basic"

    # Optional webhook configuration (for receiving Plane webhooks)
    plane_webhook_secret: Optional[str] = None

    # Sync Configuration
    sync_interval_seconds: int = 60  # 1 minute
    enable_sync: bool = True
    bidirectional_sync: bool = False  # Enable CalDAV → Plane sync

    # CalDAV Event Mapping
    event_default_duration_hours: int = 1
    event_timezone: str = "Europe/Moscow"

    # Cache Configuration
    cache_ttl_seconds: int = 3600  # 1 hour
    max_cache_size: int = 1000

    # Logging
    log_level: str = "INFO"

    # Webhook Settings (for receiving updates)
    webhook_timeout: int = 30
    max_retries: int = 3

    @property
    def plane_api_url(self) -> str:
        """Get full Plane API URL"""
        return f"{self.plane_base_url}/api/v1/"

    @field_validator("plane_base_url", "caldav_url")
    @classmethod
    def validate_urls(cls, v: str) -> str:
        """Ensure URLs are valid and end without trailing slash."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v.rstrip("/")

    @field_validator("plane_webhook_secret")
    @classmethod
    def validate_webhook_secret(cls, v: Optional[str]) -> Optional[str]:
        """Ensure webhook secret is not empty if provided."""
        if v is not None and len(v) < 32:
            raise ValueError("Webhook secret must be at least 32 characters long")
        return v

    @field_validator("caldav_auth_type")
    @classmethod
    def validate_caldav_auth_type(cls, v: str) -> str:
        """Ensure CalDAV auth type is valid."""
        valid_types = ["digest", "basic"]
        if v.lower() not in valid_types:
            raise ValueError(f"CalDAV auth type must be one of: {', '.join(valid_types)}")
        return v.lower()


# Global settings instance
settings = Settings()

# Validate configuration on import
try:
    validate_config()
except Exception as e:
    print(f"Configuration validation failed: {e}")
    raise

