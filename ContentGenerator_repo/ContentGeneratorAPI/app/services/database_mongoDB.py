import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import DuplicateKeyError

from app.utils.encrypt_utils import hash_password

# 🌍 Cargar variables de entorno
load_dotenv()


class MongoConnector:
    """
    Conector a MongoDB: users, openai (historial), login_attempts, refresh_tokens y rate_limits.
    Incluye índices y helpers por colección.
    """

    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_URI"), tz_aware=True)
        self.db = self.client[os.getenv("MONGODB_DB")]

        # ================================
        # ======= COLECCIONES (DB) =======
        # ================================
        self.users_collection = self.db[os.getenv("MONGODB_USERS_COLLECTION")]
        self.openai_collection = self.db[os.getenv("MONGODB_OPENAI_COLLECTION")]
        self.login_attempts_collection = self.db[os.getenv("MONGODB_LOGIN_ATTEMPS_COLLECTION")]
        self.refresh_tokens_collection = self.db[os.getenv("MONGODB_REFRESH_TOKENS_COLLECTION", "refresh_tokens")]
        self.rate_limits_collection = self.db[os.getenv("MONGODB_RATE_LIMITS_COLLECTION", "rate_limits")]  # ⭐

        self._ensure_indexes()

    # ======================================
    # ============== ÍNDICES ===============
    # ======================================
    def _ensure_indexes(self):
        # ----- users_collection -----
        try:
            self.users_collection.create_index([("username", ASCENDING)], name="user_username_unique", unique=True)
        except Exception:
            pass
        try:
            self.users_collection.create_index([("email", ASCENDING)], name="user_email_unique", unique=True)
        except Exception:
            pass
        try:
            self.users_collection.create_index([("verification_token", ASCENDING)], name="user_verify_token_idx")
        except Exception:
            pass

        # ----- openai_collection -----
        try:
            self.openai_collection.create_index(
                [("username", ASCENDING), ("timestamp", DESCENDING)],
                name="openai_user_time_idx",
            )
        except Exception:
            pass

        # ----- login_attempts_collection -----
        try:
            self.login_attempts_collection.create_index(
                [("username", ASCENDING)], name="login_username_unique", unique=True
            )
        except Exception:
            pass
        try:
            self.login_attempts_collection.create_index([("last_attempt", DESCENDING)], name="login_last_attempt_idx")
        except Exception:
            pass

        # ----- refresh_tokens_collection (TTL por exp) -----
        try:
            self.refresh_tokens_collection.create_index([("jti", ASCENDING)], name="refresh_jti_unique", unique=True)
        except Exception:
            pass
        try:
            self.refresh_tokens_collection.create_index([("user_id", ASCENDING)], name="refresh_user_idx")
        except Exception:
            pass
        try:
            self.refresh_tokens_collection.create_index(
                [("exp", ASCENDING)], name="refresh_exp_ttl", expireAfterSeconds=0
            )
        except Exception:
            pass

        # ----- rate_limits_collection (TTL por reset_at) ⭐ -----
        try:
            self.rate_limits_collection.create_index([("key", ASCENDING)], name="rl_key_unique", unique=True)
        except Exception:
            pass
        try:
            # TTL: Mongo purga el doc cuando reset_at < now (~cada 60s)
            self.rate_limits_collection.create_index(
                [("reset_at", ASCENDING)], name="rl_reset_ttl", expireAfterSeconds=0
            )
        except Exception:
            pass

    # ============================================================
    # =================== USERS COLLECTION =======================
    # ============================================================

    def get_user(self, username: str):
        return self.users_collection.find_one({"username": username})

    def get_user_by_email(self, email: str):
        return self.users_collection.find_one({"email": email})

    def get_user_by_token(self, token: str):
        return self.users_collection.find_one({"verification_token": token})

    def get_user_by_verification_token(self, token: str):
        return self.users_collection.find_one({"verification_token": token})

    def create_user(
        self,
        username: str,
        password: str,
        is_admin: bool,
        is_verified: bool,
        email: str,
        allow_notifications: bool = True,
    ):
        hashed = hash_password(password)
        token = str(uuid4())
        self.users_collection.insert_one(
            {
                "username": username,
                "password": hashed,
                "is_admin": is_admin,
                "email": email,
                "allow_notifications": allow_notifications,
                "is_verified": is_verified,
                "verification_token": token,
            }
        )
        return token

    def verify_user_email(self, username: str):
        self.users_collection.update_one({"username": username}, {"$set": {"is_verified": True}})

    def update_user_password(self, username: str, new_hashed_password: str):
        self.users_collection.update_one({"username": username}, {"$set": {"password": new_hashed_password}})

    def delete_user(self, username: str) -> dict:
        res_user = self.users_collection.delete_one({"username": username})
        res_history = self.openai_collection.delete_many({"username": username})
        res_attempts = self.login_attempts_collection.delete_many({"username": username})
        res_tokens = self.refresh_tokens_collection.delete_many({"user_id": username})
        return {
            "deleted_user": res_user.deleted_count,
            "deleted_history": res_history.deleted_count,
            "deleted_login_attempts": res_attempts.deleted_count,
            "deleted_refresh_tokens": res_tokens.deleted_count,
        }

    # ============================================================
    # ============== OPENAI CONTENT COLLECTION ==================
    # ============================================================

    def save_generated_content(self, username: str, prompt: str, content: str, content_type: str, tone: str):
        self.openai_collection.insert_one(
            {
                "username": username,
                "prompt": prompt,
                "content": content,
                "content_type": content_type,
                "tone": tone,
                "timestamp": datetime.now(timezone.utc),
            }
        )

    def get_user_history(self, username: str):
        return list(
            self.openai_collection.find({"username": username}, {"_id": 0}).sort("timestamp", DESCENDING)
        )

    def clear_user_history(self, username: str) -> int:
        res = self.openai_collection.delete_many({"username": username})
        return res.deleted_count

    # ============================================================
    # ============ LOGIN ATTEMPTS COLLECTION =====================
    # ============================================================

    def get_login_attempt(self, username: str):
        return self.login_attempts_collection.find_one({"username": username})

    def create_login_attempt(self, username: str):
        self.login_attempts_collection.insert_one(
            {
                "username": username,
                "fail_count": 1,
                "last_attempt": datetime.now(timezone.utc),
                "blocked_until": None,
            }
        )

    def update_login_attempt(self, username: str, fail_count: int, blocked_until=None):
        if blocked_until and blocked_until.tzinfo is None:
            blocked_until = blocked_until.replace(tzinfo=timezone.utc)

        self.login_attempts_collection.update_one(
            {"username": username},
            {
                "$set": {
                    "fail_count": fail_count,
                    "last_attempt": datetime.now(timezone.utc),
                    "blocked_until": blocked_until,
                }
            },
        )

    def delete_login_attempt(self, username: str):
        self.login_attempts_collection.delete_one({"username": username})

    # ================================================================
    # === Password reset helpers (guardar / leer / limpiar código) ===
    # ================================================================

    def set_reset_code(self, email: str, code: str, expiry: datetime) -> bool:
        """Guarda el código de recuperación y su expiración para el usuario con ese email."""
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        res = self.users_collection.update_one(
            {"email": email},
            {"$set": {"reset_code": code, "reset_code_expiry": expiry}}
        )
        return res.matched_count == 1

    def get_reset_meta(self, email: str) -> dict | None:
        """Obtiene {reset_code, reset_code_expiry} para ese email (o None)."""
        return self.users_collection.find_one(
            {"email": email},
            {"_id": 0, "reset_code": 1, "reset_code_expiry": 1}
        )

    def clear_reset_code(self, email: str) -> bool:
        """Elimina los campos de recuperación tras usar el código o expirar."""
        res = self.users_collection.update_one(
            {"email": email},
            {"$unset": {"reset_code": "", "reset_code_expiry": ""}}
        )
        return res.modified_count == 1

    # ============================================================
    # ============ REFRESH TOKENS COLLECTION (STORE) =============
    # ============================================================

    def allow_refresh_token(self, jti: str, user_id: str, exp: datetime) -> None:
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        doc = {
            "jti": jti,
            "user_id": user_id,
            "exp": exp,
            "revoked": False,
            "created_at": datetime.now(timezone.utc),
        }

        try:
            self.refresh_tokens_collection.insert_one(doc)
        except DuplicateKeyError:
            self.refresh_tokens_collection.update_one(
                {"jti": jti, "user_id": user_id},
                {"$set": {"exp": exp, "revoked": False}},
            )

    def is_refresh_valid(self, jti: str, user_id: str) -> bool:
        doc = self.refresh_tokens_collection.find_one(
            {"jti": jti, "user_id": user_id}, {"_id": 0, "revoked": 1, "exp": 1}
        )
        if not doc or doc.get("revoked", False):
            return False

        exp = doc.get("exp")
        if not isinstance(exp, datetime):
            return False
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        return exp > datetime.now(timezone.utc)

    def revoke_refresh_token(self, jti: str) -> None:
        self.refresh_tokens_collection.update_one(
            {"jti": jti}, {"$set": {"revoked": True, "revoked_at": datetime.now(timezone.utc)}}
        )

    def revoke_all_refresh_tokens(self, user_id: str) -> int:
        res = self.refresh_tokens_collection.update_many(
            {"user_id": user_id, "revoked": {"$ne": True}},
            {"$set": {"revoked": True, "revoked_at": datetime.now(timezone.utc)}},
        )
        return getattr(res, "modified_count", 0)

    def cleanup_refresh_expired(self) -> int:
        now = datetime.now(timezone.utc)
        res = self.refresh_tokens_collection.delete_many({"exp": {"$lte": now}})
        return getattr(res, "deleted_count", 0)

    # ============================================================
    # ================= RATE LIMITS (Mongo TTL) ==================
    # ============================================================

    def rate_limit_hit(self, key: str, window_seconds: int, max_allowed: int) -> tuple[bool, int]:
        """
        Ventana fija con TTL:
        - Si no hay doc o la ventana expiró → inicia ventana (count=1).
        - Si existe y count >= max → bloquea (429) con Retry-After.
        - Si existe y count < max → incrementa (allow).
        Devuelve (allowed, retry_after_seconds).
        """
        now = datetime.now(timezone.utc)
        doc = self.rate_limits_collection.find_one({"key": key})

        # Nueva ventana o ventana expirada
        if not doc or not isinstance(doc.get("reset_at"), datetime) or doc["reset_at"] <= now:
            reset_at = now + timedelta(seconds=window_seconds)
            # upsert defensivo
            self.rate_limits_collection.update_one(
                {"key": key},
                {"$set": {"count": 1, "reset_at": reset_at, "updated_at": now}},
                upsert=True,
            )
            return True, 0

        # Ventana activa
        reset_at = doc["reset_at"]
        remaining = max(1, int((reset_at - now).total_seconds()))
        count = int(doc.get("count", 0))

        if count >= max_allowed:
            # Límite alcanzado
            return False, remaining

        # Incrementa contador dentro de la ventana
        self.rate_limits_collection.update_one(
            {"key": key},
            {"$inc": {"count": 1}, "$set": {"updated_at": now}},
        )
        return True, 0
