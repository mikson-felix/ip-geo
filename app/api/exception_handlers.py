from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from structlog import get_logger

from app.domain.exceptions import (
    ExternalServiceError,
    GeoLookupError,
    GeoNotFoundError,
    InvalidIPError,
    StartupCheckError,
)

logger = get_logger(__name__)


def _request_context(request: Request) -> dict[str, Any]:
    return {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_host": request.client.host if request.client else None,
    }


async def invalid_ip_exception_handler(
    request: Request,  # noqa: ARG001
    exc: InvalidIPError,
) -> JSONResponse:
    logger.warning(
        "invalid_ip_error",
        detail=str(exc),
        **_request_context(request),
    )
    return JSONResponse(
        status_code=422,
        content={"code": "invalid_ip", "message": str(exc)},
    )


async def geo_not_found_exception_handler(
    request: Request,  # noqa: ARG001
    exc: GeoNotFoundError,
) -> JSONResponse:
    logger.info(
        "geo_not_found",
        detail=str(exc),
        **_request_context(request),
    )
    return JSONResponse(
        status_code=404,
        content={"code": "geo_not_found", "message": str(exc)},
    )


async def startup_check_exception_handler(
    request: Request,  # noqa: ARG001
    exc: StartupCheckError,
) -> JSONResponse:
    logger.error(
        "startup_check_error",
        detail=str(exc),
        **_request_context(request),
    )
    return JSONResponse(
        status_code=503,
        content={"code": "startup_failure", "message": str(exc)},
    )


async def geo_lookup_exception_handler(
    request: Request,  # noqa: ARG001
    exc: GeoLookupError,
) -> JSONResponse:
    logger.error(
        "geo_lookup_error",
        detail=str(exc),
        **_request_context(request),
    )
    return JSONResponse(
        status_code=500,
        content={"code": "lookup_failure", "message": str(exc)},
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "unhandled_exception",
        detail=str(exc),
        **_request_context(request),
    )
    return JSONResponse(
        status_code=500,
        content={"code": "internal_server_error", "message": "Internal server error"},
    )


async def external_service_exception_handler(
    request: Request,
    exc: ExternalServiceError,
) -> JSONResponse:
    logger.error(
        "external_service_error",
        detail=str(exc),
        **_request_context(request),
    )
    return JSONResponse(
        status_code=502,
        content={"code": "external_service_error", "message": str(exc)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(InvalidIPError, invalid_ip_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(GeoNotFoundError, geo_not_found_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StartupCheckError, startup_check_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(GeoLookupError, geo_lookup_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ExternalServiceError, external_service_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
