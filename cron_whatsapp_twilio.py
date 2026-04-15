"""
Cron para enviar alertas de Kanban por WhatsApp con Twilio
Ejecutar cada minuto con Task Scheduler
"""

import logging
from datetime import datetime
from sqlalchemy import text
from app.db import SessionLocal
from whatsapp_service import enviar_alerta_whatsapp
from config_twilio import SEGUNDOS_MINIMOS_PARA_ENVIO

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def enviar_alertas_pendientes():
    """
    Lee eventos pendientes de la BD y envía por WhatsApp
    """
    
    logger.info("🚀 Iniciando cron_whatsapp_twilio.py")
    logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    db = SessionLocal()
    
    try:
        # Obtener eventos pendientes (no enviados y con edad mínima)
        query = text(f"""
            SELECT 
                id_alerta_evento,
                tipo_evento,
                nombre_area,
                mensaje,
                intentos_envio
            FROM dbo.kb_alertas_eventos
            WHERE enviado_whatsapp = 0
                AND DATEDIFF(SECOND, fecha_evento, GETDATE()) > {SEGUNDOS_MINIMOS_PARA_ENVIO}
                AND intentos_envio < 3
            ORDER BY fecha_evento ASC
        """)
        
        eventos = db.execute(query).fetchall()
        
        logger.info(f"📨 Eventos pendientes: {len(eventos)}")
        
        if not eventos:
            logger.info("✅ No hay eventos para enviar")
            db.close()
            return
        
        # Procesar cada evento
        exitosos = 0
        fallidos = 0
        
        for evento in eventos:
            id_evento = evento[0]
            tipo_evento = evento[1]
            nombre_area = evento[2]
            mensaje = evento[3]
            intentos = evento[4]
            
            logger.info(f"\n📤 Procesando evento {id_evento}...")
            logger.info(f"   Tipo: {tipo_evento}")
            logger.info(f"   Área: {nombre_area}")
            logger.info(f"   Intentos previos: {intentos}")
            
            # Intentar enviar
            if enviar_alerta_whatsapp(mensaje):
                # Marcar como enviado
                db.execute(text(f"""
                    UPDATE dbo.kb_alertas_eventos
                    SET enviado_whatsapp = 1,
                        fecha_envio_whatsapp = GETDATE(),
                        intentos_envio = intentos_envio + 1
                    WHERE id_alerta_evento = {id_evento}
                """))
                db.commit()
                exitosos += 1
            else:
                # Incrementar intentos
                db.execute(text(f"""
                    UPDATE dbo.kb_alertas_eventos
                    SET intentos_envio = intentos_envio + 1
                    WHERE id_alerta_evento = {id_evento}
                """))
                db.commit()
                fallidos += 1
        
        # Resumen
        logger.info(f"\n{'='*50}")
        logger.info(f"📊 RESUMEN:")
        logger.info(f"   Eventos procesados: {len(eventos)}")
        logger.info(f"   ✅ Exitosos: {exitosos}")
        logger.info(f"   ❌ Fallidos: {fallidos}")
        logger.info(f"{'='*50}")
        logger.info("✅ Cron finalizado")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
    
    finally:
        db.close()


if __name__ == "__main__":
    enviar_alertas_pendientes()
