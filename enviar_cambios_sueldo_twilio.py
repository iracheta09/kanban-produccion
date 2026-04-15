"""
Envío de cambios de sueldo por WhatsApp - Con Twilio
Lee de w_nomina_cambiosdo y envía notificaciones
"""

import pyodbc
import logging
from datetime import datetime
from whatsapp_service import enviar_alerta_whatsapp
from config_twilio import NUMEROS_DESTINO

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# === CONFIGURACIÓN BD ===
BD_CONFIG = {
    "DRIVER": "ODBC Driver 17 for SQL Server",
    "SERVER": "192.168.39.11",
    "DATABASE": "INTWYNY",
    "UID": "sa",
    "PWD": "Wyny001821"
}

print("\n" + "="*70)
print("ENVIO DE CAMBIOS DE SUELDO POR WHATSAPP (Twilio)")
print("="*70 + "\n")

# === CONEXION A SQL SERVER ===
try:
    logger.info("[*] Conectando a SQL Server...")
    conn_str = (
        f"DRIVER={BD_CONFIG['DRIVER']};"
        f"SERVER={BD_CONFIG['SERVER']};"
        f"DATABASE={BD_CONFIG['DATABASE']};"
        f"UID={BD_CONFIG['UID']};"
        f"PWD={BD_CONFIG['PWD']}"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    logger.info("[OK] Conectado a INTWYNY\n")
except Exception as e:
    logger.error(f"[ERROR] Error al conectar: {e}")
    exit(1)

# === CONSULTA REGISTROS PENDIENTES ===
try:
    query = """
        SELECT id, nombre, depto, sueldomensual, nuevosdo
        FROM dbo.w_nomina_cambiosdo
        WHERE estatus = 'Pendiente'
        ORDER BY id ASC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    logger.info(f"[Registros encontrados: {len(rows)}]\n")
    
    if len(rows) == 0:
        logger.info("✅ No hay cambios pendientes")
        conn.close()
        exit(0)
    
except Exception as e:
    logger.error(f"❌ Error en consulta SQL: {e}")
    conn.close()
    exit(1)

# === PROCESAR Y ENVIAR ===
exitosos = 0
fallidos = 0

for idx, row in enumerate(rows, 1):
    id_, nombre, depto, sueldo_old, sueldo_new = row
    
    try:
        # Formatear sueldos
        sueldo_old_fmt = f"${float(sueldo_old):,.0f}"
        sueldo_new_fmt = f"${float(sueldo_new):,.0f}"
        
        # Crear mensaje
        mensaje = f"""📋 CAMBIO DE SUELDO

👤 Empleado: {nombre.strip()}
🏢 Departamento: {depto.strip()}
💰 Sueldo Actual: {sueldo_old_fmt}
✨ Nuevo Sueldo: {sueldo_new_fmt}
🆔 ID: {id_}

Cambio pendiente de aprobación."""
        
        logger.info(f"{idx}. [ENVIANDO] ID {id_}: {nombre.strip()}")
        logger.info(f"   Sueldo: {sueldo_old_fmt} -> {sueldo_new_fmt}")
        
        # Enviar por WhatsApp (Twilio)
        if enviar_alerta_whatsapp(mensaje):
            # Marcar como enviado en BD
            try:
                update_query = f"""
                    UPDATE dbo.w_nomina_cambiosdo
                    SET estatus = 'Enviado',
                        fecha_envio = GETDATE()
                    WHERE id = {id_}
                """
                cursor.execute(update_query)
                conn.commit()
                logger.info(f"   [OK] Enviado y marcado en BD\n")
                exitosos += 1
            except Exception as e:
                logger.warning(f"   ⚠️ No se pudo marcar en BD: {e}\n")
                exitosos += 1  # Igual cuenta como exitoso el envío
        else:
            logger.warning(f"   [FALLO] Fallo en envío\n")
            fallidos += 1
    
    except Exception as e:
        logger.error(f"   ❌ Error procesando ID {id_}: {e}\n")
        fallidos += 1

conn.close()

# === RESUMEN ===
print("="*70)
logger.info(f"📊 RESUMEN:")
logger.info(f"   Total: {len(rows)}")
logger.info(f"   ✅ Exitosos: {exitosos}")
logger.info(f"   ❌ Fallidos: {fallidos}")
print("="*70)
logger.info("🏁 Script finalizado.\n")
