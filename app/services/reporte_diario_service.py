from sqlalchemy import text
from app.db import SessionLocal


def obtener_reporte_operacion(fecha: str | None = None):
    db = SessionLocal()

    sql = """
        SELECT *
        FROM dbo.vw_kb_reporte_diario_operacion
    """
    params = {}

    if fecha:
        sql += " WHERE fecha = :fecha "
        params["fecha"] = fecha

    sql += " ORDER BY fecha DESC, nombre_area, nombre_operacion "

    result = db.execute(text(sql), params).mappings().all()
    db.close()
    return result


def obtener_reporte_terminados(fecha: str | None = None):
    db = SessionLocal()

    sql = """
        SELECT *
        FROM dbo.vw_kb_reporte_diario_terminados_area
    """
    params = {}

    if fecha:
        sql += " WHERE fecha = :fecha "
        params["fecha"] = fecha

    sql += " ORDER BY fecha DESC, nombre_area "

    result = db.execute(text(sql), params).mappings().all()
    db.close()
    return result
