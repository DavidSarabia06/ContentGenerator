from pydantic import BaseModel,EmailStr

# Modelo de datos para el registro de usuarios.
# Valida que se envíen un nombre de usuario y una contraseña.
class UserRegister(BaseModel):
    username: str
    password: str
    email: EmailStr
    allow_notifications: bool = True

class UserLogin(BaseModel):
    username: str
    password: str
    is_admin: bool = False

class AdminCreateUserRequest(BaseModel):
    username: str
    password: str
    email: EmailStr
    isAdmin: bool = False
    allow_notifications: bool = True


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class EmailRequest(BaseModel):
    email: EmailStr

class CodeVerificationRequest(BaseModel):
    email: EmailStr
    code: str

class SimplePasswordChangeRequest(BaseModel):
    email: EmailStr
    new_password: str

class DeleteAccountRequest(BaseModel):
    confirm_text: str                # Debe ser "ELIMINAR"
    current_password: str | None = None  # Opcional: si lo envías, se verifica