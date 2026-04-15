"""
Envío de Alertas del Kanban por WhatsApp - Usando requests directo (API de Facebook)
Lee de kb_alertas_eventos y envía notificaciones

Este código usa el método que ya funciona en tu otro app.
"""

import pyodbc
import requests
import logging
import time
from datetime import datetime

# === CONFIGURACIÓN WHATSAPP ===
TOKEN = 'EAAQ0rUeubZAEBOzevYUHfYrZBl2PRjapYLE10M5XTtvNeautHG0HLar9wnSkntZCVZAZCVX6JBBcgv2RL1VuOjXqh3uHTyxH1zAuHjryR5gajErZBBwtGkElZCluAtU2FFNk70dZAm9xbGTDSLBLbZAxu56visLQbUaiIsBM3m8nchyHWedFes8WIWLQPovNgLkV4vgZDZD'
NUMEROS_DESTINO = ['524777301376', '524767374345']  # Ambos números
URL = 'https://graph.facebook.com/v22.0/306630785862053/messages'
MODO_DEBUG = False

# === CONFIGURACIÓN BD KANBAN ===
# (Usa la misma que en app/db.py)
BD_KANBAN = {
    "DRIVER": "ODBC Driver 17 for SQL Server",
    "SERVER": "192.168.39.203",
    "DATABASE": "dbProduccion",
    "UID": "wyny",
    "PWD": "wyny"
}
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("Alertas Kanban por WhatsApp - Usando requests directo")
print("="*70 + "\n")

# === CONEXIÓN A BD KANBAN ===
try:
    logger.info("[*] Conectando a BD Kanban...")
    conn_str = (
        f"DRIVER={BD_KANBAN['DRIVER']};"
        f"SERVER={BD_KANBAN['SERVER']};"
        f"DATABASE={BD_KANBAN['DATABASE']};"
        f"UID={BD_KANBAN['UID']};"
        f"PWD={BD_KANBAN['PWD']}"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    logger.info("[OK] Conectado a BD Kanban\n")
except Exception as e:
    logger.error(f"[ERROR] No se pudo conectar: {e}")
    exit(1)

# === CONSULTA DE ALERTAS PENDIENTES ===
try:
    query = """
        SELECT 
            id_alerta_evento,
            tipo_evento,
            nombre_area,
            pa_tipo,
            ficha,
            nombre_operacion,
            nombre_operario,
            mensaje,
            fecha_evento
        FROM dbo.kb_alertas_eventos
        WHERE enviado_whatsapp = 0
            AND DATEDIFF(SECOND, fecha_evento, GETDATE()) > 5
        ORDER BY fecha_evento ASC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    logger.info(f"[Alertas pendientes: {len(rows)}]\n")
    
    if len(rows) == 0:
        logger.info("[OK] No hay alertas para enviar")
        conn.close()
        exit(0)
    
except Exception as e:
    logger.error(f"[ERROR] Consulta SQL: {e}")
    conn.close()
    exit(1)

# === HEADERS PARA REQUEST ===
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PROCESAR Y ENVIAR ===
exitosos = 0
fallidos = 0

for idx, row in enumerate(rows, 1):
    id_alerta = row[0]
    tipo_evento = row[1]
    nombre_area = row[2]
    pa_tipo = row[3]
    ficha = row[4]
    nombre_operacion = row[5]
    nombre_operario = row[6]
    mensaje = row[7]
    fecha_evento = row[8]
    
    try:
        logger.info(f"{idx}. [ENVIANDO] ID {id_alerta}: {tipo_evento}")
        logger.info(f"   Area: {nombre_area} | Ficha: {ficha}")
        logger.info(f"   Mensaje: {mensaje[:50]}...\n" if len(mensaje) > 50 else f"   Mensaje: {mensaje}\n")
        
        # Enviar a AMBOS números
        for num_idx, numero in enumerate(NUMEROS_DESTINO):
            try:
                # Estructura del payload usando TEMPLATE (alertas_kanban - ya aprobada en FB Business)
                data = {
                    "messaging_product": "whatsapp",
                    "to": numero,
                    "type": "template",
                    "template": {
                        "name": "alertas_kanban",
                        "language": {
                            "code": "es_MX"
                        },
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": str(tipo_evento)},
                                    {"type": "text", "text": str(nombre_area)},
                                    {"type": "text", "text": str(ficha)},
                                    {"type": "text", "text": str(nombre_operario)}
                                ]
                            }
                        ]
                    }
                }
                
                if MODO_DEBUG:
                    logger.info(f"[DEBUG] Payload:")
                    import json
                    logger.info(json.dumps(data, indent=2))
                    exitosos += 1
                    continue
                
                # ENVÍO REAL
                response = requests.post(URL, headers=headers, json=data, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"   [OK] Status 200 → {numero}")
                    
                    # Marcar como enviado en BD (solo una vez, después de enviar a ambos)
                    if num_idx == len(NUMEROS_DESTINO) - 1:
                        try:
                            update_query = f"""
                                UPDATE dbo.kb_alertas_eventos
                                SET enviado_whatsapp = 1,
                                    fecha_envio_whatsapp = GETDATE()
                                WHERE id_alerta_evento = {id_alerta}
                            """
                            cursor.execute(update_query)
                            conn.commit()
                            logger.info(f"   [OK] Marcado en BD\n")
                            exitosos += 1
                        except Exception as e:
                            logger.warning(f"   [AVISO] No se marcó en BD: {e}\n")
                            exitosos += 1
                    
                    # Delay entre números (no entre mensajes diferentes)
                    if num_idx < len(NUMEROS_DESTINO) - 1:
                        time.sleep(5)
                        
                else:
                    logger.info(f"   [FALLO] Status {response.status_code} → {numero}")
                    logger.info(f"   Respuesta: {response.text}\n")
                    if num_idx == len(NUMEROS_DESTINO) - 1:
                        fallidos += 1
                        
            except Exception as e:
                logger.error(f"   [ERROR] En número {numero}: {e}\n")
                if num_idx == len(NUMEROS_DESTINO) - 1:
                    fallidos += 1
        
        # Delay entre eventos diferentes (10 seg)
        if idx < len(rows):
            time.sleep(10)
            
    except Exception as e:
        logger.error(f"   [ERROR] {e}\n")
        fallidos += 1

conn.close()

# === RESUMEN ===
print("="*70)
logger.info("RESUMEN:")
logger.info(f"   Total procesadas: {len(rows)}")
logger.info(f"   [OK] Exitosas: {exitosos}")
logger.info(f"   [FALLO] Fallidas: {fallidos}")
print("="*70)
logger.info("Script finalizado.\n")
