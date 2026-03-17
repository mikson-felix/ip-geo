import pytest
from fastapi import Request

from app.common.client_ip import extract_client_ip
from app.domain.exceptions import InvalidIPError
from tests.conftest import LOOKUP_PATH


def make_request(
    *,
    headers: dict[str, str] | None = None,
    client_host: str | None = None,
) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": LOOKUP_PATH,
        "headers": [
            (key.lower().encode("latin-1"), value.encode("latin-1"))
            for key, value in (headers or {}).items()
        ],
        "client": (client_host, 12345) if client_host is not None else None,
    }
    return Request(scope)


def test_extract_client_ip_from_x_forwarded_for_single_public_ip() -> None:
    request = make_request(headers={"X-Forwarded-For": "8.8.8.8"})

    result = extract_client_ip(request)

    assert result == "8.8.8.8"


def test_extract_client_ip_from_x_forwarded_for_first_public_ip() -> None:
    request = make_request(headers={"X-Forwarded-For": "172.18.0.1, 10.0.0.5, 8.8.8.8, 1.1.1.1"})

    result = extract_client_ip(request)

    assert result == "8.8.8.8"


def test_extract_client_ip_from_x_real_ip() -> None:
    request = make_request(headers={"X-Real-IP": "1.1.1.1"})

    result = extract_client_ip(request)

    assert result == "1.1.1.1"


def test_extract_client_ip_from_request_client_host_when_public() -> None:
    request = make_request(client_host="8.8.4.4")

    result = extract_client_ip(request)

    assert result == "8.8.4.4"


def test_extract_client_ip_prefers_x_forwarded_for_over_x_real_ip() -> None:
    request = make_request(
        headers={
            "X-Forwarded-For": "8.8.8.8",
            "X-Real-IP": "1.1.1.1",
        },
        client_host="9.9.9.9",
    )

    result = extract_client_ip(request)

    assert result == "8.8.8.8"


def test_extract_client_ip_raises_when_only_private_addresses_available() -> None:
    request = make_request(
        headers={"X-Forwarded-For": "172.18.0.1, 10.0.0.5"},
        client_host="192.168.1.20",
    )

    with pytest.raises(
        InvalidIPError,
        match="Could not determine a public client IP address",
    ):
        extract_client_ip(request)


def test_extract_client_ip_raises_when_no_addresses_available() -> None:
    request = make_request()

    with pytest.raises(
        InvalidIPError,
        match="Could not determine a public client IP address",
    ):
        extract_client_ip(request)


def test_extract_client_ip_normalizes_ipv6() -> None:
    request = make_request(
        headers={"X-Forwarded-For": "2001:4860:4860::8888"},
    )

    result = extract_client_ip(request)

    assert result == "2001:4860:4860::8888"
