from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from app.db import SessionLocal
from app.security.admin_guard import validar_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/catalogo/areas", response_class=HTMLResponse)
def catalogo_areas(request: Request, admin=Depends(validar_admin)):
    """Catálogo de áreas - Requiere autenticación admin"""
    db = SessionLocal()
    try:
        areas = db.execute(text("SELECT * FROM dbo.kb_areas ORDER BY nombre_area")).mappings().all()
    except Exception as e:
        areas = []
        print(f"Error: {e}")
    finally:
        db.close()
    
    return templates.TemplateResponse("catalogo_areas.html", {"request": request, "areas": areas})


@router.get("/catalogo/operaciones", response_class=HTMLResponse)
def catalogo_operaciones(request: Request, admin=Depends(validar_admin)):
    """Catálogo de operaciones - Requiere autenticación admin"""
    db = SessionLocal()
    try:
        operaciones = db.execute(text("SELECT * FROM dbo.kb_operaciones ORDER BY nombre_operacion")).mappings().all()
    except Exception as e:
        operaciones = []
        print(f"Error: {e}")
    finally:
        db.close()
    
    return templates.TemplateResponse("catalogo_operaciones.html", {"request": request, "operaciones": operaciones})


@router.get("/catalogo/partidas", response_class=HTMLResponse)
def catalogo_partidas(request: Request, admin=Depends(validar_admin)):
    """Catálogo de partidas - Requiere autenticación admin"""
    db = SessionLocal()
    try:
        partidas = db.execute(text("SELECT * FROM dbo.kb_partidas ORDER BY nombre_partida")).mappings().all()
    except Exception as e:
        partidas = []
        print(f"Error: {e}")
    finally:
        db.close()
    
    return templates.TemplateResponse("catalogo_partidas.html", {"request": request, "partidas": partidas})


@router.get("/catalogo/centrocostos", response_class=HTMLResponse)
def catalogo_centrocostos(request: Request, admin=Depends(validar_admin)):
    """Catálogo de centro de costos - Requiere autenticación admin"""
    db = SessionLocal()
    try:
        centrocostos = db.execute(text("SELECT DISTINCT centrocosto FROM dbo.kb_centrocostos ORDER BY centrocosto")).mappings().all()
    except Exception as e:
        centrocostos = []
        print(f"Error: {e}")
    finally:
        db.close()
    
    return templates.TemplateResponse("catalogo_centrocostos.html", {"request": request, "centrocostos": centrocostos})


@router.get("/catalogo/area-partidas", response_class=HTMLResponse)
def catalogo_area_partidas(request: Request, admin=Depends(validar_admin)):
    """Catálogo de área-partidas - Requiere autenticación admin"""
    db = SessionLocal()
    try:
        area_partidas = db.execute(text("SELECT * FROM dbo.kb_area_partidas ORDER BY id_area")).mappings().all()
    except Exception as e:
        area_partidas = []
        print(f"Error: {e}")
    finally:
        db.close()
    
    return templates.TemplateResponse("catalogo_area_partidas.html", {"request": request, "area_partidas": area_partidas})
