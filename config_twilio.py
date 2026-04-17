"""
Configuración de Twilio para WhatsApp
"""

# Credenciales de Twilio (Live)
TWILIO_ACCOUNT_SID = "AC................"
TWILIO_AUTH_TOKEN = "9457f520ce..................."
TWILIO_WHATSAPP_NUMBER = "+1415----"  # Número sandbox para WhatsApp

# Números destino (los que recibirán alertas)
# Puedes agregar múltiples números aquí
NUMEROS_DESTINO = [
    "+5214777301376",  # Tu personal (Cesar)
]

# Configuración de reintentos
MAX_REINTENTOS = 3
SEGUNDOS_ENTRE_REINTENTOS = 5

# Tiempo mínimo entre eventos (anti-spam)
SEGUNDOS_MINIMOS_PARA_ENVIO = 5
