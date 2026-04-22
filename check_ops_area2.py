"""
Verificar operaciones del área ACABADO
"""
from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Ver operaciones del área ACABADO (id_area = 2)
    ops = db.execute(text('''
        SELECT id_operacion, nombre_operacion, tipo_operacion, orden_visual
        FROM dbo.kb_operaciones
        WHERE id_area = 2 AND activo = 1
        ORDER BY orden_visual
    ''')).mappings().all()
    
    print(f'\n=== OPERACIONES ÁREA ACABADO (id_area=2) ===')
    print(f'Total: {len(ops)} operaciones\n')
    
    for op in ops:
        print(f"  {op['orden_visual']:2} - {op['nombre_operacion']:30} ({op['tipo_operacion']})")

except Exception as e:
    print(f'Error: {e}')
finally:
    db.close()
