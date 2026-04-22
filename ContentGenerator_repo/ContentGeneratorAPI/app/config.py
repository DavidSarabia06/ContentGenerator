# app/core/config.py
import os
from datetime import timedelta

class Settings:
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecret")
    JWT_ALG: str = os.getenv("JWT_ALGORITHM", "HS256")

    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "Lax")  # o "None" si cross-site
    COOKIE_DOMAIN: str | None = os.getenv("COOKIE_DOMAIN")  # p.ej. ".midominio.com"

    def access_delta(self) -> timedelta:
        return timedelta(minutes=int(os.getenv("ACCESS_MINUTES", "15")))

    def refresh_delta(self) -> timedelta:
        return timedelta(days=int(os.getenv("REFRESH_DAYS", "7")))

    def verification_delta(self) -> timedelta:
        return timedelta(hours=int(os.getenv("VERIFY_HOURS", "24")))

settings = Settings()