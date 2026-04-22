
from fastapi import FastAPI
from app.routers import azure_routers, auth_routers,encrypt_routers,admin_routers
from fastapi.middleware.cors import CORSMiddleware

# 🌍 Cargar variables de entorno (.env)
from dotenv import load_dotenv
load_dotenv()

# Creamos una instancia de la aplicación FastAPI
app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
    ],
    allow_credentials=True,        # ← IMPRESCINDIBLE para cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)

# Registramos los routers de contenido generado por Azure OpenAI y de autenticación
app.include_router(azure_routers.router)    # Prefijo: /generate
app.include_router(auth_routers.router)     # Prefijo: /auth
app.include_router(encrypt_routers.router)  # Prefijo: /crypt
app.include_router(admin_routers.router)  # Prefijo: /crypt

# Ruta raíz de la API. Útil como punto de comprobación inicial.
@app.get("/")
def root():
    return {"message": "Generador de Contenido funcionando"}

# Ruta simple para comprobar si el servidor está vivo (usada como health check)
@app.get("/ping")
def ping():
    return {"status": "ok"}

# if __name__ == "__main__":
#     pass