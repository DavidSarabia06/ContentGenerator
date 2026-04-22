from fastapi import APIRouter, HTTPException, Depends, Request, Response, responses
from datetime import datetime, timedelta, timezone
import os

from app.models.user_models import (
    UserRegister, UserLogin, ChangePasswordRequest, SimplePasswordChangeRequest,
    EmailRequest, CodeVerificationRequest, DeleteAccountRequest
)
from app.services.database_mongoDB import MongoConnector
from app.services.auth_service import (
    issue_session, rotate_refresh, logout,
    get_current_user, get_current_admin_user
)
from app.utils.auth_utils.cookie_utils import require_csrf, clear_cookie, ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE
from app.utils.auth_utils.token_utils import (
    create_verification_token, decode_token
)
from app.services.register_service import generate_reset_code
from app.utils.datetime_utils import DatetimeUtils
from app.utils.encrypt_utils import hash_password, pwd_context
from app.utils.email_utils import send_email

router = APIRouter(prefix="/auth", tags=["Auth"])

# Lockout (intentos fallidos)
MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
BLOCK_TIME_MINUTES = int(os.getenv("LOGIN_BLOCK_TIME_MINUTES", "15"))

# Rate limit (ventanas fijas)
RATE_IP_MAX = int(os.getenv("RATE_IP_MAX", "10"))
RATE_IP_WINDOW = int(os.getenv("RATE_IP_WINDOW", "60"))
RATE_USER_MAX = int(os.getenv("RATE_USER_MAX", "10"))
RATE_USER_WINDOW = int(os.getenv("RATE_USER_WINDOW", "60"))

def get_mongo_connector():
    return MongoConnector()

# -------- helpers rate-limit --------
def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def _enforce_rate_limit_pair(
    *,
    db: MongoConnector,
    request: Request,
    prefix: str,
    subject: str | None = None,
    ip_window: int = RATE_IP_WINDOW,
    ip_max: int = RATE_IP_MAX,
    subj_window: int = RATE_USER_WINDOW,
    subj_max: int = RATE_USER_MAX,
    ip_msg: str = "Demasiadas solicitudes desde esta IP. Intenta más tarde.",
    subj_msg: str = "Demasiadas solicitudes. Intenta más tarde."
) -> None:
    """Límite por IP + (opcional) por sujeto (usuario/email) con claves por endpoint."""
    ip = _get_client_ip(request)
    ok, retry = db.rate_limit_hit(
        key=f"rl:{prefix}:ip:{ip}",
        window_seconds=ip_window,
        max_allowed=ip_max
    )
    if not ok:
        raise HTTPException(status_code=429, detail=ip_msg, headers={"Retry-After": str(retry)})

    if subject:
        subj = subject.strip().lower()
        ok, retry = db.rate_limit_hit(
            key=f"rl:{prefix}:subj:{subj}",
            window_seconds=subj_window,
            max_allowed=subj_max
        )
        if not ok:
            raise HTTPException(status_code=429, detail=subj_msg, headers={"Retry-After": str(retry)})

# ---------- Me / Admin ----------
@router.get("/me")
def me(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}

@router.get("/check_admin")
def check_admin(admin_user: str = Depends(get_current_admin_user)):
    return True

# ---------- Registro / Verificación ----------
@router.post("/register")
def register(user: UserRegister, request: Request, db: MongoConnector = Depends(get_mongo_connector)):
    # rate-limit: por IP y por email
    _enforce_rate_limit_pair(
        db=db, request=request, prefix="register",
        subject=user.email,
        subj_msg="Demasiadas solicitudes de registro para este email. Intenta más tarde."
    )
    # opcional: también por username (segunda cuota independiente)
    _enforce_rate_limit_pair(
        db=db, request=request, prefix="register-user",
        subject=user.username,
        subj_msg="Demasiadas solicitudes de registro para este usuario. Intenta más tarde."
    )

    if db.get_user(user.username):
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    if db.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email ya está en uso")

    db.create_user(
        username=user.username,
        password=user.password,
        is_admin=False,
        is_verified=False,
        email=user.email,
        allow_notifications=user.allow_notifications
    )

    token = create_verification_token(user.username)
    verification_url = f"http://localhost:8000/auth/verify_email?token={token}"

    send_email(
        to_email=user.email,
        subject="🎉 Bienvenido a ContentGenerator – Verifica tu correo",
        body=(
            f"Hola {user.username}.\n\n"
            f"Gracias por registrarte. \nPara verificar tu correo, haz clic en el siguiente enlace:\n\n"
            f"{verification_url}\n\n"
            "Si no te registraste, puedes ignorar este correo."
        )
    )
    return {"message": "✅ Usuario registrado. Verifica tu email para activar la cuenta."}

@router.post("/register_admin")
def register_admin(user: UserRegister, request: Request, db: MongoConnector = Depends(get_mongo_connector)):
    # rate-limit suave también aquí
    _enforce_rate_limit_pair(
        db=db, request=request, prefix="register-admin",
        subject=user.email
    )

    if db.get_user(user.username):
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    if db.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email ya está en uso")

    db.create_user(
        username=user.username,
        password=user.password,
        is_admin=True,
        is_verified=True,
        email=user.email,
        allow_notifications=user.allow_notifications
    )
    return {"message": f"✅ Usuario '{user.username}' registrado como administrador."}

@router.get("/verify_email")
def verify_email(token: str, db: MongoConnector = Depends(get_mongo_connector)):
    try:
        payload = decode_token(token)
    except HTTPException:
        return responses.RedirectResponse(url="http://localhost:5500/email_verification.html?status=invalid")

    if payload.get("type") != "verify":
        return responses.RedirectResponse(url="http://localhost:5500/email_verification.html?status=invalid")

    username = payload.get("sub")
    if not username:
        return responses.RedirectResponse(url="http://localhost:5500/email_verification.html?status=invalid")

    user = db.get_user(username)
    if not user:
        return responses.RedirectResponse(url="http://localhost:5500/email_verification.html?status=notfound")

    if user.get("is_verified"):
        return responses.RedirectResponse(url="http://localhost:5500/email_verification.html?status=already_verified")

    db.verify_user_email(username)
    return responses.RedirectResponse(url="http://localhost:5500/email_verification.html?status=success")

# ---------- Login / Refresh / Logout ----------
@router.post("/login")
def login(user: UserLogin, request: Request, response: Response, db: MongoConnector = Depends(get_mongo_connector)):
    now = DatetimeUtils.now()
    print(f"\n🛠️ LOGIN intento de: {user.username} @ {now.isoformat()}")

    # rate-limit por IP + por usuario
    _enforce_rate_limit_pair(
        db=db, request=request, prefix="login",
        subject=user.username,
        subj_msg="Demasiados intentos para este usuario. Intenta más tarde."
    )

    # Bloqueo por intentos fallidos (lockout)
    attempt = db.get_login_attempt(user.username)
    print(f"🔎 Registro previo de intentos: {attempt}")

    if attempt:
        blocked_until = attempt.get("blocked_until")
        if blocked_until and blocked_until.tzinfo is None:
            blocked_until = blocked_until.replace(tzinfo=timezone.utc)

        if blocked_until and blocked_until > now:
            remaining_seconds = int((blocked_until - now).total_seconds())
            unlock_time_str = DatetimeUtils.format_local_time(blocked_until, "%H:%M:%S")
            if remaining_seconds >= 60:
                minutes_left = remaining_seconds // 60
                detail_msg = f"Cuenta bloqueada hasta las {unlock_time_str}. Intenta en {minutes_left} minuto(s)."
            else:
                detail_msg = f"Cuenta bloqueada hasta las {unlock_time_str}. Intenta en {remaining_seconds} segundo(s)."
            raise HTTPException(status_code=403, detail=detail_msg)

        if blocked_until and blocked_until <= now:
            print("🔓 Bloqueo expirado. Reiniciando intentos fallidos.")
            db.delete_login_attempt(user.username)
            attempt = None

    # Credenciales
    db_user = db.get_user(user.username)
    print(f"👤 Usuario encontrado: {bool(db_user)}")

    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        if not attempt:
            print("🆕 Primer intento fallido. Registrando...")
            db.create_login_attempt(user.username)
        else:
            fail_count = attempt["fail_count"] + 1
            blocked_until = None
            if fail_count >= MAX_ATTEMPTS:
                blocked_until = now + timedelta(minutes=BLOCK_TIME_MINUTES)
                print(f"⛔ Límite alcanzado. Bloqueando hasta {blocked_until.isoformat()}")
            print(f"🔁 Actualizando intentos fallidos: {fail_count}")
            db.update_login_attempt(user.username, fail_count, blocked_until)

        raise HTTPException(status_code=401, detail="⚠️ Credenciales inválidas.")

    # Verificación de email
    if not db_user.get("is_verified", False):
        print("📨 La cuenta no esta verificada ...")
        raise HTTPException(status_code=403, detail="❌ Cuenta no verificada, revisa tu email.")

    # Login OK
    if attempt:
        print("✅ Login exitoso. Eliminando intentos fallidos...")
        db.delete_login_attempt(user.username)

    session_info = issue_session(response, user_id=user.username)
    print("🔐 Token generado. Login OK.\n")
    return {"message": "✅ Login correcto.", **session_info}

@router.post("/refresh")
def refresh(request: Request, response: Response):
    return rotate_refresh(request, response)

@router.post("/logout")
def do_logout(request: Request, response: Response):
    return logout(request, response)

# ---------- Password ----------
@router.post("/change_password")
def change_password(
    data: ChangePasswordRequest,
    username: str = Depends(get_current_user),
    db: MongoConnector = Depends(get_mongo_connector)
):
    user = db.get_user(username)
    if not user or not pwd_context.verify(data.current_password, user["password"]):
        raise HTTPException(status_code=401, detail="⚠️ Contraseña actual incorrecta.")
    new_hashed = hash_password(data.new_password)
    db.update_user_password(username, new_hashed)
    return {"message": "✅ Contraseña actualizada correctamente."}

@router.post("/force_change_password")
def force_change_password(data: SimplePasswordChangeRequest, db: MongoConnector = Depends(get_mongo_connector)):
    user = db.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="⚠️ Usuario no encontrado.")
    hashed_password = hash_password(data.new_password)
    db.update_user_password(user["username"], hashed_password)
    return {"message": "✅ Contraseña actualizada correctamente."}

@router.post("/request_reset_password_code")
def request_reset_password_code(
    data: EmailRequest,
    request: Request,
    db: MongoConnector = Depends(get_mongo_connector)
):
    # rate-limit por IP y por email de destino
    _enforce_rate_limit_pair(
        db=db, request=request, prefix="reset-code", subject=data.email,
        subj_msg="Demasiadas solicitudes para este email. Intenta más tarde."
    )

    user = db.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="⚠️ Correo no registrado.")

    code = generate_reset_code()
    expiry = DatetimeUtils.now() + timedelta(minutes=10)

    db.set_reset_code(data.email, code, expiry)
    send_email(str(data.email), "Tu código de recuperación", f"Tu código de recuperación de contraseña es: {code}")
    return {"message": "✅ Código enviado por email."}

@router.post("/validate_reset_password_code")
def validate_reset_password_code(data: CodeVerificationRequest, db: MongoConnector = Depends(get_mongo_connector)):
    user = db.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="⚠️ Usuario no encontrado.")
    if user.get("reset_code") != data.code:
        raise HTTPException(status_code=400, detail="⚠️ Código incorrecto.")

    expiry = user.get("reset_code_expiry")
    if not expiry:
        raise HTTPException(status_code=400, detail="⚠️ El código ha expirado.")
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if DatetimeUtils.now() > expiry:
        raise HTTPException(status_code=400, detail="⚠️ El código ha expirado.")
    return {"message": "✅ Código válido."}

# ---------- Borrado de cuenta ----------
@router.post("/delete_account")
def delete_account(
    request: Request,
    response: Response,
    data: DeleteAccountRequest,
    username: str = Depends(get_current_user),
    db: MongoConnector = Depends(get_mongo_connector)
):
    require_csrf(request)

    user = db.get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="⚠️ Usuario no encontrado.")

    if not data.confirm_text or data.confirm_text.strip().upper() != "ELIMINAR":
        raise HTTPException(status_code=400, detail="⚠️ Debes escribir 'ELIMINAR' para confirmar.")

    db.delete_user(username)

    try:
        logout(request, response)
    except Exception:
        clear_cookie(response, ACCESS_COOKIE)
        clear_cookie(response, REFRESH_COOKIE)
        clear_cookie(response, CSRF_COOKIE)

    return {"message": "✅ Cuenta eliminada correctamente."}
