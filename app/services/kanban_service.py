from sqlalchemy import text
from app.db import SessionLocal


def obtener_tablero(id_area: int):
    """
    Obtiene toda la información del tablero Kanban para un área:
    - Operaciones
    - Fichas
    - Nombre del área
    - Contadores (activas, en curso, en pausa, pendientes por recibir)
    """
    db = SessionLocal()

    try:
        # 1. Operaciones del área
        operaciones = db.execute(text("""
            SELECT *
            FROM dbo.kb_operaciones
            WHERE id_area = :id_area
              AND activo = 1
            ORDER BY orden_visual
        """), {"id_area": id_area}).mappings().all()

        # 2. Fichas del área
        fichas = db.execute(text("""
            SELECT *
            FROM dbo.vw_kb_tablero
            WHERE id_area = :id_area
            ORDER BY orden_visual, fecha_ultima_accion DESC
        """), {"id_area": id_area}).mappings().all()

        # 3. Nombre del área
        area = db.execute(text("""
            SELECT nombre_area
            FROM dbo.kb_areas
            WHERE id_area = :id_area
        """), {"id_area": id_area}).mappings().first()

        # 4. Transferencias pendientes de recibción
        pendientes_resultado = db.execute(text("""
            SELECT COUNT(*) AS total
            FROM dbo.kb_transferencias
            WHERE id_area_destino = :id_area
              AND estatus_transferencia = 'PENDIENTE'
              AND activo = 1
        """), {"id_area": id_area}).mappings().first()

        # 5. Calcular contadores
        fichas_list = list(fichas)
        total_activas = len(fichas_list)
        total_curso = sum(1 for f in fichas_list if f["estado_actual"] == "CURSO")
        total_pausa = sum(1 for f in fichas_list if f["estado_actual"] == "PAUSA")
        total_pendientes_recibir = pendientes_resultado["total"] if pendientes_resultado else 0

        return {
            "operaciones": operaciones,
            "fichas": fichas_list,
            "nombre_area": area["nombre_area"] if area else f"Área {id_area}",
            "total_activas": total_activas,
            "total_curso": total_curso,
            "total_pausa": total_pausa,
            "total_pendientes_recibir": total_pendientes_recibir
        }

    except Exception as e:
        print(f"Error en obtener_tablero: {str(e)}")
        return {
            "operaciones": [],
            "fichas": [],
            "nombre_area": f"Área {id_area}",
            "total_activas": 0,
            "total_curso": 0,
            "total_pausa": 0,
            "total_pendientes_recibir": 0
        }

    finally:
        db.close()