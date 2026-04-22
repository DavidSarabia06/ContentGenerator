from fastapi import APIRouter, Depends
from datetime import datetime
from app.services.azure_openai import generate_content
from app.services.database_mongoDB import MongoConnector
from app.models.azure_models import ContentRequest
from app.services.auth_service import get_current_user
from app.utils.datetime_utils import DatetimeUtils  # ✅ NUEVA UTILIDAD

db = MongoConnector()

router = APIRouter(prefix="/generate", tags=["Content"])

# Mapeo para mostrar los tipos con nombres más amigables
TYPE_LABELS = {
    "product_description": "Descripción de producto",
    "email": "Email",
    "post": "Publicación"
}

@router.post("/")
async def generate(
    data: ContentRequest,
    user: str = Depends(get_current_user)
):
    """
    Endpoint para generar contenido sin guardar en base de datos.
    """
    return {"content": await generate_content(data)}


@router.post("/save")
async def generate_and_save(
    data: ContentRequest,
    user: str = Depends(get_current_user)
):
    """
    Endpoint que genera contenido con Azure OpenAI y lo guarda en la base de datos.
    """
    generated = await generate_content(data)
    db.save_generated_content(
        username=user,
        prompt=data.prompt,
        content=generated,
        content_type=data.content_type,
        tone=data.tone
    )
    return {"content": generated}


@router.get("/history")
def history(user: str = Depends(get_current_user)):
    """
    Devuelve el historial completo de contenidos generados por el usuario,
    con intros descriptivos y la fecha convertida a la hora local del sistema.
    """
    items = db.get_user_history(user)

    enhanced_items = []
    for i, item in enumerate(items, 1):
        tipo_legible = TYPE_LABELS.get(item["content_type"], item["content_type"].capitalize())
        intro = f"📝 Entrada #{i} - Tipo: {tipo_legible} - Tono: {item['tone'].capitalize()}"

        fecha = item.get("timestamp")
        if fecha:
            if isinstance(fecha, str):
                fecha = datetime.fromisoformat(fecha)
            fecha_str = DatetimeUtils.format_local_time(fecha, "%Y-%m-%d %H:%M:%S")
        else:
            fecha_str = "Fecha no disponible"

        enhanced_items.append({
            "intro": intro,
            "contenido": item["content"],
            "prompt": item["prompt"],
            "fecha": fecha_str
        })

    return enhanced_items


@router.delete("/history/clear")
def clear_history(user: str = Depends(get_current_user)):
    """
    🧹 Elimina todo el historial de contenidos generados del usuario autenticado.
    """
    deleted_count = db.clear_user_history(user)
    return {"message": f"{deleted_count} entradas eliminadas del historial."}
