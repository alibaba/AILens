"""Tracing configuration."""

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from typing import Optional


class TracingSettings(BaseSettings):
    """Tracing settings."""

    # EagleEye configuration (Alibaba-internal, leave empty in open-source deployments)
    EAGLEEYE_AUTH_KEY: str = ""
    EAGLEEYE_BASE_URL: str = ""

    # Sunfire configuration (reserved)
    SUNFIRE_ENABLED: bool = False
    SUNFIRE_BASE_URL: str = ""

    # Trace configuration
    DEFAULT_TRACE_PROVIDER: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from environment


_settings: Optional[TracingSettings] = None


def get_settings() -> TracingSettings:
    """Get tracing settings singleton."""
    global _settings
    if _settings is None:
        _settings = TracingSettings()
    return _settings
