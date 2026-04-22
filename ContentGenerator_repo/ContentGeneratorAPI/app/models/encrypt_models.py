from pydantic import BaseModel

class PasswordData(BaseModel):
    password: str