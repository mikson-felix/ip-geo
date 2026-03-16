class GeoLookupError(Exception):
    """Base geolocation exception."""


class InvalidIPError(GeoLookupError):
    """Raised when the provided IP address is invalid."""


class GeoNotFoundError(GeoLookupError):
    """Raised when geolocation was not found."""


class ExternalServiceError(GeoLookupError):
    """Raised when external service failed."""


class CircuitBreakerOpenError(ExternalServiceError):
    """Raised when provider circuit breaker is open."""


class StartupCheckError(RuntimeError):
    """Raised when application startup checks fail."""
