"""
WhatsApp con Twilio - Versión Simple
Envía mensajes WhatsApp a cualquier número sin verificación previa
"""

from twilio.rest import Client
from datetime import datetime

# Credenciales de Twilio
ACCOUNT_SID = "ACd2f2c4ea6849754261613134d6cb085a"
AUTH_TOKEN = "9457f520cee19e8abda8c2b7fcb242bd"
NUMERO_TWILIO = "+14155238886"  # Número sandbox de Twilio para WhatsApp

# Destino (tu número personal - sin espacios)
NUMERO_DESTINO = "+5214777301376"


def enviar_mensaje_twilio(mensaje):
    """
    Envía un mensaje WhatsApp usando Twilio
    """
    
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    
    print(f"\n{'='*70}")
    print(f"📤 ENVIANDO MENSAJE WHATSAPP CON TWILIO")
    print(f"{'='*70}")
    print(f"⏰ Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📱 Desde (Twilio): {NUMERO_TWILIO}")
    print(f"📱 Destino: {NUMERO_DESTINO}")
    print(f"💬 Mensaje: {mensaje}")
    print(f"{'='*70}\n")
    
    try:
        # Formato para WhatsApp: whatsapp:+numero
        message = client.messages.create(
            body=mensaje,
            from_=f"whatsapp:{NUMERO_TWILIO}",
            to=f"whatsapp:{NUMERO_DESTINO}"
        )
        
        print(f"✅ ÉXITO: Mensaje enviado correctamente")
        print(f"   Message SID: {message.sid}")
        print(f"   Estado: {message.status}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    # Prueba simple
    mensaje = "✅ Prueba desde Twilio: Sistema WhatsApp funcionando correctamente"
    enviar_mensaje_twilio(mensaje)
