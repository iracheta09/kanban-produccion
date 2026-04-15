"""
CRON - Fase 1: Depuración de fichas activas
============================================

Objetivo:
Validar que todas las fichas activas en kb_ficha_estado existan y estén abiertas en Curtits.
Si no, desactivarlas y registrar el motivo en motivo_baja.

Reglas:
- Si la ficha NO existe en c_partid → motivo_baja = 'NO_EXISTE_EN_ERP'
- Si la ficha existe pero pa_acaba != 'N' → motivo_baja = 'CERRADA_EN_ERP'
- Si todo OK → mantener activo = 1
"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Configuración de conexiones
PROD_DB = "mssql+pyodbc://wyny:wyny@192.168.39.203/dbProduccion?driver=ODBC+Driver+17+for+SQL+Server"
CURTITS_DB = "mssql+pyodbc://wyny:wyny@192.168.39.203/Vegetal?driver=ODBC+Driver+17+for+SQL+Server"

engine_prod = create_engine(PROD_DB, echo=False, future=True)
engine_curtits = create_engine(CURTITS_DB, echo=False, future=True)

SessionProd = sessionmaker(bind=engine_prod, future=True)
SessionCurtits = sessionmaker(bind=engine_curtits, future=True)


def depurar_fichas_activas(modo_simulacion=True):
    """
    Valida y depura fichas activas.
    
    Args:
        modo_simulacion (bool): Si True, solo reporta sin modificar datos.
                               Si False, realiza actualizaciones.
    """
    db_prod = SessionProd()
    db_curtits = SessionCurtits()

    try:
        print(f"\n{'='*70}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INICIO DEPURACIÓN DE FICHAS ACTIVAS")
        print(f"Modo: {'SIMULACIÓN (sin cambios)' if modo_simulacion else 'ACTUALIZACIÓN (con cambios)'}")
        print(f"{'='*70}")

        # 1. Obtener todas las fichas activas del tablero
        fichas_activas = db_prod.execute(text("""
            SELECT
                id_ficha_estado,
                pa_tipo,
                ficha
            FROM dbo.kb_ficha_estado
            WHERE activo = 1
            ORDER BY pa_tipo, ficha
        """)).mappings().all()

        print(f"\n📊 Fichas activas encontradas: {len(fichas_activas)}")

        desactivadas = 0
        no_existe_erp = 0
        cerrada_erp = 0
        ok = 0

        # 2. Validar cada ficha contra Curtits
        print(f"\n{'Validando fichas':─^70}")
        
        for ficha in fichas_activas:
            existe_en_curtits = db_curtits.execute(text("""
                SELECT TOP 1
                    pa_acaba
                FROM dbo.c_partid
                WHERE pa_tipo = :pa_tipo
                  AND pa_numer = :ficha
            """), {
                "pa_tipo": ficha["pa_tipo"],
                "ficha": ficha["ficha"]
            }).mappings().first()

            # Determinar motivo
            motivo = None
            
            if not existe_en_curtits:
                motivo = "NO_EXISTE_EN_ERP"
                no_existe_erp += 1
            elif str(existe_en_curtits["pa_acaba"]).strip().upper() != "N":
                motivo = "CERRADA_EN_ERP"
                cerrada_erp += 1
            else:
                ok += 1
                continue  # Ficha sigue activa, no hacer nada

            # Desactivar la ficha
            desactivadas += 1

            if modo_simulacion:
                print(
                    f"[SIM] {ficha['pa_tipo']}-{ficha['ficha']:>6} | "
                    f"Motivo: {motivo} | "
                    f"Estado: id_ficha_estado={ficha['id_ficha_estado']}"
                )
            else:
                db_prod.execute(text("""
                    UPDATE dbo.kb_ficha_estado
                    SET activo = 0,
                        motivo_baja = :motivo,
                        updated_at = GETDATE(),
                        fecha_ultima_accion = GETDATE()
                    WHERE id_ficha_estado = :id_ficha_estado
                """), {
                    "id_ficha_estado": ficha["id_ficha_estado"],
                    "motivo": motivo
                })

                print(
                    f"[OK]  {ficha['pa_tipo']}-{ficha['ficha']:>6} | "
                    f"Motivo: {motivo:20} | "
                    f"Desactivada (id_ficha_estado={ficha['id_ficha_estado']})"
                )

        # Commit si no es simulación
        if not modo_simulacion and desactivadas > 0:
            db_prod.commit()
            print(f"\n✅ Cambios guardados en la base de datos")
        elif modo_simulacion:
            print(f"\n⚠️  Modo simulación: No se realizaron cambios")

        # Resumen final
        print(f"\n{'RESUMEN':─^70}")
        print(f"  Total fichas activas:      {len(fichas_activas):>4}")
        print(f"  Fichas OK en ERP:          {ok:>4}")
        print(f"  Fichas desactivadas:       {desactivadas:>4}")
        print(f"    └─ No existen en ERP:    {no_existe_erp:>4}")
        print(f"    └─ Cerradas en ERP:      {cerrada_erp:>4}")
        print(f"{'='*70}\n")

    except Exception as e:
        if not modo_simulacion:
            db_prod.rollback()
        print(f"\n❌ ERROR en depuración: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db_prod.close()
        db_curtits.close()


if __name__ == "__main__":
    # Determinar modo por argumento de línea de comandos
    modo_sim = True
    
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--actualizar":
        modo_sim = False
        print("\n⚠️  MODO ACTUALIZACIÓN ACTIVADO - Se realizarán cambios en la BD")
        confirmacion = input("¿Deseas continuar? (si/no): ").strip().lower()
        if confirmacion != "si":
            print("Operación cancelada.")
            sys.exit(0)

    depurar_fichas_activas(modo_simulacion=modo_sim)
