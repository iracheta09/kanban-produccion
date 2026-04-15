from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text("""
        SELECT TOP 5 id_operacion, nombre_operacion, tipo_operacion
        FROM dbo.vw_kb_tablero
    """)).mappings().fetchall()
    
    if result:
        print("✅ tipo_operacion encontrado. Valores:")
        for row in result:
            print(f"  {row['nombre_operacion']} → {row['tipo_operacion']}")
    else:
        print("No hay datos en vw_kb_tablero")
finally:
    db.close()
