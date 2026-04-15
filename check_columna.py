from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'kb_ficha_estado' 
        AND COLUMN_NAME = 'fecha_inicio'
    """)).scalar()
    
    if result:
        print('✅ Columna fecha_inicio ya existe')
    else:
        db.execute(text("""
            ALTER TABLE kb_ficha_estado
            ADD fecha_inicio DATETIME NULL
        """))
        db.commit()
        print('✅ Columna fecha_inicio creada')
finally:
    db.close()
