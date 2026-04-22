# app/services/auth_service.py
import uuid
from fastapi import Request, Response, HTTPException
from app.utils.auth_utils.token_utils import create_access_token, create_refresh_token, decode_token
from app.utils.auth_utils.cookie_utils import ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE, set_cookie, clear_cookie, require_csrf
from app.services.database_mongoDB import MongoConnector



# ============================================================
# ======================= Dependencias =======================
# ============================================================

db = MongoConnector()


def get_current_admin_user(request: Request) -> str:
    user_id = get_current_user(request)
    user = db.get_user(user_id)
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores.")
    return user_id

def get_current_user(request: Request) -> str:
    """
    Obtiene el user_id (sub) desde el access token guardado en cookie.
    Verifica que el token exista, sea válido y sea de tipo 'access'.
    """
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Falta access token")
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")
    return payload["sub"]


# ============================================================
# ======================== Flujo auth ========================
# ============================================================

def issue_session(response: Response, user_id: str) -> dict:
    """
    Emite una sesión completa:
    - Genera y setea cookie de access (HttpOnly)
    - Genera y setea cookie de refresh (HttpOnly) + whitelist
    - Genera y setea cookie de CSRF (accesible por JS) para rotación/logout
    Devuelve info útil para el cliente (fechas de expiración).
    """
    # Access
    access, access_exp = create_access_token(user_id)
    set_cookie(response, ACCESS_COOKIE, access, access_exp, http_only=True)

    # Refresh + CSRF
    refresh, refresh_exp, jti = create_refresh_token(user_id)
    db.allow_refresh_token(jti=jti, user_id=user_id, exp=refresh_exp)
    set_cookie(response, REFRESH_COOKIE, refresh, refresh_exp, http_only=True)

    # CSRF token legible por JS (no HttpOnly) para doble envío
    csrf = str(uuid.uuid4())
    set_cookie(response, CSRF_COOKIE, csrf, refresh_exp, http_only=False)

    return {
        "user_id": user_id,
        "access_expires_at": access_exp.isoformat(),
        "refresh_expires_at": refresh_exp.isoformat(),
    }

def rotate_refresh(request: Request, response: Response) -> dict:
    """
    Rota el refresh token usando el patrón 'rotating refresh tokens':
    - Requiere CSRF (doble envío)
    - Verifica refresh actual, tipo y whitelist (no revocado)
    - Emite nuevo access y nuevo refresh (con nuevo jti)
    - Rota CSRF (genera uno nuevo)
    - Revoca el refresh anterior en la whitelist
    """
    require_csrf(request)

    # Leer refresh de cookie
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Falta refresh token")

    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")

    user_id = payload["sub"]
    jti_old = payload["jti"]

    # Validar en whitelist (no revocado y reconocido)
    if not db.is_refresh_valid(jti_old, user_id):
        raise HTTPException(status_code=401, detail="Refresh revocado o no reconocido")

    # Emitir nuevos tokens
    access, access_exp = create_access_token(user_id)
    set_cookie(response, ACCESS_COOKIE, access, access_exp, http_only=True)

    refresh, refresh_exp, jti_new = create_refresh_token(user_id)
    db.allow_refresh_token(jti=jti_new, user_id=user_id, exp=refresh_exp)
    set_cookie(response, REFRESH_COOKIE, refresh, refresh_exp, http_only=True)

    # Rotar CSRF (limpia el anterior si existe y crea uno nuevo)
    csrf = request.cookies.get(CSRF_COOKIE) or ""
    if csrf:
        clear_cookie(response, CSRF_COOKIE)
    set_cookie(response, CSRF_COOKIE, str(uuid.uuid4()), refresh_exp, http_only=False)

    # Revocar el refresh antiguo para evitar reutilización
    db.revoke_refresh_token(jti_old)

    return {
        "user_id": user_id,
        "access_expires_at": access_exp.isoformat(),
        "refresh_expires_at": refresh_exp.isoformat(),
    }

def logout(request: Request, response: Response) -> dict:
    """
    Cierra sesión de forma segura:
    - Requiere CSRF (doble envío) para evitar CSRF logout
    - Intenta revocar el refresh actual (si existe y es válido)
    - Limpia las cookies de access, refresh y CSRF
    """
    # CSRF requerido (doble envío)
    require_csrf(request)

    # Intentar revocar refresh si existe
    token = request.cookies.get(REFRESH_COOKIE)
    if token:
        try:
            payload = decode_token(token)
            if payload.get("type") == "refresh":
                db.revoke_refresh_token(payload.get("jti", ""))
        except Exception:
            # Si algo falla al decodificar, continuamos con limpieza de cookies
            pass

    # Limpiar todas las cookies relacionadas con la sesión
    clear_cookie(response, ACCESS_COOKIE)
    clear_cookie(response, REFRESH_COOKIE)
    clear_cookie(response, CSRF_COOKIE)

    return {"detail": "logout ok"}

