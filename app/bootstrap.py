from redis.asyncio import Redis
from structlog import get_logger

from app.config import Settings
from app.domain.exceptions import StartupCheckError

logger = get_logger(__name__)


async def run_startup_checks(settings: Settings) -> None:
    redis = Redis.from_url(settings.redis_url, decode_responses=True)

    try:
        pong = await redis.ping()
        if pong is not True:
            raise StartupCheckError("Redis ping failed")
    finally:
        await redis.aclose()  # type: ignore[attr-defined]
