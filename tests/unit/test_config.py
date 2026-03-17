from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_accept_missing_mmdb_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.mmdb"

    settings = Settings(
        app_name="geoip-service-test",
        debug=False,
        redis_url="redis://localhost:6379/0",
        cache_ttl_seconds=900,
        geoip_db_path=missing_path,
        ipapi_base_url="https://ipapi.co",
        ipapi_timeout_seconds=3.0,
        ipapi_rate_limit_per_minute=30,
        ipapi_max_retries=3,
        ip_api_base_url="http://ip-api.com",
        ip_api_timeout_seconds=3.0,
        ip_api_rate_limit_per_minute=40,
        ip_api_max_retries=3,
        external_backoff_base_seconds=0.2,
        external_backoff_multiplier=2.0,
        circuit_breaker_failure_threshold=3,
        circuit_breaker_recovery_timeout_seconds=30.0,
        log_level="INFO",
        log_json=True,
    )

    assert settings.geoip_db_path == missing_path


def test_settings_fail_when_geoip_path_is_directory(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_name="geoip-service-test",
            debug=False,
            redis_url="redis://localhost:6379/0",
            cache_ttl_seconds=900,
            geoip_db_path=tmp_path,
            ipapi_base_url="https://ipapi.co",
            ipapi_timeout_seconds=3.0,
            ipapi_rate_limit_per_minute=30,
            ipapi_max_retries=3,
            ip_api_base_url="http://ip-api.com",
            ip_api_timeout_seconds=3.0,
            ip_api_rate_limit_per_minute=40,
            ip_api_max_retries=3,
            external_backoff_base_seconds=0.2,
            external_backoff_multiplier=2.0,
            circuit_breaker_failure_threshold=3,
            circuit_breaker_recovery_timeout_seconds=30.0,
            log_level="INFO",
            log_json=True,
        )
