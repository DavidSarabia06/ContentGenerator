# app/services/verification_service.py (opcional)
from fastapi import HTTPException
from jose import jwt, JWTError
from app.config import settings
from app.utils.auth_utils.token_utils import create_verification_token

def build_verification_link(base_url: str, username: str) -> str:
    token = create_verification_token(username)
    return f"{base_url}/auth/verify?token={token}"

def verify_verification_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        if payload.get("type") != "verify":
            raise HTTPException(status_code=400, detail="Token no es de verificación")
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


#Reubicar
import random, string
def generate_reset_code(length=6):
    return ''.join(random.choices(string.digits, k=length))