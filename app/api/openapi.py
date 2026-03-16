from typing import Any

from app.api.schemas import ErrorResponse


def json_example(example: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": {
            "application/json": {
                "example": example,
            }
        }
    }


def build_error_response(
    *,
    description: str,
    code: str,
    message: str,
) -> dict[str, Any]:
    return {
        "model": ErrorResponse,
        "description": description,
        **json_example(
            {
                "code": code,
                "message": message,
            }
        ),
    }


HEALTH_RESPONSES: dict[int, Any] = {
    200: {
        "description": "Service is healthy",
        **json_example({"status": "ok"}),
    }
}

LOOKUP_ERROR_RESPONSES: dict[int, Any] = {
    422: build_error_response(
        description="Invalid IP address",
        code="invalid_ip",
        message="Invalid IP address",
    ),
    404: build_error_response(
        description="Geolocation not found",
        code="geo_not_found",
        message="Geolocation not found for ip=203.0.113.10",
    ),
    502: build_error_response(
        description="External provider error",
        code="external_service_error",
        message="Provider 'ipapi' failed after 3 attempts",
    ),
    500: build_error_response(
        description="Internal server error",
        code="internal_server_error",
        message="Internal server error",
    ),
}
