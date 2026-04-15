-- ===================================================================
-- 1. ACTUALIZAR LA VISTA DE PRODUCTIVIDAD BASE
-- ===================================================================

CREATE OR ALTER VIEW dbo.vw_kb_productividad_base
AS
SELECT
    m.id_mov,
    m.pa_tipo,
    m.ficha,
    m.id_area,
    a.nombre_area,
    m.id_operacion,
    o.nombre_operacion,
    m.id_operario,
    ISNULL(m.nombre_operario, 'SIN OPERARIO') AS nombre_operario,
    m.fecha_inicio,
    m.fecha_fin,
    m.pzas,
    m.kg,
    m.estatus_mov,
    m.forma_inicio,

    DATEDIFF(SECOND, m.fecha_inicio, m.fecha_fin) / 60.0 AS minutos_trabajados

FROM dbo.kb_produccion_mov m
INNER JOIN dbo.kb_areas a
    ON a.id_area = m.id_area
INNER JOIN dbo.kb_operaciones o
    ON o.id_operacion = m.id_operacion
WHERE m.estatus_mov = 'CERRADO'
GO

-- ===================================================================
-- 2. CREAR LA VISTA DE SUPERVISIÓN EN TIEMPO REAL (PIEZAS PRINCIPAL)
-- ===================================================================

CREATE OR ALTER VIEW dbo.vw_kb_tablero_supervision
AS
SELECT
    o.id_operacion,
    o.nombre_operacion,

    COUNT(CASE WHEN f.estado_actual = 'CURSO' THEN 1 END) AS en_curso,

    ISNULL(SUM(m.pzas),0) AS pzas_hoy,
    ISNULL(SUM(m.kg),0) AS kg_hoy,

    AVG(
        DATEDIFF(SECOND,m.fecha_inicio,m.fecha_fin) / 60.0
    ) AS promedio_min,

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
GO
