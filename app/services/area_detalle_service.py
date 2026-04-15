from sqlalchemy import text
from app.db import SessionLocal
from datetime import datetime


def obtener_fichas_activas_detalle(id_area: int):
    """
    Obtiene listado de fichas ACTIVAS en un área con detalle enriquecido:
    - Identificación (pa_tipo + ficha)
    - Estado actual y operación
    - Fechas clave (creación, entrada a área)
    - Días en el área y desde creación
    - Cantidades (iniciales, actuales, producidas)
    - Operario actual
    - Historial de operaciones
    """
    db = SessionLocal()
    
    try:
        fichas = db.execute(text("""
            SELECT
                f.pa_tipo,
                f.ficha,
                f.ficha AS identificador,
                f.estado_actual,
                ISNULL(o.nombre_operacion, 'Sin operación') AS operacion_actual,
                ISNULL(f.nombre_operario_actual, 'Sin asignar') AS operario_actual,
                f.pzas_iniciales,
                f.pzas_actuales,
                ISNULL(f.pzas_iniciales - f.pzas_actuales, 0) AS pzas_producidas,
                f.kg_iniciales,
                f.kg_actuales,
                ISNULL(f.kg_iniciales - f.kg_actuales, 0) AS kg_producido,
                f.pies_iniciales,
                f.pies_actuales,
                ISNULL(f.pies_iniciales - f.pies_actuales, 0) AS pies_producidos,
                f.created_at,
                f.fecha_inicio,
                f.fecha_ultima_accion,
                DATEDIFF(DAY, f.created_at, GETDATE()) AS dias_desde_creacion,
                CASE 
                    WHEN f.fecha_inicio IS NULL THEN 0
                    ELSE DATEDIFF(DAY, f.fecha_inicio, GETDATE())
                END AS dias_en_area,
                a1.nombre_area AS area_actual,
                ISNULL(a2.nombre_area, 'N/A') AS area_origen,
                f.id_ficha_estado
            FROM dbo.kb_ficha_estado f
            LEFT JOIN dbo.kb_operaciones o ON f.id_operacion_actual = o.id_operacion
            LEFT JOIN dbo.kb_areas a1 ON f.id_area = a1.id_area
            LEFT JOIN dbo.kb_areas a2 ON f.id_area_origen = a2.id_area
            WHERE f.id_area = :id_area AND f.activo = 1
            ORDER BY f.fecha_ultima_accion DESC
        """), {"id_area": id_area}).mappings().all()
        
        # Para cada ficha, obtener historial de operaciones
        fichas_detalle = []
        for ficha in fichas:
            ficha_dict = dict(ficha)
            
            # Obtener historial de operaciones
            historial = db.execute(text("""
                SELECT
                    CONVERT(DATE, m.fecha_inicio) AS fecha,
                    o.nombre_operacion,
                    m.nombre_operario,
                    m.pzas,
                    m.kg,
                    m.pies,
                    DATEDIFF(MINUTE, m.fecha_inicio, m.fecha_fin) AS minutos,
                    m.fecha_inicio,
                    m.fecha_fin
                FROM dbo.kb_produccion_mov m
                JOIN dbo.kb_operaciones o ON m.id_operacion = o.id_operacion
                WHERE m.pa_tipo = :pa_tipo AND m.ficha = :ficha
                ORDER BY m.fecha_fin DESC
            """), {"pa_tipo": ficha.pa_tipo, "ficha": ficha.ficha}).mappings().all()
            
            ficha_dict['historial_operaciones'] = list(historial) if historial else []
            fichas_detalle.append(ficha_dict)
        
        return fichas_detalle
        
    except Exception as e:
        print(f"Error en obtener_fichas_activas_detalle: {str(e)}")
        return []
        
    finally:
        db.close()


def obtener_resumen_area(id_area: int, fecha: str | None = None):
    """
    Obtiene resumen completo de un área:
    - Totales de fichas, piezas, en curso, en pausa
    - Transferencias pendientes por recibir
    - Producción del día por operación
    - Fichas terminadas del día
    """
    db = SessionLocal()

    try:
        # 1. Resumen general del área
        resumen = db.execute(text("""
            SELECT
                a.id_area,
                a.nombre_area,
                COUNT(f.id_ficha_estado) AS total_fichas,
                SUM(ISNULL(f.pzas_actuales, 0)) AS total_pzas,
                SUM(CASE WHEN f.estado_actual = 'CURSO' THEN 1 ELSE 0 END) AS total_curso,
                SUM(CASE WHEN f.estado_actual = 'PAUSA' THEN 1 ELSE 0 END) AS total_pausa
            FROM dbo.kb_areas a
            LEFT JOIN dbo.kb_ficha_estado f
                ON f.id_area = a.id_area
                AND f.activo = 1
            WHERE a.id_area = :id_area
            GROUP BY a.id_area, a.nombre_area
        """), {"id_area": id_area}).mappings().first()

        # 2. Pendientes por recibir
        pendientes = db.execute(text("""
            SELECT COUNT(*) AS total
            FROM dbo.kb_transferencias
            WHERE id_area_destino = :id_area
              AND estatus_transferencia = 'PENDIENTE'
              AND activo = 1
        """), {"id_area": id_area}).scalar()

        # 3. Producción del día por operación
        sql_oper = """
            SELECT *
            FROM dbo.vw_kb_reporte_diario_operacion
            WHERE id_area = :id_area
        """
        params_oper = {"id_area": id_area}

        if fecha:
            sql_oper += " AND fecha = :fecha "
            params_oper["fecha"] = fecha

        sql_oper += " ORDER BY fecha DESC, nombre_operacion "

        produccion_operacion = db.execute(text(sql_oper), params_oper).mappings().all()

        # 4. Fichas terminadas del día
        sql_term = """
            SELECT *
            FROM dbo.vw_kb_reporte_diario_terminados_area
            WHERE id_area = :id_area
        """
        params_term = {"id_area": id_area}

        if fecha:
            sql_term += " AND fecha = :fecha "
            params_term["fecha"] = fecha

        sql_term += " ORDER BY fecha DESC "

        terminados = db.execute(text(sql_term), params_term).mappings().all()
        
        # 5. Fichas activas con detalle enriquecido
        db.close()
        fichas_activas = obtener_fichas_activas_detalle(id_area)

    except Exception as e:
        print(f"Error en obtener_resumen_area: {str(e)}")
        resumen = None
        pendientes = 0
        produccion_operacion = []
        terminados = []
        fichas_activas = []

    finally:
        try:
            db.close()
        except:
            pass

    return {
        "resumen": resumen,
        "pendientes": pendientes or 0,
        "produccion_operacion": list(produccion_operacion) if produccion_operacion else [],
        "terminados": list(terminados) if terminados else [],
        "fichas_activas": fichas_activas
    }
