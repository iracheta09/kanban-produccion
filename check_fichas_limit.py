"""
Script para verificar si hay un límite de 15 fichas
"""
from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Contar fichas por área
    areas = db.execute(text('SELECT id_area, nombre_area FROM dbo.kb_areas WHERE activo=1')).mappings().all()
    
    print('\n' + '='*60)
    print('VERIFICACIÓN DE FICHAS POR ÁREA')
    print('='*60 + '\n')
    
    for area in areas:
        count = db.execute(text('''
            SELECT COUNT(*) as total
            FROM dbo.kb_ficha_estado
            WHERE id_area = :id_area AND activo = 1
        '''), {'id_area': area['id_area']}).scalar()
        
        print(f"  Área {area['id_area']:2} - {area['nombre_area']:20}: {count:3} fichas")
    
    print('\n' + '='*60)
    print('Si ves más de 15 fichas en algún área, el límite está en')
    print('el TEMPLATE HTML o CSS, no en la base de datos.')
    print('='*60 + '\n')

except Exception as e:
    print(f'Error: {e}')
finally:
    db.close()
