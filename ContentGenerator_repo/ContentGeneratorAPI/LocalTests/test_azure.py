import requests
from constants_and_tools import ConstantsAndTools

from typing import Dict, List, Tuple, Literal

API_BASE = "http://localhost:8000"
AUTH_URL = f"{API_BASE}/auth"
GEN_URL = f"{API_BASE}/generate"

# 🧪 Credenciales del usuario de prueba
user_data: Dict[str, str] = {
    "username": "David",
    "password": "123456"
}


ct: ConstantsAndTools = ConstantsAndTools()

# 🔐 Obtener el token JWT iniciando sesión
def get_token() -> None | str:
    response = requests.post(f"{AUTH_URL}/login", json=user_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("❌ Login fallido:", response.json())
        return None

# 🧠 Probar /generate (solo genera contenido, no lo guarda)
def test_generate(token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "prompt": "Escribe una publicación sobre IA en redes sociales",
        "content_type": "post",
        "tone": "casual"
    }
    response = requests.post(f"{GEN_URL}/", json=payload, headers=headers)
    print("📩 /generate:", response.status_code)
    print(response.json())

# 💾 Probar /generate/save (genera y guarda el contenido)
def test_generate_and_save(token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "prompt": "Crea una descripción de producto para una consola.",
        "content_type": "product_description",
        "tone": "profesional"
    }
    response: requests.Response = requests.post(f"{GEN_URL}/save", json=payload, headers=headers)
    print("💾 /generate/save:", response.status_code)
    print(response.json())

# 📜 Probar /generate/history (ver historial de contenido)
@ct.hx_info_decorator
def test_history(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{GEN_URL}/history", headers=headers)
    print("📜 /generate/history:", response.status_code)

    if response.status_code == 200:
        items = response.json()  # ✅ Ahora es una lista directamente
        print("🧪 Número de entradas:", len(items))

        for i, entry in enumerate(items, 1):
            print("\n" + "=" * 60)
            print(f"📌 Entrada #{i}")
            print("=" * 60)
            print(f"📅 Fecha: {entry.get('fecha', 'No disponible')}")
            print(f"📂 Intro:\n{entry['intro']}\n")
            print(f"📥 Prompt:\n{entry['prompt']}\n")

            # 🔠 Formatear el contenido para añadir intros después de puntos y comas
            contenido_formateado = entry["contenido"].replace(". ", ".\n").replace(", ", ",\n")

            print("✍️ Contenido generado:\n")
            print(contenido_formateado)
            print("=" * 60 + "\n")

    else:
        print("❌ Error al obtener historial:", response.json())


if __name__ == "__main__":
    token = get_token()
    if token:
        # test_generate(token)
        #test_generate_and_save(token)
        test_history(token)

