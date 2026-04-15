from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Obtener la restricción actual
    result = db.execute(text("""
        SELECT definition
        FROM sys.check_constraints
        WHERE parent_object_id = OBJECT_ID('kb_ficha_estado')
        AND name = 'CK_kb_ficha_estado_estado'
    """)).scalar()
    
    if result:
        print("Restricción actual encontrada:")
        print(result)
    else:
        print("No se encontró la restricción")
    
    # Eliminar la restricción antigua
    db.execute(text("""
        ALTER TABLE kb_ficha_estado
        DROP CONSTRAINT CK_kb_ficha_estado_estado
    """))
    db.commit()
    print("✅ Restricción antigua eliminada")
    
    # Crear la nueva restricción con PAUSA incluido
    db.execute(text("""
        ALTER TABLE kb_ficha_estado
        ADD CONSTRAINT CK_kb_ficha_estado_estado
        CHECK (estado_actual IN ('LISTA', 'CURSO', 'PAUSA', 'FINALIZADA'))
    """))
    db.commit()
    print("✅ Nueva restricción creada con PAUSA incluido")
    
finally:
    db.close()
