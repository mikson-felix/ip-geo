import pytest

from app.common.ip import normalize_ip
from app.domain.exceptions import InvalidIPError


def test_normalize_ip_returns_same_for_valid_ipv4() -> None:
    assert normalize_ip("8.8.8.8") == "8.8.8.8"


def test_normalize_ip_normalizes_ipv6() -> None:
    assert normalize_ip("2001:0db8:0000:0000:0000:ff00:0042:8329") == "2001:db8::ff00:42:8329"


def test_normalize_ip_raises_for_invalid_ip() -> None:
    with pytest.raises(InvalidIPError):
        normalize_ip("not-an-ip")
