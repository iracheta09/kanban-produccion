"""
CRON: Envío automático de alertas a WhatsApp
Ejecutar cada 1 minuto desde Windows Task Scheduler

Lógica:
1. Lee eventos pendientes (enviado_whatsapp = 0)
2. Envía cada uno a la API de WhatsApp
3. Actualiza estado en BD (enviado_whatsapp = 1 o error_envio)
4. Implementa reintentos si falla
"""

import requests
import logging
from datetime import datetime
from sqlalchemy import text
from app.db import SessionLocal
from config_whatsapp import (
    WHATSAPP_API_TOKEN,
    WHATSAPP_PHONE_ID,
    NUMERO_DESTINO,
    WHATSAPP_API_URL,
    MAX_INTENTOS,
    SEGUNDOS_ENTRE_REINTENTOS,
    SEGUNDOS_MINIMOS_PARA_ENVIO
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validar_config():
    """Valida que las credenciales estén configuradas"""
    if "TU_TOKEN" in WHATSAPP_API_TOKEN or "TU_PHONE_ID" in WHATSAPP_PHONE_ID:
        logger.error("❌ CREDENCIALES DE WHATSAPP NO CONFIGURADAS")
        logger.error("   Edita config_whatsapp.py e ingresa tus datos reales")
        return False
    return True


def enviar_whatsapp(mensaje, numero=None):
    """
    Envía un mensaje a WhatsApp
    
    Args:
        mensaje: Texto del mensaje
        numero: Número destino (opcional, usa el de config si no se proporciona)
    
    Returns:
        tuple: (éxito: bool, status_code: int, respuesta: str)
    """
    
    if numero is None:
        numero = NUMERO_DESTINO
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": mensaje
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, response.status_code, response.text
        else:
            return False, response.status_code, response.text
            
    except requests.exceptions.Timeout:
        return False, 0, "Timeout en conexión a WhatsApp API"
    except requests.exceptions.ConnectionError:
        return False, 0, "Error de conexión a WhatsApp API"
    except Exception as e:
        return False, 0, str(e)


def procesar_eventos_pendientes():
    """
    Procesa y envía todos los eventos pendientes a WhatsApp
    """
    
    db = SessionLocal()
    eventos_procesados = 0
    eventos_exitosos = 0
    eventos_fallidos = 0
    
    try:
        # Obtener eventos pendientes (máximo 20 por ejecución)
        # Con filtro para evitar spam (mín 5 segundos desde generación)
        eventos = db.execute(text("""
            SELECT TOP 20
                id_alerta_evento,
                tipo_evento,
                nombre_area,
                mensaje,
                fecha_evento,
                intentos_envio
            FROM dbo.kb_alertas_eventos
            WHERE enviado_whatsapp = 0
                AND DATEDIFF(SECOND, fecha_evento, GETDATE()) > :segundos_minimos
                AND ISNULL(intentos_envio, 0) < :max_intentos
            ORDER BY fecha_evento ASC
        """), {
            "segundos_minimos": SEGUNDOS_MINIMOS_PARA_ENVIO,
            "max_intentos": MAX_INTENTOS
        }).mappings().all()
        
        logger.info(f"📨 Eventos pendientes: {len(eventos)}")
        
        if not eventos:
            logger.info("✅ Sin eventos pendientes de enviar")
            return
        
        for evento in eventos:
            evento_id = evento["id_alerta_evento"]
            mensaje = evento["mensaje"]
            intentos = evento["intentos_envio"] or 0
            
            logger.info(f"\n📤 Procesando evento {evento_id}...")
            
            # Intentar envío (con reintentos)
            exito = False
            error_msg = None
            
            for intento in range(1, MAX_INTENTOS + 1):
                
                exito, status_code, respuesta = enviar_whatsapp(mensaje)
                
                if exito:
                    logger.info(f"   ✅ Intento {intento}/{MAX_INTENTOS}: OK (Status {status_code})")
                    eventos_exitosos += 1
                    
                    # Actualizar BD: marcado como enviado
                    db.execute(text("""
                        UPDATE dbo.kb_alertas_eventos
                        SET enviado_whatsapp = 1,
                            fecha_envio_whatsapp = GETDATE(),
                            intentos_envio = :intentos,
                            error_envio = NULL
                        WHERE id_alerta_evento = :id
                    """), {
                        "id": evento_id,
                        "intentos": intento
                    })
                    db.commit()
                    break
                    
                else:
                    error_msg = respuesta[:200] if respuesta else "Error desconocido"
                    logger.warning(f"   ❌ Intento {intento}/{MAX_INTENTOS}: FALLÓ")
                    logger.warning(f"      Error: {error_msg}")
                    
                    # Si hay más intentos, esperar
                    if intento < MAX_INTENTOS:
                        logger.info(f"   ⏳ Esperando {SEGUNDOS_ENTRE_REINTENTOS}s antes del siguiente intento...")
                        import time
                        time.sleep(SEGUNDOS_ENTRE_REINTENTOS)
            
            if not exito:
                eventos_fallidos += 1
                # Guardar error y incrementar contador de intentos
                db.execute(text("""
                    UPDATE dbo.kb_alertas_eventos
                    SET error_envio = :error,
                        intentos_envio = :intentos
                    WHERE id_alerta_evento = :id
                """), {
                    "id": evento_id,
                    "error": error_msg,
                    "intentos": intentos + 1
                })
                db.commit()
            
            eventos_procesados += 1
        
        # Resumen
        logger.info(f"\n{'='*50}")
        logger.info(f"📊 RESUMEN:")
        logger.info(f"   Eventos procesados: {eventos_procesados}")
        logger.info(f"   ✅ Exitosos: {eventos_exitosos}")
        logger.info(f"   ❌ Fallidos: {eventos_fallidos}")
        logger.info(f"{'='*50}\n")
        
    except Exception as e:
        logger.error(f"❌ Error en procesar_eventos_pendientes: {str(e)}")
        
    finally:
        db.close()


def main():
    """Punto de entrada"""
    
    logger.info("🚀 Iniciando cron_enviar_alertas.py")
    logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not validar_config():
        logger.error("Abortando: configuración incompleta")
        return
    
    procesar_eventos_pendientes()
    
    logger.info("✅ Cron finalizado")


if __name__ == "__main__":
    main()
