from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from app.api.openapi import LOOKUP_ERROR_RESPONSES
from app.api.schemas import GeoLookupResponse
from app.application.use_cases import GeoLookupUseCase
from app.common.ip import normalize_ip
from app.domain.entities import GeoInfo

router = APIRouter(route_class=DishkaRoute)


@router.get(
    "/lookup/",
    response_model=GeoLookupResponse,
    tags=["ip"],
    summary="Lookup geolocation by IP",
    description=(
        "Returns geolocation information for the provided IP address. "
        "The service first checks Redis cache, then MaxMind GeoLite2, "
        "and finally external providers if needed."
    ),
    responses=LOOKUP_ERROR_RESPONSES,  # type: ignore[arg-type]
)
async def lookup(
    ip: str = Query(..., description="IPv4 or IPv6 address"),
    use_case: FromDishka[GeoLookupUseCase] = GeoLookupUseCase,  # type: ignore[assignment]
) -> GeoInfo:
    normalized_ip = normalize_ip(ip)
    ip_data = await use_case.execute(normalized_ip)
    return GeoLookupResponse.from_entity(ip_data)  # type: ignore[return-value]
