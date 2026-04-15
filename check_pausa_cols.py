from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Verificar y crear motivo_pausa
    result1 = db.execute(text("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'kb_ficha_estado' 
        AND COLUMN_NAME = 'motivo_pausa'
    """)).scalar()
    
    if not result1:
        db.execute(text("""
            ALTER TABLE kb_ficha_estado
            ADD motivo_pausa VARCHAR(50)
        """))
        db.commit()
        print('✅ Columna motivo_pausa creada')
    else:
        print('✅ Columna motivo_pausa ya existe')
    
    # Verificar y crear fecha_pausa
    result2 = db.execute(text("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'kb_ficha_estado' 
        AND COLUMN_NAME = 'fecha_pausa'
    """)).scalar()
    
    if not result2:
        db.execute(text("""
            ALTER TABLE kb_ficha_estado
            ADD fecha_pausa DATETIME
        """))
        db.commit()
        print('✅ Columna fecha_pausa creada')
    else:
        print('✅ Columna fecha_pausa ya existe')
        
finally:
    db.close()
