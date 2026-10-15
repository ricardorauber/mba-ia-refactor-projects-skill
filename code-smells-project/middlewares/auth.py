import hmac
from functools import wraps

from flask import current_app, request

from middlewares.errors import ForbiddenError, UnauthorizedError


def require_admin_token(view):
    """401 without X-Admin-Token, 403 when it is wrong or ADMIN_TOKEN is not configured."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN", "")
        received = request.headers.get("X-Admin-Token", "")
        if not received:
            raise UnauthorizedError("Token de administrador ausente")
        if not expected or not hmac.compare_digest(received.encode(), expected.encode()):
            raise ForbiddenError("Token de administrador inválido")
        return view(*args, **kwargs)

    return wrapper
