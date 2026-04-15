"""
Crear evento de prueba y enviar a WhatsApp
"""

from sqlalchemy import text
from app.db import SessionLocal
import time

print("\n" + "="*70)
print("🧪 PRUEBA: Crear evento y enviar a WhatsApp")
print("="*70)

db = SessionLocal()

try:
    print("\n1️⃣ Creando evento de prueba en BD...")
    
    db.execute(text("""
        INSERT INTO dbo.kb_alertas_eventos 
        (tipo_evento, id_area, nombre_area, mensaje, fecha_evento, enviado_whatsapp, created_at)
        VALUES 
        ('PRUEBA_SISTEMA', 3, 'ACABADO', 
         '✅ PRUEBA EXITOSA: Sistema Kanban + WhatsApp funcionando correctamente', 
         GETDATE(), 0, GETDATE())
    """))
    db.commit()
    print("   ✅ Evento creado en BD")
    
    print("\n2️⃣ Ejecutando cron (esperando 2 segundos)...")
    time.sleep(2)
    
    # Ejecutar el cron
    import subprocess
    resultado = subprocess.run(
        [r"C:\kanban_produccion\.venv\Scripts\python.exe", r"C:\kanban_produccion\cron_enviar_alertas.py"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print("\n3️⃣ Resultado del cron:")
    print("─" * 70)
    print(resultado.stdout)
    
    if resultado.stderr:
        print("ERRORES:")
        print(resultado.stderr)
    
    print("─" * 70)
    print("\n✅ PRUEBA COMPLETADA")
    print("\n📱 El mensaje debería estar en tu WhatsApp:")
    print('   "✅ PRUEBA EXITOSA: Sistema Kanban + WhatsApp funcionando correctamente"')
    print("\n👉 Verifica tu WhatsApp en los próximos 30 segundos")
    
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()

finally:
    db.close()

print("\n" + "="*70 + "\n")
