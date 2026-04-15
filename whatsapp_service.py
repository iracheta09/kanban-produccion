"""
Servicio para enviar mensajes WhatsApp con Twilio
"""

import logging
from twilio.rest import Client
from config_twilio import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_WHATSAPP_NUMBER,
    NUMEROS_DESTINO,
    MAX_REINTENTOS,
    SEGUNDOS_ENTRE_REINTENTOS,
)
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar cliente de Twilio
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def enviar_alerta_whatsapp(mensaje, numero_destino=None):
    """
    Envía una alerta por WhatsApp usando Twilio
    
    Args:
        mensaje (str): Contenido del mensaje
        numero_destino (str, opcional): Número específico. Si no se proporciona, envía a todos
    
    Returns:
        bool: True si se envió exitosamente, False si falló todas las pruebas
    """
    
    numeros = [numero_destino] if numero_destino else NUMEROS_DESTINO
    
    resultados = []
    
    for numero in numeros:
        logger.info(f"📤 Enviando mensaje a {numero}...")
        
        exito = False
        for intento in range(1, MAX_REINTENTOS + 1):
            try:
                message = client.messages.create(
                    body=mensaje,
                    from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
                    to=f"whatsapp:{numero}"
                )
                
                logger.info(f"   ✅ Intento {intento}/{MAX_REINTENTOS}: OK")
                logger.info(f"      Message SID: {message.sid}")
                logger.info(f"      Estado: {message.status}")
                
                exito = True
                break
                
            except Exception as e:
                logger.warning(f"   ❌ Intento {intento}/{MAX_REINTENTOS}: FALLÓ")
                logger.warning(f"      Error: {str(e)}")
                
                if intento < MAX_REINTENTOS:
                    logger.info(f"   ⏳ Esperando {SEGUNDOS_ENTRE_REINTENTOS}s...")
                    time.sleep(SEGUNDOS_ENTRE_REINTENTOS)
        
        resultados.append(exito)
    
    return all(resultados)


def enviar_alerta_batch(mensajes_data):
    """
    Envía múltiples alertas
    
    Args:
        mensajes_data (list): Lista de dicts con 'mensaje' y opcionalmente 'numero'
    
    Returns:
        tuple: (exitosos, fallidos)
    """
    
    exitosos = 0
    fallidos = 0
    
    for item in mensajes_data:
        mensaje = item.get('mensaje')
        numero = item.get('numero')
        
        if enviar_alerta_whatsapp(mensaje, numero):
            exitosos += 1
        else:
            fallidos += 1
    
    return exitosos, fallidos
