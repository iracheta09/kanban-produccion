import os
import requests


class WhatsAppClient:
    def __init__(self):
        self.base_url = os.getenv("WHATSAPP_GATEWAY_URL", "http://127.0.0.1:5000")
        self.api_key = os.getenv("WHATSAPP_GATEWAY_API_KEY", "kanban123")
        self.timeout = int(os.getenv("WHATSAPP_GATEWAY_TIMEOUT", "10"))

    def send_kanban_alert(self, telefono, evento, area, fecha, operario, ficha=None):
        # Simplificar payload: todo va en el campo ficha concatenado
        # ficha ya contiene: pa_numer + fecha/hora + piezas
        payload = {
            "telefono": telefono,
            "evento": evento,
            "area": area,
            "fecha": fecha,
            "operario": operario,
            "ficha": ficha if ficha else ""
        }

        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{self.base_url}/send-kanban",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            try:
                body = response.json()
            except Exception:
                body = {"raw": response.text}

            return {
                "ok": response.ok,
                "status_code": response.status_code,
                "data": body
            }

        except Exception as e:
            return {
                "ok": False,
                "error": str(e)
            }
