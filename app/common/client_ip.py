from ipaddress import ip_address

from fastapi import Request

from app.common.ip import normalize_ip
from app.domain.exceptions import InvalidIPError


def _is_public_ip(value: str) -> bool:
    ip = ip_address(value)
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def extract_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        candidates = [item.strip() for item in forwarded_for.split(",") if item.strip()]
        for candidate in candidates:
            normalized = normalize_ip(candidate)
            if _is_public_ip(normalized):
                return normalized

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        normalized = normalize_ip(real_ip)
        if _is_public_ip(normalized):
            return normalized

    if request.client and request.client.host:
        normalized = normalize_ip(request.client.host)
        if _is_public_ip(normalized):
            return normalized

    raise InvalidIPError(
        "Could not determine a public client IP address. Pass the 'ip' query parameter explicitly."
    )
