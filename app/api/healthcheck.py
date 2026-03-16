from fastapi import APIRouter

from app.api.openapi import HEALTH_RESPONSES
from app.api.schemas import HealthResponseSchema

router = APIRouter()


@router.get(
    "/health/",
    response_model=HealthResponseSchema,
    tags=["healthcheck"],
    summary="Health check",
    description="Returns service health status.",
    responses=HEALTH_RESPONSES,  # type: ignore[arg-type]
)
async def health() -> HealthResponseSchema:
    return HealthResponseSchema()
