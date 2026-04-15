"""
Migración: Agregar columna intentos_envio a kb_alertas_eventos
"""

from sqlalchemy import text
from app.db import SessionLocal

db = SessionLocal()

try:
    print("\n🔧 Agregando columna intentos_envio a kb_alertas_eventos...")
    
    db.execute(text("""
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'kb_alertas_eventos' 
            AND COLUMN_NAME = 'intentos_envio'
        )
        BEGIN
            ALTER TABLE dbo.kb_alertas_eventos
            ADD intentos_envio INT DEFAULT 0 NULL
            
            PRINT 'Columna intentos_envio agregada correctamente'
        END
        ELSE
        BEGIN
            PRINT 'La columna intentos_envio ya existe'
        END
    """))
    
    db.commit()
    print("✅ Migración completada")
    
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()

finally:
    db.close()
