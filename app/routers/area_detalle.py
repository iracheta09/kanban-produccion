from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.area_detalle_service import obtener_resumen_area
from app.services.area_details_service import obtener_details_area

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/area/{id_area}/detalle", response_class=HTMLResponse)
def ver_detalle_area(
    request: Request,
    id_area: int,
    fecha: str | None = None
):
    """
    Pantalla de detalle de un área con resumen y reportes
    """
    data = obtener_resumen_area(id_area, fecha)

    return templates.TemplateResponse(
        "area_detalle.html",
        {
            "request": request,
            "id_area": id_area,
            "fecha": fecha or "",
            "resumen": data["resumen"],
            "pendientes": data["pendientes"],
            "produccion_operacion": data["produccion_operacion"],
            "terminados": data["terminados"],
            "fichas_activas": data.get("fichas_activas", [])
        }
    )


@router.get("/area/{id_area}/details", response_class=HTMLResponse)
def ver_details_area(request: Request, id_area: int):
    """
    Pantalla de estado vivo del área con fichas activas
    """
    data = obtener_details_area(id_area)

    return templates.TemplateResponse(
        "area_details.html",
        {
            "request": request,
            "id_area": id_area,
            "resumen": data["resumen"],
            "pendientes": data["pendientes"],
            "fichas": data["fichas"]
        }
    )
