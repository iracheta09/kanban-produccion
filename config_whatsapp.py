"""
Configuración de WhatsApp
Modifica estos valores con tus credenciales reales
"""

# Credenciales reales configuradas
WHATSAPP_API_TOKEN = "EAAQ0rUeubZAEBOzevYUHfYrZBl2PRjapYLE10M5XTtvNeautHG0HLar9wnSkntZCVZAZCVX6JBBcgv2RL1VuOjXqh3uHTyxH1zAuHjryR5gajErZBBwtGkElZCluAtU2FFNk70dZAm9xbGTDSLBLbZAxu56visLQbUaiIsBM3m8nchyHWedFes8WIWLQPovNgLkV4vgZDZD"
WHATSAPP_PHONE_ID = "306630785862053"  # ID del número en WhatsApp
NUMERO_DESTINO = "5214777301376"  # +52 1 477 730 1376 (formato correcto con 1)

# URL base de la API
WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"

# Configuración de reintentos
MAX_INTENTOS = 3
SEGUNDOS_ENTRE_REINTENTOS = 5

# Variación mínima de segundos entre generación del evento e envío
# (evita spam si múltiples eventos se disparan en cascada)
SEGUNDOS_MINIMOS_PARA_ENVIO = 5
