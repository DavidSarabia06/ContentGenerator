import requests

# ⚠️ Usa el MISMO host que tu servidor FastAPI.
# Si uvicorn corre en 127.0.0.1, usa 127.0.0.1 aquí (no "localhost").
API = "http://127.0.0.1:8000"

ADMIN_USER = "Admin"   # ← tu usuario admin real
ADMIN_PASS = "0000"    # ← tu contraseña real


# ------------- Helpers -------------

def csrf_headers(session: requests.Session) -> dict:
    """Devuelve el header X-CSRF-Token a partir de la cookie csrf_refresh_token."""
    token = session.cookies.get("csrf_refresh_token")
    return {"X-CSRF-Token": token} if token else {}

def print_session_cookies(session: requests.Session, title="🍪 Cookies"):
    print(f"\n{title}")
    if not session.cookies:
        print("(sin cookies)")
    else:
        for c in session.cookies:
            preview = (c.value[:20] + "...") if len(c.value) > 20 else c.value
            print(f"- {c.name}={preview} (domain={c.domain}, path={c.path}, secure={c.secure})")


# ------------- Auth / Admin tests -------------

def login_admin(session: requests.Session) -> bool:
    print("🔐 Iniciando sesión como admin...")
    res = session.post(f"{API}/auth/login", json={
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    })

    if res.status_code == 200:
        print("✅ Login exitoso:", res.json())
        print_session_cookies(session)
        return True
    else:
        print("❌ Error al hacer login:", res.status_code, res.text)
        return False


def test_check_admin(session: requests.Session) -> bool:
    print("\n🛡️ Probando /auth/check_admin")
    res = session.get(f"{API}/auth/check_admin")
    if res.status_code == 200:
        print("✅ El usuario es administrador.")
        return True
    else:
        print("❌ Error:", res.status_code, res.text)
        return False


def test_get_users(session: requests.Session):
    print("\n👥 Probando /admin/list_users")
    res = session.get(f"{API}/admin/list_users")
    if res.status_code == 200:
        users = res.json()
        print(f"Total de usuarios: {len(users)}")
        for u in users:
            username = u.get("username", "Desconocido")
            role = "Admin" if u.get("is_admin", False) else "Usuario"
            print(f"- {username} ({role})")
    else:
        print("❌ Error:", res.status_code, res.text)


def test_get_users_summary(session: requests.Session):
    print("\n📊 Probando /admin/list_users_summary")
    res = session.get(f"{API}/admin/list_users_summary")
    if res.status_code == 200:
        summary = res.json()
        for r in summary:
            print(f"\n👤 Usuario: {r.get('_id')}")
            print(f"📄 Entradas: {r.get('total_entradas')}")
            print(f"📅 Última actividad: {r.get('ultima_actividad', 'N/A')}")
    else:
        print("❌ Error:", res.status_code, res.text)


# --- Opcionales: endpoints que requieren CSRF (POST/DELETE) ---

def test_register_user_by_admin(session: requests.Session, new_user: dict):
    """
    POST /admin/register_user_by_admin (requiere CSRF)
    new_user = {
        "username": "...",
        "password": "...",
        "email": "...",
        "isAdmin": false,
        "allow_notifications": true
    }
    """
    print("\n➕ Probando /admin/register_user_by_admin")
    headers = csrf_headers(session)
    if "X-CSRF-Token" not in headers:
        print("⚠️ No hay csrf_refresh_token en cookies. ¿Hiciste login?")
        return

    res = session.post(f"{API}/admin/register_user_by_admin", json=new_user, headers=headers)
    if res.status_code == 200:
        print("✅ Usuario creado por admin:", res.json())
    else:
        print("❌ Error:", res.status_code, res.text)


def test_delete_user_by_admin(session: requests.Session, username: str):
    """DELETE /admin/users/{username} (requiere CSRF)."""
    print(f"\n🗑️ Probando /admin/users/{username} (DELETE)")
    headers = csrf_headers(session)
    if "X-CSRF-Token" not in headers:
        print("⚠️ No hay csrf_refresh_token en cookies. ¿Hiciste login?")
        return

    res = session.delete(f"{API}/admin/users/{username}", headers=headers)
    if res.status_code == 200:
        print("✅ Usuario eliminado:", res.json())
    else:
        print("❌ Error:", res.status_code, res.text)


# ------------- Main -------------

if __name__ == "__main__":
    s = requests.Session()

    if login_admin(s):
        if test_check_admin(s):
            # test_get_users(s)
            # test_get_users_summary(s)

            # ---- Ejemplos opcionales (descomenta si quieres probarlos) ----
            nuevo = {
                "username": "user_creado_por_admin",
                "password": "0000",
                "email": "davidprojects1999@gmail.com",
                "isAdmin": False,
                "allow_notifications": True
            }
            # test_register_user_by_admin(s, nuevo)
            test_delete_user_by_admin(s, "user_creado_por_admin")
