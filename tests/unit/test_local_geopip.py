from pathlib import Path

from app.infrastructure.local_geoip import MaxMindGeoRepository


def test_local_geoip_repository_returns_none_when_db_file_is_missing(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing.mmdb"

    repo = MaxMindGeoRepository.from_path(str(db_path))

    result = repo.lookup("8.8.8.8")

    assert result is None


def test_local_geoip_repository_close_does_not_fail_when_reader_is_missing(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing.mmdb"

    repo = MaxMindGeoRepository.from_path(str(db_path))

    repo.close()
