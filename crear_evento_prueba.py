from sqlalchemy import text
from app.db import SessionLocal

db = SessionLocal()
db.execute(text("""
    INSERT INTO dbo.kb_alertas_eventos 
    (tipo_evento, id_area, nombre_area, mensaje, fecha_evento, enviado_whatsapp, created_at)
    VALUES 
    ('PRUEBA_NUMERO_PERSONAL', 3, 'ACABADO', 
     'Número personal verificado: Sistema Kanban + WhatsApp listo', 
     GETDATE(), 0, GETDATE())
"""))
db.commit()
db.close()
print('✅ Evento de prueba creado')
