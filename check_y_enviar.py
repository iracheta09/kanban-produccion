"""
Verificar y enviar eventos directamente
"""
from sqlalchemy import text
from app.db import SessionLocal
from whatsapp_service import enviar_alerta_whatsapp

db = SessionLocal()

# Ver pendientes
pendientes = db.execute(text("SELECT COUNT(*) FROM kb_alertas_eventos WHERE enviado_whatsapp=0")).fetchone()[0]
print(f"📊 Eventos pendientes: {pendientes}\n")

# Si hay pendientes, enviar
if pendientes > 0:
    print("🚀 Ejecutando envío...\n")
    import subprocess
    subprocess.run([r'C:\kanban_produccion\.venv\Scripts\python.exe', 
                    r'C:\kanban_produccion\cron_whatsapp_twilio.py'])
else:
    print("✅ No hay eventos pendientes")

db.close()
