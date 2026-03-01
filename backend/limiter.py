from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_real_ip(request) -> str:
    """優先使用 Cloudflare CF-Connecting-IP，其次 X-Forwarded-For，最後 remote address。"""
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_get_real_ip)
