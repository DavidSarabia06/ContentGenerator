# app/utils/auth_utils/cookie_utils.py
from fastapi import Response, Request, HTTPException
from app.config import settings
from app.utils.datetime_utils import DatetimeUtils
from datetime import datetime

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_refresh_token"

def _should_set_domain() -> bool:
    """
    Solo establece 'domain' si es un FQDN válido (producción).
    No se establece para 'localhost' ni para IPs (127.0.0.1).
    """
    d = (settings.COOKIE_DOMAIN or "").strip().lower()
    if not d:
        return False
    if d == "localhost":
        return False
    # Evitar IPs
    parts = d.split(".")
    if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        return False
    return True

def set_cookie(response: Response, key: str, value: str, expires_at: datetime, http_only: bool = True):
    max_age = int(expires_at.timestamp() - DatetimeUtils.now().timestamp())
    kwargs = dict(
        key=key,
        value=value,
        httponly=http_only,
        secure=settings.COOKIE_SECURE,      # en local: False
        samesite=settings.COOKIE_SAMESITE,  # en local: "Lax"
        max_age=max_age,
        expires=expires_at,
        path="/",
    )
    if _should_set_domain():
        kwargs["domain"] = settings.COOKIE_DOMAIN

    response.set_cookie(**kwargs)

def clear_cookie(response: Response, key: str):
    # Borra sin domain si no se está usando domain
    if _should_set_domain():
        response.delete_cookie(key, domain=settings.COOKIE_DOMAIN, path="/")
    else:
        response.delete_cookie(key, path="/")

def require_csrf(request: Request) -> None:
    header = request.headers.get("X-CSRF-Token")
    cookie = request.cookies.get(CSRF_COOKIE)
    if not header or not cookie or header != cookie:
        raise HTTPException(status_code=403, detail="CSRF inválido")
