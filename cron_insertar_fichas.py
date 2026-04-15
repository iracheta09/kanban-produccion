"""
CRON - Fase 2: Inserción automática de fichas abiertas
========================================================

Objetivo:
Traer todas las fichas abiertas de ERP (Curtits) que tienen área natural asignada
e insertarlas en kb_ficha_estado si no existen activas ya en el tablero.

Flujo:
1. Buscar fichas en c_partid con pa_acaba = 'N'
2. Que tengan área natural en kb_area_partidas
3. Verificar que no existan activas en kb_ficha_estado
4. Buscar operación RECEPCION del área
5. Insertar la ficha en LISTA, estado NORMAL, origen ERP
"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.services.alerta_service import registrar_evento_alerta

# Configuración de conexiones
PROD_DB = "mssql+pyodbc://wyny:wyny@192.168.39.203/dbProduccion?driver=ODBC+Driver+17+for+SQL+Server"

engine = create_engine(PROD_DB, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, future=True)

# CONFIGURACIÓN IMPORTANTE
# En la primera ejecución real, limita fichas para evitar saturar el tablero
# Comentar o cambiar este valor para cargar todas las fichas
LIMITE_FICHAS_PRIMERA_CARGA = 30  # Limita a 30 fichas en ejecución real
APLICAR_LIMITE = False  # Cambiar a True para limitar en la primera corrida real


def insertar_fichas_abiertas(modo_simulacion=True):
    """
    Inserta fichas abiertas de ERP en el tablero del Kanban.
    
    Args:
        modo_simulacion (bool): Si True, solo reporta sin insertar.
                               Si False, realiza inserciones reales.
    """
    db = SessionLocal()

    try:
        print(f"\n{'='*70}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INICIO ALTA AUTOMÁTICA DE FICHAS")
        print(f"Modo: {'SIMULACIÓN (sin cambios)' if modo_simulacion else 'EJECUCIÓN REAL'}")
        print(f"{'='*70}")

        # 1. Traer fichas abiertas en Curtits que tengan área natural definida
        fichas_erp = db.execute(text("""
            SELECT
                p.pa_tipo,
                p.pa_numer AS ficha,
                ap.id_area
            FROM Vegetal.dbo.c_partid p
            INNER JOIN dbo.kb_area_partidas ap
                ON ap.pa_tipo = p.pa_tipo
               AND ap.activo = 1
            WHERE UPPER(LTRIM(RTRIM(ISNULL(p.pa_acaba, '')))) = 'N'
            ORDER BY p.pa_tipo, p.pa_numer
        """)).mappings().all()

        total_fichas_erp = len(fichas_erp)
        
        # APLICAR LÍMITE si está habilitado (solo en ejecución real, no en simulación)
        if APLICAR_LIMITE and not modo_simulacion:
            fichas_erp = fichas_erp[:LIMITE_FICHAS_PRIMERA_CARGA]
            print(f"\n⚠️  LÍMITE APLICADO: Cargando solo {len(fichas_erp)} de {total_fichas_erp} fichas abiertas")
        
        print(f"\n📊 Fichas a procesar: {len(fichas_erp)} (Total en ERP: {total_fichas_erp})")

        insertadas = 0
        ya_existian = 0
        sin_recepcion = 0
        fichas_por_area = {}  # Dict para guardar fichas insertadas por área

        print(f"\n{'Validando altas':─^70}")

        for ficha in fichas_erp:
            pa_tipo = str(ficha["pa_tipo"]).strip()
            numero_ficha = str(ficha["ficha"]).strip()
            id_area = ficha["id_area"]

            # 2. Verificar si ya existe activa en tablero
            existe_activa = db.execute(text("""
                SELECT COUNT(*)
                FROM dbo.kb_ficha_estado
                WHERE pa_tipo = :pa_tipo
                  AND ficha = :ficha
                  AND activo = 1
            """), {
                "pa_tipo": pa_tipo,
                "ficha": numero_ficha
            }).scalar()

            if existe_activa and existe_activa > 0:
                ya_existian += 1
                print(f"[OK]  {pa_tipo}-{numero_ficha:>6} ya existe activa en tablero")
                continue

            # 3. Buscar operación de recepción del área
            id_operacion_recepcion = db.execute(text("""
                SELECT TOP 1 id_operacion
                FROM dbo.kb_operaciones
                WHERE id_area = :id_area
                  AND tipo_operacion = 'RECEPCION'
                  AND activo = 1
                ORDER BY orden_visual
            """), {
                "id_area": id_area
            }).scalar()

            if not id_operacion_recepcion:
                sin_recepcion += 1
                print(f"[WARN] {pa_tipo}-{numero_ficha:>6} NO tiene operación RECEPCION en área {id_area}")
                continue

            if modo_simulacion:
                print(
                    f"[SIM] {pa_tipo}-{numero_ficha:>6} → "
                    f"Área {id_area} | Recepción op={id_operacion_recepcion}"
                )
                insertadas += 1
                continue

            # 4. Insertar ficha en el tablero
            db.execute(text("""
                INSERT INTO dbo.kb_ficha_estado
                (
                    ficha,
                    pa_tipo,
                    id_area,
                    id_operacion_actual,
                    estado_actual,
                    tipo_ingreso,
                    fecha_ultima_accion,
                    origen_ficha,
                    activo,
                    created_at
                )
                VALUES
                (
                    :ficha,
                    :pa_tipo,
                    :id_area,
                    :id_operacion_actual,
                    'LISTA',
                    'NORMAL',
                    GETDATE(),
                    'ERP',
                    1,
                    GETDATE()
                )
            """), {
                "ficha": numero_ficha,
                "pa_tipo": pa_tipo,
                "id_area": id_area,
                "id_operacion_actual": id_operacion_recepcion
            })

            insertadas += 1
            
            # Guardar ficha insertada por área para notificación WhatsApp
            if id_area not in fichas_por_area:
                fichas_por_area[id_area] = []
            fichas_por_area[id_area].append({
                "pa_tipo": pa_tipo,
                "ficha": numero_ficha
            })

            print(
                f"[ADD] {pa_tipo}-{numero_ficha:>6} insertada en área {id_area}, "
                f"operación recepción {id_operacion_recepcion}"
            )

        # Commit si no es simulación
        if not modo_simulacion and insertadas > 0:
            db.commit()
            print(f"\n✅ {insertadas} fila(s) insertada(s) en base de datos")
            
            # Registrar evento LLEGADA_FICHAS para todas las áreas con fichas insertadas
            for id_area_iter, fichas_area in fichas_por_area.items():
                if fichas_area:
                    # Obtener información del área
                    area_info = db.execute(text("""
                        SELECT nombre_area FROM kb_areas WHERE id_area = :id_area
                    """), {"id_area": id_area_iter}).scalar()
                    nombre_area = area_info or f"Área {id_area_iter}"
                    
                    # Usar la última ficha insertada en esta área
                    ultima_ficha = fichas_area[-1]
                    
                    # Obtener pzas_actuales de la última ficha (si es NULL, usar 0)
                    pzas_insertar = db.execute(text("""
                        SELECT ISNULL(pzas_actuales, 0) as pzas FROM kb_ficha_estado 
                        WHERE pa_tipo = :pa_tipo AND ficha = :ficha
                    """), {
                        "pa_tipo": ultima_ficha["pa_tipo"],
                        "ficha": ultima_ficha["ficha"]
                    }).scalar()
                    
                    mensaje = f"{nombre_area}: llegaron {len(fichas_area)} fichas nuevas."
                    registrar_evento_alerta(
                        tipo_evento="LLEGADA_FICHAS",
                        id_area=id_area_iter,
                        nombre_area=nombre_area,
                        pa_tipo=ultima_ficha["pa_tipo"],
                        ficha=ultima_ficha["ficha"],
                        pzas=pzas_insertar,
                        mensaje=mensaje,
                        db=db
                    )
                    print(f"🔔 Evento de alerta registrado: {mensaje}")
                
        elif modo_simulacion:
            print(f"\n⚠️  Modo simulación: No se realizaron inserciones")

        # Resumen final
        print(f"\n{'RESUMEN':─^70}")
        print(f"  Total fichas abiertas en ERP:   {total_fichas_erp:>4}")
        print(f"  Fichas procesadas:              {len(fichas_erp):>4}")
        print(f"  Nuevas fichas insertadas:       {insertadas:>4}")
        print(f"  Ya existían activas:            {ya_existian:>4}")
        print(f"  Sin operación recepción:        {sin_recepcion:>4}")
        if APLICAR_LIMITE and not modo_simulacion and len(fichas_erp) < total_fichas_erp:
            print(f"\n  ⚠️  Próxima corrida: {total_fichas_erp - len(fichas_erp)} fichas pendientes")
        print(f"{'='*70}\n")

    except Exception as e:
        if not modo_simulacion:
            db.rollback()
        print(f"\n❌ ERROR en alta automática: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    # Determinar modo por argumento de línea de comandos
    modo_sim = True
    
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--ejecutar":
        modo_sim = False
        print("\n⚠️  MODO EJECUCIÓN ACTIVADO - Se insertarán fichas en la BD")
        
        if APLICAR_LIMITE:
            print(f"    LÍMITE ACTIVO: Solo se insertarán {LIMITE_FICHAS_PRIMERA_CARGA} fichas")
        else:
            print(f"    Se insertarán TODAS las fichas abiertas de ERP")
        
        confirmacion = input("¿Deseas continuar? (si/no): ").strip().lower()
        if confirmacion != "si":
            print("Operación cancelada.")
            sys.exit(0)

    insertar_fichas_abiertas(modo_simulacion=modo_sim)
