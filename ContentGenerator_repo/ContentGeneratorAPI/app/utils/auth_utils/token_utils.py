# app/utils/security/jwt_tokens.py
from datetime import datetime
from typing import Tuple
from fastapi import HTTPException,status
from jose import jwt
import uuid
from app.utils.datetime_utils import DatetimeUtils

from app.config import settings



def create_access_token(user_id: str) -> Tuple[str, datetime]:
    """
    Crea un JWT de acceso de corta duración.
    - sub: identifica al usuario
    - type: 'access' para distinguir tipos
    - iat/exp: tiempos en segundos UNIX
    - jti: identificador único del token
    """
    iat = DatetimeUtils.now()
    exp = iat + settings.access_delta()  # p.ej. 15 min
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    return token, exp

def create_refresh_token(user_id: str) -> Tuple[str, datetime, str]:
    """
    Crea un JWT de refresh (larga duración)
    Devuelve (token, exp, jti) para poder revocarlo/validarlo después.
    """
    iat = DatetimeUtils.now()
    exp = iat + settings.refresh_delta()  # p.ej. 7-30 días
    jti = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

    return token, exp, jti

def create_verification_token(username: str) -> str:
    """Token para enlace de verificación de email (24h por defecto)"""
    iat = DatetimeUtils.now()
    exp = iat + settings.verification_delta()
    payload = {
        "sub": username,
        "type": "verify",
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_token(token: str) -> dict:
    """
    Decodifica y verifica un JWT (firma y expiración).
    Lanza HTTP 401 en caso de token expirado o inválido.
    """
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
