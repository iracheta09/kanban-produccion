"""
WhatsApp Simple - Envía mensajes de prueba directamente
Sin base de datos, sin complejidad. Solo envía.
"""

import requests
import json
from datetime import datetime

# Credenciales (confirmadas como válidas)
PHONE_ID = "306630785862053"
TOKEN = "EAAQ0rUeubZAEBOzevYUHfYrZBl2PRjapYLE10M5XTtvNeautHG0HLar9wnSkntZCVZAZCVX6JBBcgv2RL1VuOjXqh3uHTyxH1zAuHjryR5gajErZBBwtGkElZCluAtU2FFNk70dZAm9xbGTDSLBLbZAxu56visLQbUaiIsBM3m8nchyHWedFes8WIWLQPovNgLkV4vgZDZD"

NUMERO_EMISOR = "52 477 852 0266"  # Empresa
NUMERO_DESTINO = "524777301376"    # Tu personal


def enviar_mensaje(mensaje):
    """
    Envía un mensaje WhatsApp a NUMERO_DESTINO
    """
    
    url = f"https://graph.facebook.com/v22.0/{PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": NUMERO_DESTINO,
        "type": "text",
        "text": {
            "body": mensaje
        }
    }
    
    print(f"\n{'='*70}")
    print(f"📤 ENVIANDO MENSAJE WHATSAPP")
    print(f"{'='*70}")
    print(f"⏰ Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📱 Emisor: {NUMERO_EMISOR}")
    print(f"📱 Destino: {NUMERO_DESTINO}")
    print(f"💬 Mensaje: {mensaje}")
    print(f"{'='*70}\n")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"HTTP Status: {response.status_code}")
        
        respuesta = response.json()
        print(f"\nRespuesta JSON:")
        print(json.dumps(respuesta, indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            print(f"\n✅ ÉXITO: Mensaje enviado correctamente")
            print(f"   Message ID: {respuesta['messages'][0]['id']}")
            return True
        else:
            print(f"\n❌ ERROR: {respuesta.get('error', {}).get('message', 'Error desconocido')}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "🎯 WHATSAPP SIMPLE - Control Manual" + "\n")
    
    # Opción 1: Enviar mensaje de prueba directo
    print("Opciones:")
    print("1. Enviar mensaje de prueba")
    print("2. Enviar mensaje personalizado")
    print("3. Salir")
    
    opcion = input("\nElige opción (1-3): ").strip()
    
    if opcion == "1":
        mensaje = "🧪 PRUEBA: Sistema WhatsApp funcionando correctamente"
        enviar_mensaje(mensaje)
        
    elif opcion == "2":
        mensaje = input("\nEscribe tu mensaje: ").strip()
        if mensaje:
            enviar_mensaje(mensaje)
        else:
            print("❌ Mensaje vacío")
            
    elif opcion == "3":
        print("Adiós")
    else:
        print("❌ Opción inválida")
