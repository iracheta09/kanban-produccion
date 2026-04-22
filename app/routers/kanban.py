from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlalchemy import text
from pydantic import BaseModel

from app.services.kanban_service import obtener_tablero
from app.services.alerta_service import registrar_evento_alerta
from app.db import SessionLocal

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


class MoverFicha(BaseModel):
    ficha: str
    pa_tipo: str
    id_operacion: int
    id_operario: str | None = None
    nombre_operario: str | None = None
    id_operacion_caracteristica: int | None = None
    nombre_caracteristica: str | None = None


class FinalizarFicha(BaseModel):
    ficha: str
    pa_tipo: str
    pzas: float | None = None
    kg: float | None = None
    pies: float | None = None


class EnviarFicha(BaseModel):
    ficha: str
    pa_tipo: str
    id_area_origen: int
    id_area_destino: int
    id_operacion_origen: int | None = None
    enviado_por: str | None = None
    enviado_por_nombre: str | None = None
    requiere_regreso: bool = False
    id_area_retorno: int | None = None
    observaciones: str | None = None


class RecibirTransferencia(BaseModel):
    id_transferencia: int
    recibido_por: str | None = None
    recibido_por_nombre: str | None = None


@router.get("/kanban/areas-destino")
def obtener_areas_destino():
    """
    Lista todas las áreas disponibles como destino
    NOTA: Esta ruta DEBE ir antes de /kanban/{id_area} para evitar conflictos
    """
    db = SessionLocal()

    try:
        result = db.execute(text("""
            SELECT
                id_area,
                nombre_area
            FROM dbo.kb_areas
            WHERE activo = 1
            ORDER BY nombre_area
        """)).mappings().all()

        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@router.get("/kanban/{id_area}", response_class=HTMLResponse)
def ver_tablero(request: Request, id_area: int):

    tablero = obtener_tablero(id_area)

    return templates.TemplateResponse(
        "kanban.html",
        {
            "request": request,
            "id_area": id_area,
            "operaciones": tablero["operaciones"],
            "fichas": tablero["fichas"],
            "nombre_area": tablero["nombre_area"],
            "total_activas": tablero["total_activas"],
            "total_curso": tablero["total_curso"],
            "total_pausa": tablero["total_pausa"],
            "total_pendientes_recibir": tablero["total_pendientes_recibir"]
        }
    )


@router.get("/kanban/operarios/{id_area}")
def obtener_operarios(id_area: int):

    db = SessionLocal()

    try:
        result = db.execute(text("""
            SELECT
                wp.personal AS id_operario,
                wp.Nombre_Personal AS nombre_operario
            FROM kb_centrocostos kc
            INNER JOIN [192.168.39.11].intelisisweb.dbo.w_personal wp
                ON wp.CENTROCOSTOS = kc.centrocosto
            WHERE kc.id_area = :area
              AND kc.activo = 1
            ORDER BY wp.Nombre_Personal
        """), {
            "area": id_area
        })

        operarios = [
            {
                "id_operario": str(r.id_operario),
                "nombre_operario": r.nombre_operario
            }
            for r in result
        ]

        return operarios

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@router.get("/kanban/operaciones-area/{id_area}")
def obtener_operaciones_area(id_area: int):
    db = SessionLocal()

    try:
        data = db.execute(text("""
            SELECT
                id_operacion,
                nombre_operacion,
                tipo_operacion,
                orden_visual
            FROM dbo.kb_operaciones
            WHERE id_area = :id_area
              AND activo = 1
            ORDER BY orden_visual
        """), {"id_area": id_area}).mappings().all()

        operaciones = [dict(row) for row in data]
        return operaciones

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@router.post("/kanban/mover-ficha")
async def mover_ficha(data: MoverFicha):
    db = SessionLocal()

    try:
        # Obtener datos de la operación destino
        operacion_destino = db.execute(text("""
            SELECT
                id_operacion,
                nombre_operacion,
                tipo_operacion
            FROM dbo.kb_operaciones
            WHERE id_operacion = :id_operacion
        """), {
            "id_operacion": data.id_operacion
        }).mappings().first()

        # Si la operación destino es FINALIZACION, finalizar inmediatamente
        if operacion_destino and operacion_destino["tipo_operacion"] == "FINALIZACION":

            result = db.execute(text("""
                UPDATE kb_ficha_estado
                SET id_operacion_actual = :op,
                    estado_actual = 'FINALIZADA',
                    fecha_ultima_accion = GETDATE(),
                    id_operario_actual = :id_operario,
                    nombre_operario_actual = :nombre_operario,
                    id_operacion_caracteristica = :id_operacion_caracteristica,
                    nombre_caracteristica_actual = :nombre_caracteristica,
                    updated_at = GETDATE(),
                    activo = 0
                WHERE ficha = :ficha
                  AND pa_tipo = :tipo
                  AND estado_actual = 'LISTA'
                  AND activo = 1
            """), {
                "op": data.id_operacion,
                "ficha": data.ficha,
                "tipo": data.pa_tipo,
                "id_operario": data.id_operario,
                "nombre_operario": data.nombre_operario,
                "id_operacion_caracteristica": data.id_operacion_caracteristica,
                "nombre_caracteristica": data.nombre_caracteristica
            })

            if result.rowcount == 0:
                db.rollback()
                db.close()
                return {"status": "error", "message": "La ficha no está en LISTA o no existe"}

            db.execute(text("""
                INSERT INTO kb_produccion_mov
                (
                    pa_tipo,
                    ficha,
                    id_area,
                    id_operacion,
                    id_operario,
                    nombre_operario,
                    id_operacion_caracteristica,
                    nombre_caracteristica,
                    fecha_inicio,
                    fecha_fin,
                    estatus_mov,
                    forma_inicio,
                    created_at
                )
                SELECT
                    :pa_tipo,
                    :ficha,
                    id_area,
                    :id_operacion,
                    :id_operario,
                    :nombre_operario,
                    :id_operacion_caracteristica,
                    :nombre_caracteristica,
                    GETDATE(),
                    GETDATE(),
                    'CERRADO',
                    'CLICK',
                    GETDATE()
                FROM dbo.kb_areas
                WHERE EXISTS (
                    SELECT 1
                    FROM dbo.kb_operaciones o
                    WHERE o.id_operacion = :id_operacion
                      AND o.id_area = kb_areas.id_area
                )
            """), {
                "pa_tipo": data.pa_tipo,
                "ficha": data.ficha,
                "id_operacion": data.id_operacion,
                "id_operario": data.id_operario,
                "nombre_operario": data.nombre_operario,
                "id_operacion_caracteristica": data.id_operacion_caracteristica,
                "nombre_caracteristica": data.nombre_caracteristica
            })

            db.commit()
            db.close()
            return {"status": "ok", "finalizada": True}

        # Flujo normal para operaciones que no son FINALIZACION
        result = db.execute(text("""
            UPDATE kb_ficha_estado
            SET id_operacion_actual = :op,
                estado_actual = 'CURSO',
                fecha_inicio_actual = GETDATE(),
                fecha_ultima_accion = GETDATE(),
                id_operario_actual = :id_operario,
                nombre_operario_actual = :nombre_operario,
                id_operacion_caracteristica = :id_operacion_caracteristica,
                nombre_caracteristica_actual = :nombre_caracteristica,
                updated_at = GETDATE()
            WHERE ficha = :ficha
              AND pa_tipo = :tipo
              AND estado_actual = 'LISTA'
              AND activo = 1
        """), {
            "op": data.id_operacion,
            "ficha": data.ficha,
            "tipo": data.pa_tipo,
            "id_operario": data.id_operario,
            "nombre_operario": data.nombre_operario,
            "id_operacion_caracteristica": data.id_operacion_caracteristica,
            "nombre_caracteristica": data.nombre_caracteristica
        })

        if result.rowcount == 0:
            db.rollback()
            return {"status": "error", "message": "La ficha no esta en LISTA o no existe"}

        # Obtener datos actualizados de la ficha
        ficha_actualizada = db.execute(text("""
            SELECT
                id_area,
                id_operacion_actual,
                nombre_operario_actual
            FROM kb_ficha_estado
            WHERE ficha = :ficha
              AND pa_tipo = :tipo
        """), {
            "ficha": data.ficha,
            "tipo": data.pa_tipo
        }).mappings().first()

        insert_result = db.execute(text("""
            INSERT INTO kb_produccion_mov
            (
                pa_tipo,
                ficha,
                id_area,
                id_operacion,
                id_operario,
                nombre_operario,
                id_operacion_caracteristica,
                nombre_caracteristica,
                fecha_inicio,
                estatus_mov,
                forma_inicio,
                created_at
            )
            SELECT
                pa_tipo,
                ficha,
                id_area,
                id_operacion_actual,
                id_operario_actual,
                nombre_operario_actual,
                id_operacion_caracteristica,
                nombre_caracteristica_actual,
                GETDATE(),
                'CURSO',
                'CLICK',
                GETDATE()
            FROM kb_ficha_estado
            WHERE ficha = :ficha
              AND pa_tipo = :tipo
              AND activo = 1
        """), {
            "ficha": data.ficha,
            "tipo": data.pa_tipo
        })

        # Registrar evento INICIO_FICHA para todas las áreas (dispara notificación WhatsApp)
        if ficha_actualizada:
            # Obtener nombre del área y de la operación
            area_info = db.execute(text("""
                SELECT nombre_area
                FROM kb_areas
                WHERE id_area = :id_area
            """), {"id_area": ficha_actualizada["id_area"]}).scalar()

            nombre_area = area_info or f"Área {ficha_actualizada['id_area']}"

            nombre_operacion = db.execute(text("""
                SELECT nombre_operacion
                FROM kb_operaciones
                WHERE id_operacion = :id_operacion
            """), {"id_operacion": ficha_actualizada["id_operacion_actual"]}).scalar()

            # Obtener pzas_actuales para enviar en WhatsApp (si es NULL, usar 0)
            pzas_actuales = db.execute(text("""
                SELECT ISNULL(pzas_actuales, 0) as pzas
                FROM kb_ficha_estado
                WHERE ficha = :ficha
                  AND pa_tipo = :tipo
            """), {
                "ficha": data.ficha,
                "tipo": data.pa_tipo
            }).scalar()

            mensaje = (
                f"{nombre_area}: {data.nombre_operario} inició la ficha "
                f"{data.pa_tipo}-{data.ficha} en {nombre_operacion}."
            )

            # Usar registrar_evento_alerta para que dispare automáticamente WhatsApp
            registrar_evento_alerta(
                tipo_evento="INICIO_FICHA",
                id_area=ficha_actualizada["id_area"],
                nombre_area=nombre_area,
                pa_tipo=data.pa_tipo,
                ficha=data.ficha,
                id_operacion=ficha_actualizada["id_operacion_actual"],
                nombre_operacion=nombre_operacion,
                id_operario=data.id_operario,
                nombre_operario=data.nombre_operario,
                pzas=pzas_actuales,
                mensaje=mensaje,
                db=db
            )

        db.commit()

        return {
            "status": "ok",
            "updated_rows": result.rowcount,
            "inserted_rows": insert_result.rowcount
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@router.post("/kanban/finalizar-ficha")
async def finalizar_ficha(data: FinalizarFicha):
    db = SessionLocal()

    try:
        # 0. Obtener datos actuales de la ficha ANTES de actualizar
        ficha_actual = db.execute(text("""
            SELECT
                pa_tipo,
                ficha,
                id_area,
                id_operacion_actual,
                nombre_operario_actual
            FROM dbo.kb_ficha_estado
            WHERE pa_tipo = :tipo
              AND ficha = :ficha
              AND activo = 1
        """), {
            "tipo": data.pa_tipo,
            "ficha": data.ficha
        }).mappings().first()

        # 1. Cerrar el ultimo movimiento abierto
        mov_result = db.execute(text("""
            UPDATE kb_produccion_mov
            SET fecha_fin = GETDATE(),
                pzas = :pzas,
                kg = :kg,
                pies = :pies,
                estatus_mov = 'CERRADO',
                updated_at = GETDATE()
            WHERE id_mov = (
                SELECT MAX(id_mov)
                FROM kb_produccion_mov
                WHERE pa_tipo = :tipo
                  AND ficha = :ficha
                  AND estatus_mov = 'CURSO'
            )
        """), {
            "tipo": data.pa_tipo,
            "ficha": data.ficha,
            "pzas": data.pzas,
            "kg": data.kg,
            "pies": data.pies
        })

        # 2. Regresar ficha a LISTA
        ficha_result = db.execute(text("""
            UPDATE kb_ficha_estado
            SET estado_actual = 'LISTA',
                id_operario_actual = NULL,
                nombre_operario_actual = NULL,
                fecha_inicio_actual = NULL,
                pzas_actuales = :pzas,
                kg_actuales = :kg,
                pies_actuales = :pies,
                fecha_ultima_accion = GETDATE(),
                updated_at = GETDATE()
            WHERE pa_tipo = :tipo
              AND ficha = :ficha
              AND estado_actual = 'CURSO'
        """), {
            "tipo": data.pa_tipo,
            "ficha": data.ficha,
            "pzas": data.pzas,
            "kg": data.kg,
            "pies": data.pies
        })

        if ficha_result.rowcount == 0:
            db.rollback()
            return {"status": "error", "message": "La ficha no esta en CURSO o no existe"}

        # 3. Registrar evento de alerta FIN_OPERACION si es Acabado
        if ficha_actual and int(ficha_actual["id_area"]) == 2:
            nombre_operacion = db.execute(text("""
                SELECT nombre_operacion
                FROM kb_operaciones
                WHERE id_operacion = :id_operacion
            """), {
                "id_operacion": ficha_actual["id_operacion_actual"]
            }).scalar()

            mensaje = (
                f"Acabado: {ficha_actual['nombre_operario_actual'] or 'Operario'} terminó la ficha "
                f"{data.pa_tipo}-{data.ficha} en {nombre_operacion}. "
                f"Pzas: {data.pzas}, Kg: {data.kg}."
            )

            registrar_evento_alerta(
                tipo_evento="FIN_OPERACION",
                id_area=ficha_actual["id_area"],
                nombre_area="ACABADO",
                pa_tipo=data.pa_tipo,
                ficha=data.ficha,
                id_operacion=ficha_actual["id_operacion_actual"],
                nombre_operacion=nombre_operacion,
                nombre_operario=ficha_actual["nombre_operario_actual"],
                pzas=data.pzas,
                mensaje=mensaje,
                db=db
            )

            # 4. Registrar evento LOTE_TERMINADO si la operación es FINALIZACION
            tipo_operacion = db.execute(text("""
                SELECT tipo_operacion
                FROM kb_operaciones
                WHERE id_operacion = :id_operacion
            """), {
                "id_operacion": ficha_actual["id_operacion_actual"]
            }).scalar()

            if tipo_operacion == "FINALIZACION":
                total_hoy = db.execute(text("""
                    SELECT COUNT(*)
                    FROM dbo.kb_produccion_mov m
                    INNER JOIN dbo.kb_operaciones o
                        ON o.id_operacion = m.id_operacion
                    WHERE m.id_area = 2
                      AND m.estatus_mov = 'CERRADO'
                      AND o.tipo_operacion = 'FINALIZACION'
                      AND CONVERT(date, m.fecha_fin) = CONVERT(date, GETDATE())
                """)).scalar()

                mensaje_lote = f"Acabado: se concluyó el lote {total_hoy} del día."

                registrar_evento_alerta(
                    tipo_evento="LOTE_TERMINADO",
                    id_area=2,
                    nombre_area="ACABADO",
                    mensaje=mensaje_lote,
                    db=db
                )

        db.commit()

        return {
            "status": "ok",
            "mov_updated": mov_result.rowcount,
            "ficha_updated": ficha_result.rowcount
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@router.get("/kanban/pendientes-recibir/{id_area}", response_class=HTMLResponse)
def pendientes_recibir(request: Request, id_area: int):
    """
    Muestra la bandeja de recepciones pendientes para un área
    """
    db = SessionLocal()

    try:
        result = db.execute(text("""
            SELECT
                t.id_transferencia,
                t.pa_tipo,
                t.ficha,
                ao.nombre_area AS area_origen,
                ad.nombre_area AS area_destino,
                t.fecha_envio,
                t.enviado_por_nombre,
                t.observaciones
            FROM dbo.kb_transferencias t
            INNER JOIN dbo.kb_areas ao
                ON ao.id_area = t.id_area_origen
            INNER JOIN dbo.kb_areas ad
                ON ad.id_area = t.id_area_destino
            WHERE t.id_area_destino = :id_area
              AND t.estatus_transferencia = 'PENDIENTE'
              AND t.activo = 1
            ORDER BY t.fecha_envio
        """), {"id_area": id_area}).mappings().all()

        return templates.TemplateResponse(
            "recepciones.html",
            {
                "request": request,
                "transferencias": result,
                "id_area": id_area
            }
        )

    except Exception as e:
        return f"<h2>Error: {str(e)}</h2>"

    finally:
        db.close()


@router.post("/kanban/enviar-ficha")
async def enviar_ficha(data: EnviarFicha):
    """
    Envía una ficha a otra área:
    1. Valida que la ficha existe, está activa y en LISTA
    2. Crea registro en kb_transferencias
    3. Desactiva la ficha del tablero origen (activo=0)
    """
    db = SessionLocal()

    try:
        # 1. Obtener la ficha actual
        ficha_actual = db.execute(text("""
            SELECT
                pa_tipo,
                ficha,
                id_area,
                id_operacion_actual,
                estado_actual,
                activo
            FROM dbo.kb_ficha_estado
            WHERE pa_tipo = :pa_tipo
              AND ficha = :ficha
              AND activo = 1
        """), {
            "pa_tipo": data.pa_tipo,
            "ficha": data.ficha
        }).mappings().first()

        if not ficha_actual:
            return {"status": "error", "message": "La ficha no existe activa en el tablero"}

        # 2. Validar que está en LISTA
        if ficha_actual["estado_actual"] != "LISTA":
            return {"status": "error", "message": "Solo se pueden enviar fichas en LISTA"}

        # 3. Validar que el área origen coincide
        if int(ficha_actual["id_area"]) != int(data.id_area_origen):
            return {"status": "error", "message": "El área origen no coincide con la ficha activa"}

        # 4. Validar que no haya transferencia pendiente ya
        ya_pendiente = db.execute(text("""
            SELECT COUNT(*)
            FROM dbo.kb_transferencias
            WHERE pa_tipo = :pa_tipo
              AND ficha = :ficha
              AND estatus_transferencia = 'PENDIENTE'
              AND activo = 1
        """), {
            "pa_tipo": data.pa_tipo,
            "ficha": data.ficha
        }).scalar()

        if ya_pendiente and ya_pendiente > 0:
            return {"status": "error", "message": "La ficha ya tiene una transferencia pendiente"}

        # 5. Crear transferencia
        db.execute(text("""
            INSERT INTO dbo.kb_transferencias
            (
                pa_tipo,
                ficha,
                id_area_origen,
                id_area_destino,
                id_operacion_origen,
                estatus_transferencia,
                fecha_envio,
                enviado_por,
                enviado_por_nombre,
                requiere_regreso,
                id_area_retorno,
                observaciones,
                activo,
                created_at
            )
            VALUES
            (
                :pa_tipo,
                :ficha,
                :id_area_origen,
                :id_area_destino,
                :id_operacion_origen,
                'PENDIENTE',
                GETDATE(),
                :enviado_por,
                :enviado_por_nombre,
                :requiere_regreso,
                :id_area_retorno,
                :observaciones,
                1,
                GETDATE()
            )
        """), {
            "pa_tipo": data.pa_tipo,
            "ficha": data.ficha,
            "id_area_origen": data.id_area_origen,
            "id_area_destino": data.id_area_destino,
            "id_operacion_origen": data.id_operacion_origen,
            "enviado_por": data.enviado_por,
            "enviado_por_nombre": data.enviado_por_nombre,
            "requiere_regreso": 1 if data.requiere_regreso else 0,
            "id_area_retorno": data.id_area_retorno,
            "observaciones": data.observaciones
        })

        # 6. Desactivar la ficha en el tablero origen
        db.execute(text("""
            UPDATE dbo.kb_ficha_estado
            SET activo = 0,
                fecha_ultima_accion = GETDATE(),
                updated_at = GETDATE()
            WHERE pa_tipo = :pa_tipo
              AND ficha = :ficha
              AND activo = 1
        """), {
            "pa_tipo": data.pa_tipo,
            "ficha": data.ficha
        })

        db.commit()
        return {"status": "ok"}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@router.post("/kanban/recibir-transferencia")
async def recibir_transferencia(data: RecibirTransferencia):
    """
    Confirma la recepción de una transferencia:
    1. Mete la ficha en kb_ficha_estado del área destino
    2. La coloca en operación de RECEPCION
    3. Actualiza el estado de la transferencia a RECIBIDA
    """
    db = SessionLocal()

    try:
        # 1. Obtener datos de la transferencia
        transferencia = db.execute(text("""
            SELECT
                t.id_transferencia,
                t.pa_tipo,
                t.ficha,
                t.id_area_origen,
                t.id_area_destino
            FROM dbo.kb_transferencias t
            WHERE t.id_transferencia = :id_transferencia
              AND t.estatus_transferencia = 'PENDIENTE'
              AND t.activo = 1
        """), {"id_transferencia": data.id_transferencia}).mappings().first()

        if not transferencia:
            return {"status": "error", "message": "Transferencia no encontrada o ya recibida"}

        # 2. Obtener operacion RECEPCION del área destino
        id_operacion_recepcion = db.execute(text("""
            SELECT TOP 1 id_operacion
            FROM dbo.kb_operaciones
            WHERE id_area = :id_area
              AND tipo_operacion = 'RECEPCION'
              AND activo = 1
            ORDER BY orden_visual
        """), {"id_area": transferencia["id_area_destino"]}).scalar()

        if not id_operacion_recepcion:
            return {"status": "error", "message": "No existe operacion de recepcion en el area destino"}

        # 3. Verificar que la ficha no existe activa ya en el destino
        existe_activa = db.execute(text("""
            SELECT COUNT(*)
            FROM dbo.kb_ficha_estado
            WHERE pa_tipo = :pa_tipo
              AND ficha = :ficha
              AND activo = 1
        """), {
            "pa_tipo": transferencia["pa_tipo"],
            "ficha": transferencia["ficha"]
        }).scalar()

        if existe_activa and existe_activa > 0:
            return {"status": "error", "message": "La ficha ya existe activa en el tablero"}

        # 4. Insertar ficha en kb_ficha_estado del área destino
        db.execute(text("""
            INSERT INTO dbo.kb_ficha_estado
            (
                ficha,
                pa_tipo,
                id_area,
                id_operacion_actual,
                estado_actual,
                id_transferencia_actual,
                id_area_origen,
                tipo_ingreso,
                fecha_ultima_accion,
                origen_ficha,
                activo,
                created_at
            )
            VALUES
            (
                :ficha,
                :pa_tipo,
                :id_area_destino,
                :id_operacion_recepcion,
                'LISTA',
                :id_transferencia,
                :id_area_origen,
                'TRANSFERIDA',
                GETDATE(),
                'ERP',
                1,
                GETDATE()
            )
        """), {
            "ficha": transferencia["ficha"],
            "pa_tipo": transferencia["pa_tipo"],
            "id_area_destino": transferencia["id_area_destino"],
            "id_operacion_recepcion": id_operacion_recepcion,
            "id_transferencia": transferencia["id_transferencia"],
            "id_area_origen": transferencia["id_area_origen"]
        })

        # 5. Actualizar transferencia como RECIBIDA
        db.execute(text("""
            UPDATE dbo.kb_transferencias
            SET estatus_transferencia = 'RECIBIDA',
                fecha_recepcion = GETDATE(),
                recibido_por = :recibido_por,
                recibido_por_nombre = :recibido_por_nombre,
                updated_at = GETDATE()
            WHERE id_transferencia = :id_transferencia
        """), {
            "id_transferencia": data.id_transferencia,
            "recibido_por": data.recibido_por,
            "recibido_por_nombre": data.recibido_por_nombre
        })

        db.commit()
        return {"status": "ok"}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@router.post("/ficha/iniciar")
def iniciar_ficha(data: dict):
    """
    Inicia una ficha: cambia estado de LISTA a CURSO
    Registra evento de alerta si es área 2 (Acabado)
    """
    ficha = data.get("ficha")
    pa_tipo = data.get("pa_tipo")

    db = SessionLocal()

    try:
        # 1. Obtener datos actuales de la ficha
        ficha_actual = db.execute(text("""
            SELECT
                id_area,
                id_operacion_actual,
                id_operario_actual,
                nombre_operario_actual
            FROM dbo.kb_ficha_estado
            WHERE ficha = :ficha
              AND pa_tipo = :pa_tipo
              AND activo = 1
        """), {
            "ficha": ficha,
            "pa_tipo": pa_tipo
        }).mappings().first()

        if not ficha_actual:
            db.close()
            return {"ok": False, "error": "Ficha no encontrada"}

        # 2. Hacer update del estado
        db.execute(text("""
            UPDATE dbo.kb_ficha_estado
            SET estado_actual = 'CURSO',
                fecha_inicio = GETDATE(),
                fecha_ultima_accion = GETDATE()
            WHERE ficha = :ficha
            AND pa_tipo = :pa_tipo
            AND activo = 1
        """), {
            "ficha": ficha,
            "pa_tipo": pa_tipo
        })

        db.commit()

        # 3. Registrar evento de alerta si es Acabado (id_area = 2)
        if int(ficha_actual["id_area"]) == 2:
            # Obtener nombre de la operación
            nombre_operacion = db.execute(text("""
                SELECT nombre_operacion
                FROM kb_operaciones
                WHERE id_operacion = :id_operacion
            """), {"id_operacion": ficha_actual["id_operacion_actual"]}).scalar()

            # Obtener pzas_actuales para enviar en WhatsApp (si es NULL, usar 0)
            pzas_actuales = db.execute(text("""
                SELECT ISNULL(pzas_actuales, 0) as pzas
                FROM kb_ficha_estado
                WHERE ficha = :ficha
                  AND pa_tipo = :pa_tipo
            """), {
                "ficha": ficha,
                "pa_tipo": pa_tipo
            }).scalar()

            mensaje = (
                f"Acabado: {ficha_actual['nombre_operario_actual'] or 'Operario'} inició la ficha "
                f"{pa_tipo}-{ficha} en {nombre_operacion}."
            )

            registrar_evento_alerta(
                tipo_evento="INICIO_FICHA",
                id_area=ficha_actual["id_area"],
                nombre_area="ACABADO",
                pa_tipo=pa_tipo,
                ficha=ficha,
                id_operacion=ficha_actual["id_operacion_actual"],
                nombre_operacion=nombre_operacion,
                id_operario=ficha_actual["id_operario_actual"],
                nombre_operario=ficha_actual["nombre_operario_actual"],
                pzas=pzas_actuales,
                mensaje=mensaje,
                db=db
            )

        db.close()
        return {"ok": True}

    except Exception as e:
        db.rollback()
        db.close()
        return {"ok": False, "error": str(e)}


@router.get("/kanban/buscar-partida/{id_area}/{numero_ficha}")
def buscar_partida(id_area: int, numero_ficha: str):
    """
    Busca una partida por número en el área especificada.
    Retorna: numero, estado, descripción y si hay acciones disponibles
    """
    db = SessionLocal()

    try:
        # Buscar la ficha en la base de datos usando vista vw_kb_tablero
        ficha = db.execute(text("""
            SELECT
                kf.ficha,
                kf.pa_tipo,
                kf.estado_actual,
                v.descripcion_articulo,
                v.unidades_originales,
                v.kilos_originales,
                kf.id_operacion_actual,
                ko.nombre_operacion,
                kf.nombre_operario_actual,
                kf.id_area
            FROM dbo.kb_ficha_estado kf
            LEFT JOIN dbo.vw_kb_tablero v ON v.id_ficha_estado = kf.id_ficha_estado
            LEFT JOIN dbo.kb_operaciones ko ON ko.id_operacion = kf.id_operacion_actual
            WHERE kf.ficha = :numero_ficha
              AND kf.id_area = :id_area
              AND kf.activo = 1
        """), {
            "numero_ficha": numero_ficha.strip(),
            "id_area": id_area
        }).mappings().first()

        if not ficha:
            return {
                "status": "error",
                "message": "Partida no encontrada en esta área"
            }

        # Determinar qué acciones son permitidas según estado
        acciones = {}
        if ficha["estado_actual"] == "LISTA":
            acciones = {
                "puede_iniciar": True,
                "puede_enviar": True,
                "puede_pausar": False,
                "puede_finalizar": False,
                "puede_reanudar": False
            }
        elif ficha["estado_actual"] == "CURSO":
            acciones = {
                "puede_iniciar": False,
                "puede_enviar": False,
                "puede_pausar": True,
                "puede_finalizar": True,
                "puede_reanudar": False
            }
        elif ficha["estado_actual"] == "PAUSA":
            acciones = {
                "puede_iniciar": False,
                "puede_enviar": False,
                "puede_pausar": False,
                "puede_finalizar": True,
                "puede_reanudar": True
            }
        else:  # FINALIZADA u otro
            acciones = {
                "puede_iniciar": False,
                "puede_enviar": False,
                "puede_pausar": False,
                "puede_finalizar": False,
                "puede_reanudar": False
            }

        return {
            "status": "ok",
            "ficha": {
                "numero": ficha["ficha"],
                "tipo": ficha["pa_tipo"],
                "estado": ficha["estado_actual"],
                "descripcion": ficha["descripcion_articulo"] or "",
                "unidades": ficha["unidades_originales"] or 0,
                "kilos": ficha["kilos_originales"] or 0,
                "operacion": ficha["nombre_operacion"] or "",
                "operario": ficha["nombre_operario_actual"] or "",
                "id_operacion": ficha["id_operacion_actual"]
            },
            "acciones": acciones
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@router.post("/ficha/pausar")
def pausar_ficha(data: dict):
    """
    Pausa una ficha: cambia estado de CURSO a PAUSA con motivo
    Inserta registro histórico en kb_pausas
    """
    ficha = data.get("ficha")
    pa_tipo = data.get("pa_tipo")
    motivo = data.get("motivo")

    db = SessionLocal()

    try:
        # 1. Obtener datos actuales de la ficha
        ficha_actual = db.execute(text("""
            SELECT
                pa_tipo,
                ficha,
                id_area,
                id_operacion_actual,
                id_operario_actual,
                nombre_operario_actual
            FROM dbo.kb_ficha_estado
            WHERE ficha = :ficha
              AND pa_tipo = :pa_tipo
              AND activo = 1
        """), {
            "ficha": ficha,
            "pa_tipo": pa_tipo
        }).mappings().first()

        # 2. Actualizar estado en kb_ficha_estado
        db.execute(text("""
            UPDATE dbo.kb_ficha_estado
            SET estado_actual = 'PAUSA',
                motivo_pausa = :motivo,
                fecha_pausa = GETDATE(),
                fecha_ultima_accion = GETDATE()
            WHERE ficha = :ficha
            AND pa_tipo = :pa_tipo
            AND activo = 1
        """), {
            "ficha": ficha,
            "pa_tipo": pa_tipo,
            "motivo": motivo
        })

        # 3. Insertar registro de pausa activa en kb_pausas
        if ficha_actual:
            db.execute(text("""
                INSERT INTO dbo.kb_pausas
                (
                    pa_tipo,
                    ficha,
                    id_area,
                    id_operacion,
                    id_operario,
                    nombre_operario,
                    motivo_pausa,
                    fecha_inicio_pausa,
                    estatus_pausa,
                    created_at
                )
                VALUES
                (
                    :pa_tipo,
                    :ficha,
                    :id_area,
                    :id_operacion,
                    :id_operario,
                    :nombre_operario,
                    :motivo_pausa,
                    GETDATE(),
                    'ACTIVA',
                    GETDATE()
                )
            """), {
                "pa_tipo": ficha_actual["pa_tipo"],
                "ficha": ficha_actual["ficha"],
                "id_area": ficha_actual["id_area"],
                "id_operacion": ficha_actual["id_operacion_actual"],
                "id_operario": ficha_actual["id_operario_actual"],
                "nombre_operario": ficha_actual["nombre_operario_actual"],
                "motivo_pausa": motivo
            })

        db.commit()
        return {"ok": True}

    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}

    finally:
        db.close()


@router.post("/ficha/reanudar")
def reanudar_ficha(data: dict):
    """
    Reanuda una ficha: cambia estado de PAUSA a CURSO
    Limpia motivo_pausa y fecha_pausa
    Cierra la pausa activa en kb_pausas
    """
    ficha = data.get("ficha")
    pa_tipo = data.get("pa_tipo")

    db = SessionLocal()

    try:
        # 1. Actualizar estado en kb_ficha_estado
        db.execute(text("""
            UPDATE dbo.kb_ficha_estado
            SET estado_actual = 'CURSO',
                motivo_pausa = NULL,
                fecha_pausa = NULL,
                fecha_ultima_accion = GETDATE()
            WHERE ficha = :ficha
            AND pa_tipo = :pa_tipo
            AND activo = 1
        """), {
            "ficha": ficha,
            "pa_tipo": pa_tipo
        })

        # 2. Cerrar la última pausa activa en kb_pausas
        db.execute(text("""
            UPDATE dbo.kb_pausas
            SET fecha_fin_pausa = GETDATE(),
                estatus_pausa = 'CERRADA',
                updated_at = GETDATE()
            WHERE id_pausa = (
                SELECT MAX(id_pausa)
                FROM dbo.kb_pausas
                WHERE ficha = :ficha
                  AND pa_tipo = :pa_tipo
                  AND estatus_pausa = 'ACTIVA'
            )
        """), {
            "ficha": ficha,
            "pa_tipo": pa_tipo
        })

        db.commit()
        return {"ok": True}

    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}

    finally:
        db.close()


@router.get("/kanban/operacion-caracteristicas/{id_operacion}")
def obtener_caracteristicas_operacion(id_operacion: int):
    """
    Obtiene las características/máquinas disponibles para una operación
    """
    db = SessionLocal()

    try:
        data = db.execute(text("""
            SELECT
                id_operacion_caracteristica,
                clave_caracteristica,
                nombre_caracteristica,
                tipo_caracteristica,
                orden_visual
            FROM dbo.kb_operacion_caracteristicas
            WHERE id_operacion = :id_operacion
              AND activo = 1
            ORDER BY orden_visual, nombre_caracteristica
        """), {
            "id_operacion": id_operacion
        }).mappings().all()

        return [dict(row) for row in data]

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        db.close()