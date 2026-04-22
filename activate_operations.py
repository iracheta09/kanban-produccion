"""
Script para actualizar operaciones del área ACABADO como activas
"""
from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Actualizar operaciones P15 a P25 como activas (activo=1)
    sql = """
    UPDATE dbo.kb_operaciones
    SET activo = 1
    WHERE id_area = 2 
      AND orden_visual BETWEEN 15 AND 25
    """
    
    db.execute(text(sql))
    db.commit()
    
    print("\n✅ Operaciones actualizadas a ACTIVAS\n")
    
    # Mostrar resultado
    result = db.execute(text("""
        SELECT orden_visual, nombre_operacion, activo
        FROM dbo.kb_operaciones
        WHERE id_area = 2
        ORDER BY orden_visual
    """)).mappings().all()
    
    print("Estado actual de operaciones en área 2:\n")
    for op in result:
        estado = "✅ ACTIVA" if op['activo'] else "❌ INACTIVA"
        print(f"  P{op['orden_visual']:2} - {op['nombre_operacion']:35} {estado}")

except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
