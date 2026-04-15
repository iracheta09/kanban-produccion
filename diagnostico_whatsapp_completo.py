"""
Validación completa de configuración de WhatsApp
"""

import requests
import json
from config_whatsapp import WHATSAPP_API_TOKEN, WHATSAPP_PHONE_ID, NUMERO_DESTINO, WHATSAPP_API_URL

print("\n" + "="*70)
print("🔍 DIAGNÓSTICO COMPLETO DE WHATSAPP")
print("="*70)

# 1. Validar token
print("\n1️⃣ VALIDANDO TOKEN")
print("─" * 70)

url_validate = f"{WHATSAPP_API_URL}/me"
headers = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"}

try:
    resp = requests.get(url_validate, headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Token válido")
        print(f"   ID: {data.get('id')}")
        print(f"   Nombre: {data.get('name')}")
    else:
        print(f"❌ Token INVÁLIDO o EXPIRADO")
        print(f"   Status: {resp.status_code}")
        print(f"   Error: {resp.text}")
except Exception as e:
    print(f"❌ Error conectando: {e}")

# 2. Validar Phone ID
print("\n2️⃣ VALIDANDO PHONE ID")
print("─" * 70)

url_phone = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}"
try:
    resp = requests.get(url_phone, headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Phone ID válido")
        print(f"   ID: {data.get('id')}")
        print(f"   Número: {data.get('display_phone_number')}")
        print(f"   Verificado: {data.get('verified_name')}")
        
        phone_num = data.get('display_phone_number')
        if phone_num:
            print(f"\n   ⚠️ El número registrado es: {phone_num}")
            print(f"   Tu número configurado es: {NUMERO_DESTINO}")
            if phone_num.replace('+', '') != NUMERO_DESTINO:
                print(f"   ❌ NO COINCIDEN - Este podría ser el problema!")
    else:
        print(f"❌ Phone ID INVÁLIDO")
        print(f"   Status: {resp.status_code}")
        print(f"   Error: {resp.text}")
except Exception as e:
    print(f"❌ Error conectando: {e}")

# 3. Probar envío simple
print("\n3️⃣ PROBANDO ENVÍO")
print("─" * 70)

url_send = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
data = {
    "messaging_product": "whatsapp",
    "to": NUMERO_DESTINO,
    "type": "text",
    "text": {"body": "Test"}
}

try:
    resp = requests.post(url_send, json=data, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        resp_data = resp.json()
        msg_id = resp_data.get('messages', [{}])[0].get('id')
        print(f"✅ Mensaje enviado")
        print(f"   Message ID: {msg_id}")
    else:
        print(f"❌ Error en envío")
        error_data = resp.json()
        if 'error' in error_data:
            err = error_data['error']
            print(f"   Código: {err.get('code')}")
            print(f"   Tipo: {err.get('type')}")
            print(f"   Mensaje: {err.get('message')}")
            
            if "destination" in err.get('message', '').lower():
                print(f"\n   ⚠️ El número de destino no es válido o no está verificado")
            if "permission" in err.get('message', '').lower():
                print(f"\n   ⚠️ Problema de permisos - verifica credenciales")
        
        print(f"\n   Respuesta completa:")
        print(f"   {resp.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*70)
print("📋 RESUMEN DE CONFIGURACIÓN")
print("="*70)
print(f"Token: {WHATSAPP_API_TOKEN[:30]}...")
print(f"Phone ID: {WHATSAPP_PHONE_ID}")
print(f"Número destino: {NUMERO_DESTINO}")
print(f"API URL: {WHATSAPP_API_URL}")
print("="*70 + "\n")
