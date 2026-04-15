"""
Servicio para registrar eventos de alerta en kb_alertas_eventos

Tipos de evento:
- LLEGADA_FICHAS: Cuando llegan nuevas fichas a un área
- INICIO_FICHA: Cuando un operario inicia una ficha
- FIN_OPERACION: Cuando un operario termina una operación
- LOTE_TERMINADO: Cuando se completa el lote del día en Acabado
"""

import os
from datetime import datetime

from sqlalchemy import text
from app.db import SessionLocal
from app.services.whatsapp_client import WhatsAppClient

wa_client = WhatsAppClient()

EVENTOS_WA = {
    "LLEGADA_FICHAS": "Llegada de fichas",
    "INICIO_FICHA": "Inicio de ficha",
    "FIN_OPERACION": "Fin de operación",
    "LOTE_TERMINADO": "Lote terminado",
}


def debe_enviar_whatsapp(tipo_evento: str) -> bool:
    return tipo_evento in {"LLEGADA_FICHAS", "INICIO_FICHA", "FIN_OPERACION", "LOTE_TERMINADO"}


def enviar_alerta_whatsapp_desde_evento(
    tipo_evento: str,
    nombre_area: str,
    nombre_operario: str = None,
    ficha: str = None,
    pa_tipo: str = None,
    pzas: float = None
):
    telefono = "524777301376"
    evento_wa = EVENTOS_WA.get(tipo_evento, tipo_evento)
    operario = nombre_operario or "Sin asignar"

    # DEBUG: Verificar qué está llegando
    print(f"[WhatsApp DEBUG] pa_tipo={pa_tipo}, pzas={pzas}, ficha={ficha}")
    
    # Concatenar en el campo ficha: ficha + pa_tipo + fecha/hora + pzas
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    ficha_completa = ""
    
    if ficha:
        ficha_completa = f"{ficha}"
    
    if pa_tipo:
        ficha_completa += f" {pa_tipo}" if ficha_completa else f"{pa_tipo}"
    
    ficha_completa += f" {fecha_actual}"
    
    if pzas is not None:
        ficha_completa += f" {pzas} pzas"

    print(f"[WhatsApp DEBUG] ficha_completa={ficha_completa}")

    return wa_client.send_kanban_alert(
        telefono=telefono,
        evento=evento_wa,
        area=nombre_area,
        fecha=ficha_completa.strip() if ficha_completa.strip() else None,  # MISMO QUE ficha
        operario=operario,
        ficha=ficha_completa.strip() if ficha_completa.strip() else None
    )


def registrar_evento_alerta(
    tipo_evento: str,
    id_area: int,
    nombre_area: str,
    mensaje: str,
    pa_tipo: str = None,
    ficha: str = None,
    id_operacion: int = None,
    nombre_operacion: str = None,
    id_operario: str = None,
    nombre_operario: str = None,
    pzas: float = None,
    db=None
):
    """
    Registra un evento de alerta en kb_alertas_eventos.

    Args:
        tipo_evento: LLEGADA_FICHAS, INICIO_FICHA, FIN_OPERACION, LOTE_TERMINADO
        id_area: ID del área
        nombre_area: Nombre del área
        mensaje: Mensaje descriptivo del evento
        pa_tipo: Tipo de partida (opcional)
        ficha: Número de ficha (opcional)
        id_operacion: ID de operación (opcional)
        nombre_operacion: Nombre de la operación (opcional)
        id_operario: ID del operario (opcional)
        nombre_operario: Nombre del operario (opcional)
        pzas: Cantidad de piezas (opcional)
        db: Sesión DB (si no se proporciona, crea una nueva)
    """

    debe_cerrar_db = False

    try:
        print(f"\n[EVENTO] Registrando evento: {tipo_evento} - Area: {nombre_area} - Operario: {nombre_operario}")
        
        if db is None:
            db = SessionLocal()
            debe_cerrar_db = True

        db.execute(text("""
            INSERT INTO dbo.kb_alertas_eventos
            (
                tipo_evento,
                id_area,
                nombre_area,
                pa_tipo,
                ficha,
                id_operacion,
                nombre_operacion,
                id_operario,
                nombre_operario,
                mensaje,
                fecha_evento,
                created_at
            )
            VALUES
            (
                :tipo_evento,
                :id_area,
                :nombre_area,
                :pa_tipo,
                :ficha,
                :id_operacion,
                :nombre_operacion,
                :id_operario,
                :nombre_operario,
                :mensaje,
                GETDATE(),
                GETDATE()
            )
        """), {
            "tipo_evento": tipo_evento,
            "id_area": id_area,
            "nombre_area": nombre_area,
            "pa_tipo": pa_tipo,
            "ficha": ficha,
            "id_operacion": id_operacion,
            "nombre_operacion": nombre_operacion,
            "id_operario": id_operario,
            "nombre_operario": nombre_operario,
            "mensaje": mensaje
        })

        if debe_cerrar_db:
            db.commit()

        print(f"[EVENTO] ✓ Registrado en BD correctamente")

        # Envío a WhatsApp vía gateway (no rompe el flujo si falla)
        print(f"[EVENTO] Verificando si debe enviar WhatsApp... tipo_evento={tipo_evento}")
        try:
            if debe_enviar_whatsapp(tipo_evento):
                print(f"[EVENTO] ✓ SÍ debe enviar - enviando a WhatsApp...")
                resultado_wa = enviar_alerta_whatsapp_desde_evento(
                    tipo_evento=tipo_evento,
                    nombre_area=nombre_area,
                    nombre_operario=nombre_operario,
                    ficha=ficha,
                    pa_tipo=pa_tipo,
                    pzas=pzas
                )
                print(f"[WhatsApp] Resultado: {resultado_wa}")
            else:
                print(f"[EVENTO] ✗ NO envía WhatsApp (tipo_evento={tipo_evento} no está en la lista)")
        except Exception as e:
            print(f"[WhatsApp] Error no bloqueante: {str(e)}")

        return {"status": "ok", "mensaje": "Evento registrado"}

    except Exception as e:
        if debe_cerrar_db:
            db.rollback()
        print(f"[EVENTO] ✗ Error registrando evento: {str(e)}")
        return {"status": "error", "mensaje": str(e)}

    finally:
        if debe_cerrar_db:
            db.close()
