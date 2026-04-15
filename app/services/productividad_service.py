from sqlalchemy import text
from app.db import SessionLocal


def obtener_productividad_operario(id_area=None):
    db = SessionLocal()

    try:
        sql = """
            SELECT
                ISNULL(nombre_operario, 'SIN OPERARIO') AS nombre_operario,
                COUNT(*) AS movimientos,
                SUM(ISNULL(pzas, 0)) AS total_pzas,
                SUM(ISNULL(kg, 0)) AS total_kg,
                SUM(ISNULL(minutos_trabajados, 0)) AS total_minutos,
                CASE 
                    WHEN SUM(ISNULL(minutos_trabajados, 0)) = 0 THEN 0
                    ELSE ROUND(SUM(ISNULL(pzas, 0)) * 1.0 / SUM(ISNULL(minutos_trabajados, 0)), 2)
                END AS pzas_por_minuto,
                CASE 
                    WHEN SUM(ISNULL(minutos_trabajados, 0)) = 0 THEN 0
                    ELSE ROUND(SUM(ISNULL(pzas, 0)) * 60.0 / SUM(ISNULL(minutos_trabajados, 0)), 2)
                END AS pzas_por_hora
            FROM dbo.vw_kb_productividad_base
        """

        params = {}

        if id_area is not None:
            sql += " WHERE id_area = :id_area "
            params["id_area"] = id_area

        sql += """
            GROUP BY ISNULL(nombre_operario, 'SIN OPERARIO')
            ORDER BY total_pzas DESC
        """

        result = db.execute(text(sql), params).mappings().all()
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


def obtener_productividad_operacion(id_area=None):
    db = SessionLocal()

    try:
        sql = """
            SELECT
                nombre_operacion,
                COUNT(*) AS movimientos,
                SUM(ISNULL(pzas, 0)) AS total_pzas,
                SUM(ISNULL(kg, 0)) AS total_kg,
                AVG(ISNULL(minutos_trabajados, 0)) AS promedio_minutos,
                CASE 
                    WHEN SUM(ISNULL(minutos_trabajados, 0)) = 0 THEN 0
                    ELSE ROUND(SUM(ISNULL(pzas, 0)) * 1.0 / SUM(ISNULL(minutos_trabajados, 0)), 2)
                END AS pzas_por_minuto
            FROM dbo.vw_kb_productividad_base
        """

        params = {}

        if id_area is not None:
            sql += " WHERE id_area = :id_area "
            params["id_area"] = id_area

        sql += """
            GROUP BY nombre_operacion
            ORDER BY total_pzas DESC
        """

        result = db.execute(text(sql), params).mappings().all()
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


def obtener_productividad_area():
    db = SessionLocal()

    try:
        sql = """
            SELECT
                nombre_area,
                COUNT(*) AS movimientos,
                SUM(ISNULL(pzas, 0)) AS total_pzas,
                SUM(ISNULL(kg, 0)) AS total_kg,
                SUM(ISNULL(minutos_trabajados, 0)) AS total_minutos
            FROM dbo.vw_kb_productividad_base
            GROUP BY nombre_area
            ORDER BY total_pzas DESC
        """

        result = db.execute(text(sql)).mappings().all()
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


def obtener_productividad_diaria(id_area=None):
    db = SessionLocal()

    try:
        sql = """
            SELECT
                CONVERT(date, fecha_inicio) AS fecha,
                nombre_operario,
                nombre_operacion,
                SUM(ISNULL(pzas, 0)) AS total_pzas,
                SUM(ISNULL(kg, 0)) AS total_kg,
                SUM(ISNULL(minutos_trabajados, 0)) AS total_minutos
            FROM dbo.vw_kb_productividad_base
        """

        params = {}

        if id_area is not None:
            sql += " WHERE id_area = :id_area "
            params["id_area"] = id_area

        sql += """
            GROUP BY
                CONVERT(date, fecha_inicio),
                nombre_operario,
                nombre_operacion
            ORDER BY fecha DESC, total_pzas DESC
        """

        result = db.execute(text(sql), params).mappings().all()
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


def obtener_tablero_supervision():
    """Tablero en tiempo real con piezas como métrica principal y último operario"""
    db = SessionLocal()

    try:
        sql = """
            SELECT
                o.id_operacion,
                o.nombre_operacion,
                COUNT(CASE WHEN f.estado_actual = 'CURSO' THEN 1 END) AS en_curso,
                ISNULL(SUM(m.pzas),0) AS pzas_hoy,
                ISNULL(SUM(m.kg),0) AS kg_hoy,
                AVG(DATEDIFF(SECOND,m.fecha_inicio,m.fecha_fin) / 60.0) AS promedio_min,
                ISNULL(
                    (SELECT TOP 1 nombre_operario
                     FROM dbo.kb_produccion_mov
                     WHERE id_operacion = o.id_operacion
                       AND CONVERT(date, fecha_inicio) = CONVERT(date, GETDATE())
                       AND estatus_mov = 'CERRADO'
                     ORDER BY fecha_fin DESC),
                    'N/A'
                ) AS ultimo_operario
            FROM dbo.kb_operaciones o
            LEFT JOIN dbo.kb_ficha_estado f
                ON f.id_operacion_actual = o.id_operacion
               AND f.activo = 1
            LEFT JOIN dbo.kb_produccion_mov m
                ON m.id_operacion = o.id_operacion
               AND CONVERT(date, m.fecha_inicio) = CONVERT(date, GETDATE())
               AND m.estatus_mov = 'CERRADO'
            GROUP BY
                o.id_operacion,
                o.nombre_operacion
            ORDER BY o.id_operacion
        """

        result = db.execute(text(sql)).mappings().all()
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        db.close()

