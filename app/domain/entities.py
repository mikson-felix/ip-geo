from pydantic import BaseModel, Field


class GeoInfo(BaseModel):
    ip: str
    country: str | None = None
    country_code: str | None = None
    city: str | None = None
    region: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    source: str = Field(description="maxmind|ipapi|ip-api")
    served_from_cache: bool = False
