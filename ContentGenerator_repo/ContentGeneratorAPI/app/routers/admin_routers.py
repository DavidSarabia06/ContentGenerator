from fastapi import APIRouter, Depends, HTTPException, Request
from pymongo import DESCENDING
from datetime import datetime, timezone

from app.services.database_mongoDB import MongoConnector
from app.services.auth_service import get_current_admin_user
from app.utils.auth_utils.cookie_utils import require_csrf
from app.utils.auth_utils.token_utils import create_verification_token
from app.utils.datetime_utils import DatetimeUtils
from app.models.user_models import AdminCreateUserRequest
from app.utils.email_utils import send_email

router = APIRouter(prefix="/admin", tags=["Admin"])

# Dependencia para obtener acceso a la base de datos (evita dependencias entre routers)
def get_mongo_connector() -> MongoConnector:
    return MongoConnector()

@router.post("/register_user_by_admin")
def register_user_by_admin(
    request: Request,
    user: AdminCreateUserRequest,
    admin_user: str = Depends(get_current_admin_user),
    db: MongoConnector = Depends(get_mongo_connector),
):
    # Acción que escribe -> proteger con CSRF (doble envío)
    require_csrf(request)

    if db.get_user(user.username):
        raise HTTPException(status_code=400, detail="⚠️ El Usuario ya existe.")

    if db.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="⚠️ El Email ya está en uso.")

    # Crear usuario (is_verified False para forzar verificación por email)
    db.create_user(
        username=user.username,
        password=user.password,
        is_admin=user.isAdmin,
        is_verified=False,
        email=user.email,
        allow_notifications=user.allow_notifications,
    )

    # Enviar email de verificación
    token = create_verification_token(user.username)
    verification_url = f"http://localhost:8000/auth/verify_email?token={token}"

    send_email(
        to_email=user.email,
        subject="🎉 Bienvenido a ContentGenerator – Verifica tu correo",
        body=(
            f"Hola {user.username}.\n\n"
            f"Gracias por registrarte.\nPara verificar tu correo, haz clic en:\n\n"
            f"{verification_url}\n\n"
            "Si no te registraste, puedes ignorar este correo."
        ),
    )
    return {"message": "✅ Usuario registrado. Verifica tu email para activar la cuenta."}

@router.get("/list_users")
def get_users(
    admin_user: str = Depends(get_current_admin_user),
    db: MongoConnector = Depends(get_mongo_connector),
):
    """
    Devuelve todos los usuarios registrados (excepto contraseñas).
    """
    users = db.users_collection.find({}, {"_id": 0, "password": 0})
    return list(users)

@router.get("/list_users_summary")
def get_users_summary(
    admin_user: str = Depends(get_current_admin_user),
    db: MongoConnector = Depends(get_mongo_connector),
):
    """
    Resumen por usuario:
    - total_entradas
    - ultima_actividad (a hora local)
    """
    pipeline = [
        {
            "$group": {
                "_id": "$username",
                "total_entradas": {"$sum": 1},
                "ultima_actividad": {"$max": "$timestamp"},
            }
        },
        {"$sort": {"ultima_actividad": DESCENDING}},
    ]

    summary = list(db.openai_collection.aggregate(pipeline))

    for user in summary:
        fecha = user.get("ultima_actividad")
        if not fecha:
            continue
        # Normalizar a datetime
        if isinstance(fecha, str):
            try:
                fecha = datetime.fromisoformat(fecha)
            except ValueError:
                # Si el formato no es ISO, déjalo tal cual
                continue
        # Asegurar timezone-aware (UTC)
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        # Mostrar en hora local
        user["ultima_actividad"] = DatetimeUtils.format_local_time(fecha, "%Y-%m-%d %H:%M:%S")

    return summary

@router.delete("/users/{username}")
def delete_user_by_admin(
    request: Request,
    username: str,
    admin_user: str = Depends(get_current_admin_user),
    db: MongoConnector = Depends(get_mongo_connector),
):
    # Acción destructiva -> CSRF
    require_csrf(request)

    user = db.get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="⚠️ Usuario no encontrado.")

    db.delete_user(username)

    # Limpia registro de intentos de login si existe el método
    if hasattr(db, "delete_login_attempt"):
        try:
            db.delete_login_attempt(username)
        except Exception:
            pass

    return {"message": f"✅ Usuario '{username}' eliminado por administrador."}
