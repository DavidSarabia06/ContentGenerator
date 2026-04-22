from pydantic import BaseModel

# Modelo de datos para solicitudes de generación de contenido con Azure OpenAI.
# Este modelo valida y estructura los datos que el usuario envía a la API.
class ContentRequest(BaseModel):
    # prompt: el texto base o pregunta del usuario.
    prompt: str

    # content_type: el tipo de contenido a generar (ej: "email", "post", "anuncio", etc.).
    content_type: str

    # tone: el tono deseado para el contenido (ej: "formal", "casual", "divertido", etc.).
    tone: str


