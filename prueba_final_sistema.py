"""
PRUEBA FINAL: Entrada real en el Kanban → WhatsApp automático
Simula lo que pasará en producción
"""

from sqlalchemy import text
from app.db import SessionLocal
import time

print("\n" + "="*80)
print("🚀 PRUEBA FINAL DEL SISTEMA COMPLETO")
print("="*80 + "\n")

db = SessionLocal()

# Simular diferentes tipos de eventos como si fueran del Kanban
eventos_prueba = [
    {
        "tipo": "INICIO_FICHA",
        "area": "3",  # Área ACABADO
        "nombre_area": "ACABADO",
        "mensaje": "⏱️ Se inició la ficha en ACABADO - Operario: Juan Pérez"
    },
    {
        "tipo": "FIN_OPERACION",
        "area": "3",
        "nombre_area": "ACABADO",
        "mensaje": "✅ Se completó operación en ACABADO - Tiempo: 15 min"
    },
    {
        "tipo": "PROBLEMA",
        "area": "3",
        "nombre_area": "ACABADO",
        "mensaje": "⚠️ ALERTA: Equipo pausado en ACABADO - Por favor revisar"
    }
]

print("📝 Creando eventos de prueba en la BD...\n")

for i, evento in enumerate(eventos_prueba, 1):
    query = f"""
    INSERT INTO dbo.kb_alertas_eventos 
    (tipo_evento, id_area, nombre_area, mensaje, fecha_evento, enviado_whatsapp, created_at)
    VALUES 
    ('{evento['tipo']}', {evento['area']}, '{evento['nombre_area']}', 
     '{evento['mensaje']}', GETDATE(), 0, GETDATE())
    """
    
    db.execute(text(query))
    db.commit()
    
    print(f"   {i}. {evento['tipo']:<20} → {evento['mensaje']}")

print(f"\n{'='*80}")
print("✅ {0} eventos creados".format(len(eventos_prueba)))
print("="*80 + "\n")

print("⏳ Esperando 6 segundos (anti-spam)...\n")
time.sleep(6)

print(f"{'='*80}")
print("🎯 RESULTADO ESPERADO:")
print("="*80)
print("""
✅ Si todo funciona correctamente:

1. La tarea de Task Scheduler ejecutará cron_whatsapp_twilio.py cada minuto
2. El cron leerá los 3 eventos pendientes
3. Los enviará a {número_destino} por WhatsApp
4. Verás 3 mensajes en tu WhatsApp:
   - ⏱️ Se inició la ficha en ACABADO
   - ✅ Se completó operación en ACABADO
   - ⚠️ ALERTA: Equipo pausado en ACABADO

5. Los eventos se marcarán como "enviado_whatsapp = 1"

📱 Revisa tu WhatsApp en los próximos 60 segundos.

""")
print(f"{'='*80}\n")

db.close()
