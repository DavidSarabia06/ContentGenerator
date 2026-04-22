from cryptography.fernet import Fernet
import os

from passlib.context import CryptContext

# 🔑 Clave secreta para cifrar y descifrar (debe mantenerse segura)
SECRET_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
fernet = Fernet(SECRET_KEY.encode())

# 🔐 Cifra una contraseña usando Fernet
def encrypt_password(password: str) -> str:
    """
    Recibe una cadena de texto y devuelve su versión encriptada.
    """
    f = Fernet(SECRET_KEY)  # Crear objeto Fernet con la clave secreta
    encrypted_password = f.encrypt(password.encode())  # Cifra la contraseña (codificada como bytes)
    return encrypted_password.decode()  # Devuelve como string

# 🔓 Descifra una contraseña previamente cifrada
def decrypt_password(encrypted_password: str) -> str:
    """
    Recibe un texto encriptado (string) y devuelve el valor original desencriptado.
    """
    f = Fernet(SECRET_KEY)  # Crear objeto Fernet con la misma clave
    decrypted_password = f.decrypt(encrypted_password.encode())  # Descifra el valor
    return decrypted_password.decode()  # Devuelve como string

# ⚙️ Configuración del contexto de encriptación de contraseñas usando bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)


