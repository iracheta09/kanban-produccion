# -*- coding: utf-8 -*-
"""Validación de sincronización entre ERP y Kanban"""

import sys
import io
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROD_DB = "mssql+pyodbc://wyny:wyny@192.168.39.203/dbProduccion?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(PROD_DB, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, future=True)


def validar_y_sincronizar(modo_simulacion=True):
    db = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print("[%s] VALIDACION DE SINCRONIZACION: ERP <-> KANBAN" % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("Modo: " + ("SIMULACION" if modo_simulacion else "EJECUCION REAL"))
        print("="*70)

        # 1. Contar fichas ABIERTAS en ERP
        fichas_abiertas_erp = db.execute(text("""
            SELECT COUNT(*) as total FROM Vegetal.dbo.c_partid
            WHERE PA_ACABA = 'N'
        """)).scalar()

        print("\n[ERP] Fichas abiertas (PA_ACABA='N'): %d" % fichas_abiertas_erp)

        # 2. Contar fichas ACTIVAS en Kanban
        fichas_activas_kanban = db.execute(text("""
            SELECT COUNT(*) as total FROM dbo.kb_ficha_estado
            WHERE activo = 1
        """)).scalar()

        print("[Kanban] Fichas activas (activo=1): %d" % fichas_activas_kanban)

        # 3. Diferencia
        diferencia = fichas_activas_kanban - fichas_abiertas_erp
        print("\n[DIFF] Diferencia: %d fichas" % diferencia)

        if diferencia > 0:
            print("[INFO] Hay %d ficha(s) en Kanban que NO estan en ERP o estan terminadas" % diferencia)

        # 4. Buscar fichas en Kanban que NO existen en ERP o estan terminadas
        fichas_inconsistentes = db.execute(text("""
            SELECT DISTINCT
                k.id_ficha_estado,
                k.pa_tipo,
                k.ficha,
                ISNULL(a.nombre_area, 'N/A') AS nombre_area,
                k.estado_actual,
                CASE 
                    WHEN e.pa_numer IS NULL THEN 'NO EXISTE EN ERP'
                    WHEN e.pa_acaba = 'S' THEN 'TERMINADA EN ERP'
                    ELSE 'OK'
                END AS status_erp
            FROM dbo.kb_ficha_estado k
            LEFT JOIN Vegetal.dbo.c_partid e ON k.pa_tipo = e.pa_tipo AND k.ficha = e.pa_numer
            LEFT JOIN dbo.kb_areas a ON k.id_area = a.id_area
            WHERE k.activo = 1
              AND (e.pa_numer IS NULL OR e.pa_acaba = 'S')
            ORDER BY k.pa_tipo, k.ficha
        """)).mappings().all()

        inconsistentes_count = len(fichas_inconsistentes)
        print("\n[PROC] Fichas inconsistentes encontradas: %d" % inconsistentes_count)

        if inconsistentes_count > 0:
            print("\n" + "-"*70)
            print("Fichas que deben desactivarse:")
            print("-"*70)
            
            fichas_a_desactivar = []
            for ficha in fichas_inconsistentes:
                print("[%s] %s-%s | Area: %s | Estado: %s | ERP: %s" % (
                    "NO_OK" if modo_simulacion else "UPD",
                    ficha["pa_tipo"],
                    ficha["ficha"],
                    ficha["nombre_area"],
                    ficha["estado_actual"],
                    ficha["status_erp"]
                ))
                fichas_a_desactivar.append(ficha)

            if not modo_simulacion:
                # Desactivar fichas
                ids_a_cambiar = [f["id_ficha_estado"] for f in fichas_a_desactivar]
                
                for id_ficha in ids_a_cambiar:
                    db.execute(text("""
                        UPDATE dbo.kb_ficha_estado
                        SET activo = 0, fecha_ultima_accion = GETDATE()
                        WHERE id_ficha_estado = :id_ficha_estado
                    """), {"id_ficha_estado": id_ficha})
                
                db.commit()
                print("\n[OK] %d ficha(s) desactivada(s)" % len(ids_a_cambiar))
            else:
                print("\n[OK] [SIMULACION] Se desactivarían %d ficha(s)" % inconsistentes_count)

        # 5. Verificar fichas en ERP que NO estan en Kanban
        fichas_erp_no_en_kanban = db.execute(text("""
            SELECT COUNT(*) as total
            FROM Vegetal.dbo.c_partid e
            WHERE e.PA_ACABA = 'N'
              AND NOT EXISTS (
                SELECT 1 FROM dbo.kb_ficha_estado k
                WHERE k.pa_tipo = e.pa_tipo AND k.ficha = e.pa_numer AND k.activo = 1
              )
        """)).scalar()

        print("\n[ERP->Kanban] Fichas en ERP que NO estan activas en Kanban: %d" % fichas_erp_no_en_kanban)

        # Resumen final
        print("\n" + "="*70)
        print("RESUMEN FINAL:")
        print("  * Fichas abiertas ERP (PA_ACABA='N'):  %d" % fichas_abiertas_erp)
        print("  * Fichas activas Kanban (activo=1):    %d" % fichas_activas_kanban)
        print("  * Diferencia (excess en Kanban):       %d" % diferencia)
        print("  * Fichas inconsistentes:               %d" % inconsistentes_count)
        print("  * Fichas ERP no en Kanban:             %d" % fichas_erp_no_en_kanban)
        print("="*70 + "\n")

        if fichas_activas_kanban == fichas_abiertas_erp - inconsistentes_count:
            print("[ESTADO] SINCRONIZACION CORRECTA")
        else:
            print("[ESTADO] SINCRONIZACION PENDIENTE")

        return {
            "fichas_abiertas_erp": fichas_abiertas_erp,
            "fichas_activas_kanban": fichas_activas_kanban,
            "diferencia": diferencia,
            "inconsistentes": inconsistentes_count,
            "fichas_erp_no_kanban": fichas_erp_no_en_kanban
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

    resultado = validar_y_sincronizar(modo_simulacion=modo_simulacion)
    sys.exit(0 if resultado else 1)
