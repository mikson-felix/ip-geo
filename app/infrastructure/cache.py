import json

from redis.asyncio import Redis

from app.domain.entities import GeoInfo


class RedisGeoCache:
    def __init__(self, redis: Redis, ttl_seconds: int) -> None:  # type: ignore[type-arg]
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def _key(ip: str) -> str:
        return f"geo:{ip}"

    async def get(self, ip: str) -> GeoInfo | None:
        raw = await self._redis.get(self._key(ip))
        if raw is None:
            return None
        return GeoInfo(**json.loads(raw))

    async def set(self, payload: GeoInfo) -> None:
        await self._redis.set(
            self._key(payload.ip),
            payload.model_dump_json(),
            ex=self._ttl_seconds,
        )
