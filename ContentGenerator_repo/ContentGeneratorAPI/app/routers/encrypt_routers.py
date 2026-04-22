from fastapi import APIRouter, HTTPException
from app.models.encrypt_models import PasswordData         # Modelo que contiene el campo 'password'
from app.utils.encrypt_utils import encrypt_password, decrypt_password  # Funciones utilitarias de cifrado

# 📦 Crear un router con prefijo '/crypto' y grupo de etiquetas "Criptografía"
router = APIRouter(prefix="/crypto", tags=["Criptografía"])

# 🔐 Endpoint POST /crypto/encrypt
# Encripta una contraseña usando Fernet
@router.post("/encrypt")
def encrypt(data: PasswordData):
    try:
        # Llama a la función utilitaria para encriptar la contraseña
        encrypted = encrypt_password(data.password)
        # Devuelve la contraseña encriptada
        return {"encrypted": encrypted}
    except Exception as e:
        # Si algo falla, lanza un error HTTP 500 con el detalle del error
        raise HTTPException(status_code=500, detail=str(e))

# 🔓 Endpoint POST /crypto/decrypt
# Desencripta una contraseña encriptada previamente con Fernet
@router.post("/decrypt")
def decrypt(data: PasswordData):
    try:
        # Llama a la función utilitaria para desencriptar
        decrypted = decrypt_password(data.password)
        # Devuelve el valor original desencriptado
        return {"decrypted": decrypted}
    except Exception as e:
        # Si ocurre un error (por ejemplo, token mal formado), lanza error 400
        raise HTTPException(status_code=400, detail="No se pudo desencriptar.")
