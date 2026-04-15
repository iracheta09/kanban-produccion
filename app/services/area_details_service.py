from sqlalchemy import text
from app.db import SessionLocal


def obtener_details_area(id_area: int):
    db = SessionLocal()

    resumen = db.execute(text("""
        SELECT
            a.id_area,
            a.nombre_area,
            COUNT(f.id_ficha_estado) AS total_partidas,
            SUM(ISNULL(v.unidades_originales, 0)) AS total_piezas,
            SUM(ISNULL(v.kilos_originales, 0)) AS total_kilos,
            SUM(ISNULL(v.pies_originales, 0)) AS total_pies,
            SUM(CASE WHEN f.estado_actual = 'CURSO' THEN 1 ELSE 0 END) AS total_curso,
            SUM(CASE WHEN f.estado_actual = 'PAUSA' THEN 1 ELSE 0 END) AS total_pausa
        FROM dbo.kb_areas a
        LEFT JOIN dbo.kb_ficha_estado f
            ON f.id_area = a.id_area
           AND f.activo = 1
        LEFT JOIN dbo.vw_kb_tablero v
            ON v.id_ficha_estado = f.id_ficha_estado
        WHERE a.id_area = :id_area
        GROUP BY a.id_area, a.nombre_area
    """), {"id_area": id_area}).mappings().first()

    pendientes = db.execute(text("""
        SELECT COUNT(*) AS total
        FROM dbo.kb_transferencias
        WHERE id_area_destino = :id_area
          AND estatus_transferencia = 'PENDIENTE'
          AND activo = 1
    """), {"id_area": id_area}).scalar()

    fichas = db.execute(text("""
        SELECT
            f.id_ficha_estado,
            f.pa_tipo,
            f.ficha,
            v.tipo_ficha_origen,

            v.articulo,
            v.ar_tpiel,
            v.descripcion_articulo,

            v.unidades_originales,
            v.kilos_originales,
            v.pies_originales,

            v.nombre_operacion,
            f.estado_actual,
            f.nombre_operario_actual,
            f.nombre_caracteristica_actual,

            f.fecha_ultima_accion,
            f.fecha_inicio_actual,
            f.fecha_pausa,
            f.created_at AS fecha_recepcion_area,

            v.fecha_creacion_ficha,

            DATEDIFF(DAY, ISNULL(v.fecha_creacion_ficha, f.created_at), GETDATE()) AS dias_desde_creacion,
            DATEDIFF(DAY, f.created_at, GETDATE()) AS dias_en_area

        FROM dbo.kb_ficha_estado f
        INNER JOIN dbo.vw_kb_tablero v
            ON v.id_ficha_estado = f.id_ficha_estado
        WHERE f.id_area = :id_area
          AND f.activo = 1
        ORDER BY
            CASE f.estado_actual
                WHEN 'CURSO' THEN 1
                WHEN 'PAUSA' THEN 2
                WHEN 'LISTA' THEN 3
                ELSE 4
            END,
            v.nombre_operacion,
            f.fecha_ultima_accion DESC
    """), {"id_area": id_area}).mappings().all()

    db.close()

    return {
        "resumen": resumen,
        "pendientes": pendientes or 0,
        "fichas": fichas
    }
