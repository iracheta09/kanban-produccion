# -*- coding: utf-8 -*-
"""Sincronización de fichas terminadas desde ERP a Kanban"""

import sys
import io
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Fix encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROD_DB = "mssql+pyodbc://wyny:wyny@192.168.39.203/dbProduccion?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(PROD_DB, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, future=True)


def sincronizar_fichas_terminadas(modo_simulacion=True):
    db = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print("[%s] SINCRONIZACION: FICHAS TERMINADAS ERP -> KANBAN" % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("Modo: " + ("SIMULACION" if modo_simulacion else "EJECUCION REAL"))
        print("="*70)

        # Traer fichas activas en Kanban
        fichas_activas_kanban = db.execute(text("""
            SELECT f.id_ficha_estado, f.pa_tipo, f.ficha, f.id_area, f.estado_actual,
                   ISNULL(a.nombre_area, 'N/A') AS nombre_area
            FROM dbo.kb_ficha_estado f
            LEFT JOIN dbo.kb_areas a ON f.id_area = a.id_area
            WHERE f.activo = 1
            ORDER BY f.pa_tipo, f.ficha
        """)).mappings().all()

        total_activas = len(fichas_activas_kanban)
        print("\n[INFO] Fichas activas en Kanban: %d" % total_activas)

        finalizadas = 0
        no_encontradas_erp = 0
        aun_abiertas = 0

        print("\n[PROC] Verificando en ERP")
        print("-" * 70)

        for ficha in fichas_activas_kanban:
            pa_tipo = str(ficha["pa_tipo"]).strip()
            numero_ficha = str(ficha["ficha"]).strip()
            id_area = ficha["id_area"]
            nombre_area = ficha["nombre_area"]

            # Buscar ficha en ERP
            ficha_erp = db.execute(text("""
                SELECT pa_acaba FROM Vegetal.dbo.c_partid
                WHERE pa_tipo = :pa_tipo AND pa_numer = :pa_numer
            """), {"pa_tipo": pa_tipo, "pa_numer": numero_ficha}).scalar()

            if not ficha_erp:
                no_encontradas_erp += 1
                continue

            # Verificar si esta terminada
            esta_terminada = str(ficha_erp).upper().strip() ==  'S'

            if not esta_terminada:
                aun_abiertas += 1
                continue

            # Ficha esta terminada en ERP
            finalizadas += 1

            if modo_simulacion:
                print("[SIM] %s-%s -> TERMINAR en Kanban (Area: %s)" % (pa_tipo, numero_ficha, nombre_area))
                continue

            # Actualizar ficha
            db.execute(text("""
                UPDATE dbo.kb_ficha_estado
                SET estado_actual = 'FINALIZADA', fecha_ultima_accion = GETDATE(), activo = 0
                WHERE id_ficha_estado = :id_ficha_estado
            """), {"id_ficha_estado": ficha["id_ficha_estado"]})

            print("[UPD] %s-%s marcada FINALIZADA en Kanban (Area: %s)" % (pa_tipo, numero_ficha, nombre_area))

        # Commit si no es simulacion
        if not modo_simulacion and finalizadas > 0:
            db.commit()
            print("\n[OK] %d ficha(s) actualizada(s) como FINALIZADA" % finalizadas)
        else:
            if modo_simulacion:
                print("\n[OK] [SIMULACION] Se terminarían %d ficha(s)" % finalizadas)

        # Resumen
        print("\n" + "="*70)
        print("RESUMEN:")
        print("  * Fichas activas en Kanban:     %d" % total_activas)
        print("  * Terminadas en ERP:            %d" % finalizadas)
        print("  * Aun abiertas en ERP:          %d" % aun_abiertas)
        print("  * No encontradas en ERP:        %d" % no_encontradas_erp)
        print("  * Diferencia/Pendiente:         %d" % (total_activas - finalizadas - aun_abiertas))
        print("="*70 + "\n")

        return {
            "total_activas": total_activas,
            "finalizadas": finalizadas,
            "aun_abiertas": aun_abiertas,
            "no_encontradas": no_encontradas_erp
        }

    except Exception as e:
        print("\n[ERROR] " + str(e))
        import traceback
        traceback.print_exc()
        try:
            db.rollback()
        except:
            pass
        return None

    finally:
        try:
            db.close()
        except:
            pass


if __name__ == "__main__":
    modo_ejecucion = "--ejecutar" in sys.argv
    modo_simulacion = not modo_ejecucion

    if modo_simulacion:
        print("\n[ADVERTENCIA] MODO SIMULACION - Para ejecutar cambios reales, usa: --ejecutar")

    resultado = sincronizar_fichas_terminadas(modo_simulacion=modo_simulacion)

    if resultado and resultado["finalizadas"] > 0:
        sys.exit(0)
    elif resultado and modo_simulacion:
        print("[INFO] Nota: En modo real se procesarían las fichas")
        sys.exit(0)
    else:
        sys.exit(0)
