from ipaddress import ip_address

from app.domain.exceptions import InvalidIPError


def normalize_ip(value: str) -> str:
    try:
        return str(ip_address(value))
    except ValueError as exc:
        raise InvalidIPError("Invalid IP address") from exc
