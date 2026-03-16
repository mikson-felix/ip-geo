from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponseSchema(BaseModel):
    status: str = Field(default="ok", description="Service health status", examples=["ok"])

    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok"}})


class GeoLookupResponse(BaseModel):
    ip: str = Field(description="Normalized IPv4 or IPv6 address", examples=["8.8.8.8"])
    country: str | None = Field(
        default=None, description="Country name", examples=["United States"]
    )
    country_code: str | None = Field(
        default=None, description="ISO 3166-1 alpha-2 country code", examples=["US"]
    )
    city: str | None = Field(default=None, description="City name", examples=["Mountain View"])
    region: str | None = Field(
        default=None, description="Region or state name", examples=["California"]
    )
    latitude: float | None = Field(
        default=None,
        description="Latitude as a numeric value",
        examples=[37.386],
    )
    longitude: float | None = Field(
        default=None,
        description="Longitude as a numeric value",
        examples=[-122.0838],
    )
    latitude_formatted: str | None = Field(
        description="Latitude formatted with 6 decimal digits",
        default=None,
        examples=["37.386000"],
    )
    longitude_formatted: str | None = Field(
        description="Longitude formatted with 6 decimal digits",
        default=None,
        examples=["-122.083800"],
    )
    source: str = Field(
        description="Original source of geolocation data",
        examples=["maxmind"],
    )
    served_from_cache: bool = Field(
        default=False,
        description="Whether this response was served from Redis cache",
        examples=[False],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ip": "8.8.8.8",
                    "country": "United States",
                    "country_code": "US",
                    "city": "Mountain View",
                    "region": "California",
                    "latitude": 37.386,
                    "longitude": -122.0838,
                    "latitude_formatted": "37.386000",
                    "longitude_formatted": "-122.083800",
                    "source": "maxmind",
                    "served_from_cache": False,
                },
                {
                    "ip": "1.1.1.1",
                    "country": "Australia",
                    "country_code": "AU",
                    "city": "Sydney",
                    "region": "New South Wales",
                    "latitude": -33.8591,
                    "longitude": 151.2002,
                    "latitude_formatted": "-33.859100",
                    "longitude_formatted": "151.200200",
                    "source": "ipapi",
                    "served_from_cache": True,
                },
            ]
        }
    }

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def round_coordinates(cls, value: Any) -> float | None:
        if value is None:
            return None
        return round(float(value), 6)

    @classmethod
    def from_entity(cls, geo) -> GeoLookupResponse:  # type: ignore[no-untyped-def]
        lat = geo.latitude
        lon = geo.longitude

        return cls(
            ip=geo.ip,
            country=geo.country,
            country_code=geo.country_code,
            city=geo.city,
            region=geo.region,
            latitude=lat,
            longitude=lon,
            latitude_formatted=f"{lat:.6f}" if lat is not None else None,
            longitude_formatted=f"{lon:.6f}" if lon is not None else None,
            source=geo.source,
            served_from_cache=geo.served_from_cache,
        )


class ErrorResponse(BaseModel):
    code: str = Field(
        description="Machine-readable error code",
        examples=["invalid_ip"],
    )
    message: str = Field(
        description="Human-readable error message",
        examples=["Invalid IP address"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "invalid_ip",
                    "message": "Invalid IP address",
                },
                {
                    "code": "geo_not_found",
                    "message": "Geolocation not found for ip=203.0.113.10",
                },
            ]
        }
    }
