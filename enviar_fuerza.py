"""
Script de fuerza: Enviar TODOS los eventos pendientes sin anti-spam
"""
import logging
from sqlalchemy import text
from app.db import SessionLocal
from whatsapp_service import enviar_alerta_whatsapp

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

db = SessionLocal()

logger.info("🚀 FUERZA: Enviando todos los eventos pendientes\n")

# Obtener TODOS los eventos sin filtro de tiempo
query = text("""
    SELECT 
        id_alerta_evento,
        tipo_evento,
        nombre_area,
        mensaje
    FROM dbo.kb_alertas_eventos
    WHERE enviado_whatsapp = 0
    ORDER BY fecha_evento ASC
""")

eventos = db.execute(query).fetchall()

logger.info(f"📨 Total de eventos pendientes: {len(eventos)}\n")

exitosos = 0
fallidos = 0

for evento in eventos:
    id_evento = evento[0]
    tipo_evento = evento[1]
    nombre_area = evento[2]
    mensaje = evento[3]
    
    logger.info(f"📤 Evento {id_evento}: {tipo_evento} - {nombre_area}")
    logger.info(f"   Mensaje: {mensaje}")
    
    if enviar_alerta_whatsapp(mensaje):
        # Marcar como enviado
        db.execute(text(f"""
            UPDATE dbo.kb_alertas_eventos
            SET enviado_whatsapp = 1,
                fecha_envio_whatsapp = GETDATE()
            WHERE id_alerta_evento = {id_evento}
        """))
        db.commit()
        exitosos += 1
        logger.info(f"   ✅ Enviado\n")
    else:
        fallidos += 1
        logger.info(f"   ❌ Falló\n")

logger.info(f"\n{'='*60}")
logger.info(f"✅ Exitosos: {exitosos}")
logger.info(f"❌ Fallidos: {fallidos}")
logger.info(f"{'='*60}")

db.close()
