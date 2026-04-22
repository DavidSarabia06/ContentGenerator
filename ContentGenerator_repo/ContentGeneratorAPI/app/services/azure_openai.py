import os
from openai import AzureOpenAI  # Cliente oficial de OpenAI para Azure
from app.models.azure_models import ContentRequest  # Modelo de entrada para el contenido a generar
from dotenv import load_dotenv  # Para cargar las variables de entorno desde .env

# 🌍 Cargar variables de entorno (.env)
load_dotenv()

# 🚀 Crear cliente para conectarse al servicio Azure OpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),             # Clave del recurso de Azure OpenAI
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),     # Endpoint del recurso
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")      # Versión de la API de Azure OpenAI
)

# 🧠 Nombre del modelo desplegado (deployment ID) definido en Azure
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# 🎯 Función principal para generar contenido con IA
async def generate_content(data: ContentRequest) -> str:
    """
    Recibe los parámetros definidos por el usuario y genera contenido usando Azure OpenAI.
    """
    response = client.chat.completions.create(
        model=DEPLOYMENT,  # Nombre del modelo desplegado en Azure (ej: "gpt-4")
        messages=[
            {
                "role": "system",
                "content": f"You are a helpful assistant writing {data.content_type} in a {data.tone} tone."
                # Mensaje de sistema que define el rol del asistente
            },
            {
                "role": "user",
                "content": data.prompt
                # Prompt del usuario: el tema o instrucciones para generar el contenido
            }
        ]
    )

    # Devuelve solo el contenido generado (texto plano) de la primera respuesta
    return response.choices[0].message.content
