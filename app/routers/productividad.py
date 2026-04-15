from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.productividad_service import (
    obtener_productividad_operario,
    obtener_productividad_operacion,
    obtener_productividad_area,
    obtener_productividad_diaria,
    obtener_tablero_supervision
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/tablero", response_class=HTMLResponse)
def ver_tablero_supervision(request: Request):
    data = obtener_tablero_supervision()

    return templates.TemplateResponse(
        "tablero_supervision.html",
        {
            "request": request,
            "data": data,
            "titulo": "Tablero de Producción en Tiempo Real"
        }
    )


@router.get("/productividad", response_class=HTMLResponse)
def ver_productividad(request: Request):
    data = obtener_productividad_operario()

    return templates.TemplateResponse(
        "productividad.html",
        {
            "request": request,
            "data": data,
            "titulo": "Productividad general por operario"
        }
    )


@router.get("/productividad/{id_area}", response_class=HTMLResponse)
def ver_productividad_area(request: Request, id_area: int):
    data = obtener_productividad_operario(id_area)

    return templates.TemplateResponse(
        "productividad.html",
        {
            "request": request,
            "data": data,
            "titulo": f"Productividad por operario - Area {id_area}"
        }
    )


@router.get("/productividad-operaciones", response_class=HTMLResponse)
def ver_productividad_operaciones(request: Request):
    data = obtener_productividad_operacion()

    return templates.TemplateResponse(
        "productividad_operaciones.html",
        {
            "request": request,
            "data": data,
            "titulo": "Productividad por operación"
        }
    )


@router.get("/productividad-areas", response_class=HTMLResponse)
def ver_productividad_areas(request: Request):
    data = obtener_productividad_area()

    return templates.TemplateResponse(
        "productividad_areas.html",
        {
            "request": request,
            "data": data,
            "titulo": "Productividad por área"
        }
    )


@router.get("/productividad-diaria", response_class=HTMLResponse)
def ver_productividad_diaria(request: Request, id_area: int = None):
    data = obtener_productividad_diaria(id_area)

    titulo = "Productividad diaria"
    if id_area:
        titulo += f" - Area {id_area}"

    return templates.TemplateResponse(
        "productividad_diaria.html",
        {
            "request": request,
            "data": data,
            "titulo": titulo
        }
    )
