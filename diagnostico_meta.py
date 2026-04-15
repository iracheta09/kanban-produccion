import requests
import json

TOKEN = 'EAAQ0rUeubZAEBOzevYUHfYrZBl2PRjapYLE10M5XTtvNeautHG0HLar9wnSkntZCVZAZCVX6JBBcgv2RL1VuOjXqh3uHTyxH1zAuHjryR5gajErZBBwtGkElZCluAtU2FFNk70dZAm9xbGTDSLBLbZAxu56visLQbUaiIsBM3m8nchyHWedFes8WIWLQPovNgLkV4vgZDZD'

headers = {'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'}
data = {
    'messaging_product': 'whatsapp',
    'to': '524767374345',
    'type': 'template',
    'template': {
        'name': 'alertas_kanban',
        'language': {'code': 'es_MX'},
        'components': [{'type': 'body', 'parameters': [
            {'type': 'text', 'text': 'PRUEBA'},
            {'type': 'text', 'text': 'AREA TEST'},
            {'type': 'text', 'text': 'FICHA-999'},
            {'type': 'text', 'text': 'OPERARIO TEST'}
        ]}]
    }
}

URL = 'https://graph.facebook.com/v22.0/306630785862053/messages'
response = requests.post(URL, headers=headers, json=data, timeout=10)

print("="*80)
print("STATUS CODE:", response.status_code)
print("="*80)
print("\nHEADERS RESPUESTA:")
print(json.dumps(dict(response.headers), indent=2, ensure_ascii=False))
print("\n" + "="*80)
print("JSON COMPLETO RESPUESTA:")
print("="*80)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
print("\n" + "="*80)
print("TEXTO RAW:")
print("="*80)
print(response.text)
