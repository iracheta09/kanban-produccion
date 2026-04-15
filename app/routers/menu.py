from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from app.db import SessionLocal

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/menu", response_class=HTMLResponse)
def menu_principal(request: Request):
    """
    Pantalla principal del sistema con selección de áreas
    y acceso a mantenimiento de catálogos
    """
    db = SessionLocal()

    try:
        # Obtener resumen de áreas desde vista materializada
        areas = db.execute(text("""
            SELECT 
                id_area,
                nombre_area,
                total_partidas,
                total_piezas,
                total_kilos,
                total_pies
            FROM dbo.vw_kb_resumen_areas
            ORDER BY nombre_area
        """)).mappings().all()
        
        # Calcular totales globales
        totales = db.execute(text("""
            SELECT 
                SUM(total_partidas) AS total_partidas_global,
                SUM(total_piezas) AS total_piezas_global,
                SUM(total_kilos) AS total_kilos_global,
                SUM(total_pies) AS total_pies_global
            FROM dbo.vw_kb_resumen_areas
        """)).mappings().first()
        
    except Exception as e:
        print(f"Error en menu_principal: {str(e)}")
        areas = []
        totales = {"total_partidas_global": 0, "total_piezas_global": 0, "total_kilos_global": 0, "total_pies_global": 0}
    finally:
        db.close()

    return templates.TemplateResponse(
        "menu.html",
        {
            "request": request,
            "areas": areas,
            "totales": totales
        }
    )


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    Redirige a la pantalla de menú
    """
    return templates.TemplateResponse(
        "index_redirect.html",
        {"request": request}
    )
