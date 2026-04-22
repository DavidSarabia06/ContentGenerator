from print_utils import print_boxed_message, print_subline_message
import requests
from time import sleep

# 📌 URL base de tu API para autenticación
API_URL = "http://127.0.0.1:8000/auth"

# 🔐 Datos del usuario
user_data = {
    "username": "TestUser",
    "password": "0000",
    "email": "davidprojects1999@gmail.com",
    "allow_notifications": True
}

# 🔐 Datos del administrador
admin_data = {
    "username": "Admin",
    "password": "0000",
    "email": "contentgeneratorinfo@gmail.com",
    "allow_notifications": True
}

# 🆕 Nueva contraseña para pruebas
NEW_PASSWORD = "0001"

# ---------- Helpers ----------
def csrf_header(session: requests.Session):
    csrf = session.cookies.get("csrf_refresh_token")
    return {"X-CSRF-Token": csrf} if csrf else {}

def print_cookies(session: requests.Session, title="🍪 Cookies de sesión"):
    print_subline_message(title, border_symbol="-", color="cyan")
    if not session.cookies:
        print("(sin cookies)")
    else:
        for c in session.cookies:
            print(f"- {c.name}={c.value[:20]}... (domain={c.domain}, path={c.path})")
    print("")

# ---------- Endpoints de prueba ----------
def test_register(session: requests.Session, data: dict):
    print_subline_message("🔐 Registrando usuario...", border_symbol="-", color="blue")
    resp = session.post(f"{API_URL}/register", json=data)
    if resp.status_code == 200:
        print("✅ Registro exitoso. Revisa tu correo para verificar la cuenta.")
    else:
        print("⚠️ Registro fallido:", safe_json(resp))

def test_register_admin(session: requests.Session, data: dict):
    print_subline_message("🔐 Registrando Administrador...", border_symbol="-", color="blue")
    resp = session.post(f"{API_URL}/register_admin", json=data)
    if resp.status_code == 200:
        print("✅ Registro de administrador exitoso.")
    else:
        print("⚠️ Registro de administrador fallido:", safe_json(resp))

def test_login(session: requests.Session, data: dict, pwd: str | None = None):
    pwd = pwd or data["password"]
    print_subline_message(f"🔑 Login de {data['username']} (pwd: {pwd})", border_symbol="-", color="green")
    payload = {"username": data["username"], "password": pwd}
    resp = session.post(f"{API_URL}/login", json=payload)

    if resp.status_code == 200:
        print("✅ Login exitoso")
        print("↩️ Respuesta:", safe_json(resp))
        print_cookies(session)
        return True
    else:
        print("❌ Login fallido:", safe_json(resp))
        return False

def test_change_password(session: requests.Session, data: dict, new_password: str):
    print_subline_message("🔄 Cambiando contraseña...", border_symbol="-", color="magenta")
    body = {"current_password": data["password"], "new_password": new_password}
    resp = session.post(f"{API_URL}/change_password", json=body)  # usa cookie access_token
    if resp.status_code == 200:
        print("✅ Contraseña cambiada con éxito.")
        data["password"] = new_password  # actualiza para siguientes pruebas
    else:
        print("❌ Error al cambiar contraseña:", safe_json(resp))

def test_refresh(session: requests.Session):
    print_subline_message("♻️ Refresh de sesión (rotación de tokens)...", border_symbol="-", color="yellow")
    headers = csrf_header(session)
    if "X-CSRF-Token" not in headers:
        print("⚠️ No hay csrf_refresh_token en cookies. ¿Hiciste login?")
        return
    resp = session.post(f"{API_URL}/refresh", headers=headers)
    if resp.status_code == 200:
        print("✅ Refresh OK:", safe_json(resp))
        print_cookies(session, "🍪 Cookies tras refresh")
    else:
        print("❌ Refresh fallido:", safe_json(resp))

def test_logout(session: requests.Session):
    print_subline_message("🚪 Logout...", border_symbol="-", color="red")
    headers = csrf_header(session)
    if "X-CSRF-Token" not in headers:
        print("⚠️ No hay csrf_refresh_token en cookies. ¿Hiciste login?")
        return
    resp = session.post(f"{API_URL}/logout", headers=headers)
    if resp.status_code == 200:
        print("✅ Logout OK.")
    else:
        print("❌ Logout fallido:", safe_json(resp))
    print_cookies(session, "🍪 Cookies tras logout")

def test_failed_logins(data: dict, attempts=5):
    print_subline_message(f"🚫 Probando {attempts} intentos fallidos de login...", border_symbol="-", color="red")
    wrong_password = "incorrecta"
    for i in range(attempts):
        print(f"❌ Intento {i+1}:")
        s = requests.Session()
        test_login(s, data, pwd=wrong_password)
        sleep(1.5)

# ---------- Utilidad ----------
def safe_json(resp: requests.Response):
    try:
        return resp.json()
    except Exception:
        return resp.text

# ---------- Flujo principal ----------
if __name__ == "__main__":
    print_boxed_message("TEST DE AUTENTICACIÓN (cookies + CSRF)", bold=True, border_symbol="-", color="yellow")
    tipo = input("¿Registrar como administrador (1) o usuario (0)? ").strip()

    s_register = requests.Session()

    if tipo == "1":
        current_data = admin_data
        test_register_admin(s_register, current_data)
        sleep(2)
    else:
        current_data = user_data
        test_register(s_register, current_data)
        input("\n📧 Verifica el correo antes de continuar.\nPresiona ENTER tras hacer clic en el enlace de verificación...")

    # Nueva sesión para login real
    s = requests.Session()

    print("\n🔐 Intentando login real...")
    if test_login(s, current_data):
        # Cambiar contraseña usando cookie de access_token
        test_change_password(s, current_data, NEW_PASSWORD)

        # Probar refresh (requiere CSRF header + refresh_token cookie)
        test_refresh(s)

        # Logout (requiere CSRF header)
        test_logout(s)

        # Login con la nueva contraseña en una nueva sesión
        print("\n🔁 Probando login con la nueva contraseña...")
        s2 = requests.Session()
        test_login(s2, current_data)
