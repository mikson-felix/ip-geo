import geoip2.database
import geoip2.errors
import structlog

from app.domain.entities import GeoInfo

logger = structlog.get_logger(__name__)


class MaxMindGeoRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._reader: geoip2.database.Reader | None = None

        try:
            self._reader = geoip2.database.Reader(db_path)
        except FileNotFoundError:
            logger.warning(
                "maxmind_db_missing",
                path=db_path,
            )
        except Exception as exc:
            logger.warning(
                "maxmind_db_unavailable",
                path=db_path,
                error=str(exc),
            )

    @classmethod
    def from_path(cls, db_path: str) -> "MaxMindGeoRepository":
        return cls(db_path)

    def lookup(self, ip: str) -> GeoInfo | None:
        if self._reader is None:
            return None

        try:
            record = self._reader.city(ip)
        except (geoip2.errors.AddressNotFoundError, ValueError):
            return None

        region = None
        if record.subdivisions and record.subdivisions.most_specific:
            region = record.subdivisions.most_specific.name

        return GeoInfo(
            ip=ip,
            country=record.country.name,
            country_code=record.country.iso_code,
            city=record.city.name,
            region=region,
            latitude=record.location.latitude,
            longitude=record.location.longitude,
            source="maxmind",
        )

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()
