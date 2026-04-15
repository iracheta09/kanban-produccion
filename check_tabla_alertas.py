"""
Script para validar estructura de tabla kb_alertas_eventos
"""

from sqlalchemy import text, inspect
from app.db import SessionLocal

db = SessionLocal()

try:
    # Obtener información sobre la tabla
    result = db.execute(text("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'kb_alertas_eventos'
        ORDER BY ORDINAL_POSITION
    """)).mappings().all()
    
    print("\n📋 ESTRUCTURA DE TABLA kb_alertas_eventos:")
    print("=" * 70)
    
    if result:
        for col in result:
            nullable = "NULL" if col["IS_NULLABLE"] == "YES" else "NOT NULL"
            print(f"  {col['COLUMN_NAME']:30} | {col['DATA_TYPE']:20} | {nullable}")
    else:
        print("  ❌ Tabla no encontrada")
    
    print("=" * 70)
    
except Exception as e:
    print(f"Error: {e}")

finally:
    db.close()
