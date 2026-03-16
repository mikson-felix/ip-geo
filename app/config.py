from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "geoip-service"
    debug: bool = False

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 900

    geoip_db_path: Path = Path("./GeoLite2-City.mmdb")

    ipapi_base_url: str = "https://ipapi.co"
    ipapi_timeout_seconds: float = 3.0
    ipapi_rate_limit_per_minute: int = 30
    ipapi_max_retries: int = 3

    ip_api_base_url: str = "http://ip-api.com"
    ip_api_timeout_seconds: float = 3.0
    ip_api_rate_limit_per_minute: int = 40
    ip_api_max_retries: int = 3

    external_backoff_base_seconds: float = Field(default=0.2, ge=0)
    external_backoff_multiplier: float = Field(default=2.0, ge=1.0)

    circuit_breaker_failure_threshold: int = Field(default=3, ge=1)
    circuit_breaker_recovery_timeout_seconds: float = Field(default=30.0, gt=0)

    log_level: str = "INFO"
    log_json: bool = True

    @field_validator("geoip_db_path")
    @classmethod
    def validate_geoip_db_path(cls, value: Path) -> Path:
        if value.exists() and not value.is_file():
            raise ValueError(f"GeoIP path exists but is not a file: {value}")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
