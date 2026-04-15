from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.reporte_diario_service import (
    obtener_reporte_operacion,
    obtener_reporte_terminados
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/reporte-diario", response_class=HTMLResponse)
def ver_reporte_diario(
    request: Request,
    fecha: str | None = None,
    vista: str = "operacion"
):
    if vista == "terminados":
        data = obtener_reporte_terminados(fecha)
        titulo = "Reporte Diario - Terminados por Área"
    else:
        data = obtener_reporte_operacion(fecha)
        titulo = "Reporte Diario - Producción por Operación"

    return templates.TemplateResponse(
        "reporte_diario.html",
        {
            "request": request,
            "data": data,
            "titulo": titulo,
            "fecha": fecha or "",
            "vista": vista
        }
    )
