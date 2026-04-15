"""
Prueba de diferentes formatos de número
"""
import requests
import json
from config_whatsapp import WHATSAPP_API_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_API_URL

numeros_a_probar = [
    ("Con +", "+524777301376"),
    ("Con 1 después de 52", "5214777301376"),
]

for nombre, numero in numeros_a_probar:
    print(f"\n{'='*60}")
    print(f"🧪 Probando: {nombre}")
    print(f"   Número: {numero}")
    print(f"{'='*60}\n")
    
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
            "body": f"🧪 TEST: Formato con {nombre}"
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        try:
            respuesta = response.json()
            print(f"Response: {json.dumps(respuesta, indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                print(f"✅ ÉXITO: Mensaje enviado")
            else:
                print(f"❌ ERROR: {respuesta.get('error', {}).get('message', 'Desconocido')}")
        except:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
