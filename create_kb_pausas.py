from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Verificar si existe y eliminarla para recrearla limpia
    result = db.execute(text("""
        SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'kb_pausas'
    """)).scalar()
    
    if result:
        print("Tabla kb_pausas ya existe, manteniéndola...")
        db.close()
    else:
        # Crear la tabla
        db.execute(text("""
            CREATE TABLE dbo.kb_pausas
            (
                id_pausa            BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                pa_tipo             VARCHAR(20) NOT NULL,
                ficha               VARCHAR(30) NOT NULL,
                id_area             INT NOT NULL,
                id_operacion        INT NOT NULL,
                id_operario         VARCHAR(20) NULL,
                nombre_operario     VARCHAR(150) NULL,

                motivo_pausa        VARCHAR(50) NOT NULL,
                fecha_inicio_pausa  DATETIME NOT NULL DEFAULT(GETDATE()),
                fecha_fin_pausa     DATETIME NULL,

                estatus_pausa       VARCHAR(20) NOT NULL DEFAULT('ACTIVA'),
                observaciones       VARCHAR(300) NULL,

                created_at          DATETIME NOT NULL DEFAULT(GETDATE()),
                updated_at          DATETIME NULL
            )
        """))
        
        # Crear índice
        db.execute(text("""
            CREATE INDEX IX_kb_pausas_patipo_ficha
            ON dbo.kb_pausas(pa_tipo, ficha)
        """))
        
        db.commit()
        print("✅ Tabla kb_pausas creada correctamente")
        db.close()
        
finally:
    pass
