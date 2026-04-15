from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from app.db import SessionLocal
from app.security.admin_guard import validar_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/catalogos/areas", response_class=HTMLResponse)
def listar_areas(request: Request, guard=Depends(validar_admin)):
    db = SessionLocal()

    areas = db.execute(text("""
        SELECT
            id_area,
            clave_area,
            nombre_area,
            descripcion,
            activo,
            orden_visual,
            created_at,
            updated_at
        FROM dbo.kb_areas
        ORDER BY orden_visual, nombre_area
    """)).mappings().all()

    db.close()

    admin_key = request.query_params.get("admin_key", "")

    return templates.TemplateResponse(
        "catalogos/areas_list.html",
        {
            "request": request,
            "areas": areas,
            "admin_key": admin_key
        }
    )


@router.get("/catalogos/areas/nueva", response_class=HTMLResponse)
def nueva_area(request: Request, guard=Depends(validar_admin)):
    admin_key = request.query_params.get("admin_key", "")

    return templates.TemplateResponse(
        "catalogos/areas_form.html",
        {
            "request": request,
            "modo": "nuevo",
            "area": None,
            "error": None,
            "admin_key": admin_key
        }
    )


@router.get("/catalogos/areas/{id_area}/editar", response_class=HTMLResponse)
def editar_area(id_area: int, request: Request, guard=Depends(validar_admin)):
    db = SessionLocal()

    area = db.execute(text("""
        SELECT
            id_area,
            clave_area,
            nombre_area,
            descripcion,
            activo,
            orden_visual
        FROM dbo.kb_areas
        WHERE id_area = :id_area
    """), {"id_area": id_area}).mappings().first()

    db.close()

    admin_key = request.query_params.get("admin_key", "")

    return templates.TemplateResponse(
        "catalogos/areas_form.html",
        {
            "request": request,
            "modo": "editar",
            "area": area,
            "error": None,
            "admin_key": admin_key
        }
    )


@router.post("/catalogos/areas/guardar")
def guardar_area(
    request: Request,
    id_area: int = Form(0),
    clave_area: str = Form(...),
    nombre_area: str = Form(...),
    descripcion: str = Form(""),
    orden_visual: int = Form(...),
    activo: int = Form(1),
    admin_key: str = Form(...)
):
    db = SessionLocal()

    clave_area = clave_area.strip()
    nombre_area = nombre_area.strip()
    descripcion = descripcion.strip()

    if not clave_area or not nombre_area:
        area_data = {
            "id_area": id_area,
            "clave_area": clave_area,
            "nombre_area": nombre_area,
            "descripcion": descripcion,
            "activo": bool(activo),
            "orden_visual": orden_visual
        }

        db.close()
        return templates.TemplateResponse(
            "catalogos/areas_form.html",
            {
                "request": request,
                "modo": "editar" if id_area else "nuevo",
                "area": area_data,
                "error": "Clave y nombre son obligatorios.",
                "admin_key": admin_key
            }
        )

    # validar clave duplicada
    existe_clave = db.execute(text("""
        SELECT COUNT(*)
        FROM dbo.kb_areas
        WHERE clave_area = :clave_area
          AND id_area <> :id_area
    """), {
        "clave_area": clave_area,
        "id_area": id_area
    }).scalar()

    if existe_clave and existe_clave > 0:
        area_data = {
            "id_area": id_area,
            "clave_area": clave_area,
            "nombre_area": nombre_area,
            "descripcion": descripcion,
            "activo": bool(activo),
            "orden_visual": orden_visual
        }

        db.close()
        return templates.TemplateResponse(
            "catalogos/areas_form.html",
            {
                "request": request,
                "modo": "editar" if id_area else "nuevo",
                "area": area_data,
                "error": "La clave de área ya existe.",
                "admin_key": admin_key
            }
        )

    # validar nombre duplicado
    existe_nombre = db.execute(text("""
        SELECT COUNT(*)
        FROM dbo.kb_areas
        WHERE nombre_area = :nombre_area
          AND id_area <> :id_area
    """), {
        "nombre_area": nombre_area,
        "id_area": id_area
    }).scalar()

    if existe_nombre and existe_nombre > 0:
        area_data = {
            "id_area": id_area,
            "clave_area": clave_area,
            "nombre_area": nombre_area,
            "descripcion": descripcion,
            "activo": bool(activo),
            "orden_visual": orden_visual
        }

        db.close()
        return templates.TemplateResponse(
            "catalogos/areas_form.html",
            {
                "request": request,
                "modo": "editar" if id_area else "nuevo",
                "area": area_data,
                "error": "El nombre de área ya existe.",
                "admin_key": admin_key
            }
        )

    if id_area and id_area > 0:
        db.execute(text("""
            UPDATE dbo.kb_areas
            SET clave_area = :clave_area,
                nombre_area = :nombre_area,
                descripcion = :descripcion,
                activo = :activo,
                orden_visual = :orden_visual,
                updated_at = GETDATE()
            WHERE id_area = :id_area
        """), {
            "id_area": id_area,
            "clave_area": clave_area,
            "nombre_area": nombre_area,
            "descripcion": descripcion,
            "activo": activo,
            "orden_visual": orden_visual
        })
    else:
        db.execute(text("""
            INSERT INTO dbo.kb_areas
            (
                clave_area,
                nombre_area,
                descripcion,
                activo,
                orden_visual,
                created_at
            )
            VALUES
            (
                :clave_area,
                :nombre_area,
                :descripcion,
                :activo,
                :orden_visual,
                GETDATE()
            )
        """), {
            "clave_area": clave_area,
            "nombre_area": nombre_area,
            "descripcion": descripcion,
            "activo": activo,
            "orden_visual": orden_visual
        })

    db.commit()
    db.close()

    return RedirectResponse(
        url=f"/catalogos/areas?admin_key={admin_key}",
        status_code=303
    )


@router.post("/catalogos/areas/{id_area}/toggle")
def toggle_area(
    id_area: int,
    admin_key: str = Form(...)
):
    db = SessionLocal()

    area = db.execute(text("""
        SELECT activo
        FROM dbo.kb_areas
        WHERE id_area = :id_area
    """), {"id_area": id_area}).mappings().first()

    if area:
        nuevo_activo = 0 if area["activo"] else 1

        db.execute(text("""
            UPDATE dbo.kb_areas
            SET activo = :activo,
                updated_at = GETDATE()
            WHERE id_area = :id_area
        """), {
            "id_area": id_area,
            "activo": nuevo_activo
        })

        db.commit()

    db.close()

    return RedirectResponse(
        url=f"/catalogos/areas?admin_key={admin_key}",
        status_code=303
    )
