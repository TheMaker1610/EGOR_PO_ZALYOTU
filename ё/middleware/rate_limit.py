from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request, Response

limiter = Limiter(key_func=get_remote_address)


def add_rate_limit_headers(request: Request, response: Response):
    """Middleware helper — slowapi handles headers automatically via its exception handler."""
    pass
