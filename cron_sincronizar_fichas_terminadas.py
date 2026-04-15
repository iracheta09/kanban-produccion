"""
CRON - Sincronización de fichas terminadas desde ERP a Kanban
=============================================================

Objetivo:
Verificar fichas que están ACTIVAS en Kanban y comprobar si ya fueron 
marcadas como TERMINADAS en ERP (pa_acaba = 'S'). Si es así, marcarlas 
como FINALIZADA en Kanban.

Flujo:
1. Traer todas las fichas ACTIVAS en Kanban (activo = 1)
2. Para cada ficha, buscar en ERP si pa_acaba = 'S'
3. Si está terminada en ERP, marcar FINALIZADA en Kanban
4. Registrar evento de conclusión

Sincronización:
- ERP: 1998 fichas abiertas (pa_acaba = 'N')
- Kanban: 2612 fichas activas
- Diferencia: ~614 fichas que probablemente ya están terminadas en ERP
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


def sincronizar_fichas_terminadas(modo_simulacion=True):
    """
    Sincroniza fichas terminadas desde ERP hacia Kanban.
    
    Args:
        modo_simulacion (bool): Si True, solo reporta sin cambios.
                               Si False, realiza actualizaciones reales.
    """
    db = SessionLocal()

    try:
        print(f"\n{'='*70}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SINCRONIZACION: FICHAS TERMINADAS ERP -> KANBAN")
        print(f"Modo: {'SIMULACION (sin cambios)' if modo_simulacion else 'EJECUCION REAL'}")
        print(f"{'='*70}")

        # 1. Traer fichas activas en Kanban
        fichas_activas_kanban = db.execute(text("""
            SELECT
                f.id_ficha_estado,
                f.pa_tipo,
                f.ficha,
                f.id_area,
                f.estado_actual,
                ISNULL(a.nombre_area, 'N/A') AS nombre_area
            FROM dbo.kb_ficha_estado f
            LEFT JOIN dbo.kb_areas a ON f.id_area = a.id_area
            WHERE f.activo = 1
            ORDER BY f.pa_tipo, f.ficha
        """)).mappings().all()

        total_activas = len(fichas_activas_kanban)
        print(f"\n[INFO] Fichas activas en Kanban: {total_activas}")

        finalizadas = 0
        no_encontradas_erp = 0
        aun_abiertas = 0
        fichas_por_area = {}  # Dict para alertas

        print(f"\n{'Verificando en ERP':-^70}")

        for ficha in fichas_activas_kanban:
            pa_tipo = str(ficha["pa_tipo"]).strip()
            numero_ficha = str(ficha["ficha"]).strip()
            id_area = ficha["id_area"]
            nombre_area = ficha["nombre_area"]

            # 2. Buscar ficha en ERP
            ficha_erp = db.execute(text("""
                SELECT
                    pa_tipo,
                    pa_numer,
                    ISNULL(pa_acaba, '') AS pa_acaba
                FROM Vegetal.dbo.c_partid
                WHERE pa_tipo = :pa_tipo
                  AND pa_numer = :pa_numer
            """), {
                "pa_tipo": pa_tipo,
                "pa_numer": numero_ficha
            }).mappings().first()

            if not ficha_erp:
                no_encontradas_erp += 1
                print(f"[NOT FOUND] {pa_tipo}-{numero_ficha:>6} no existe en ERP")
                continue

            # 3. Verificar si está terminada en ERP
            esta_terminada = ficha_erp["pa_acaba"].upper().strip() == 'S'

            if not esta_terminada:
                aun_abiertas += 1
                print(f"[OPEN] {pa_tipo}-{numero_ficha:>6} aún abierta en ERP | Estado Kanban: {ficha['estado_actual']}")
                continue

            # 4. Ficha está terminada en ERP → Actualizar en Kanban
            finalizadas += 1

            if modo_simulacion:
                print(
                    f"[SIM] {pa_tipo}-{numero_ficha:>6} → "
                    f"TERMINAR en Kanban (Area: {nombre_area})"
                )
                continue

            # Actualizar ficha a FINALIZADA
            db.execute(text("""
                UPDATE dbo.kb_ficha_estado
                SET
                    estado_actual = 'FINALIZADA',
                    fecha_ultima_accion = GETDATE(),
                    activo = 0
                WHERE id_ficha_estado = :id_ficha_estado
            """), {
                "id_ficha_estado": ficha["id_ficha_estado"]
            })

            # Guardar para registrar evento
            if id_area not in fichas_por_area:
                fichas_por_area[id_area] = {
                    "nombre_area": nombre_area,
                    "fichas": []
                }
            fichas_por_area[id_area]["fichas"].append({
                "pa_tipo": pa_tipo,
                "ficha": numero_ficha
            })

            print(
                f"[UPD] {pa_tipo}-{numero_ficha:>6} marcada FINALIZADA en Kanban "
                f"(Área: {nombre_area})"
            )

        # Commit si no es simulación
        if not modo_simulacion and finalizadas > 0:
            db.commit()
            print(f"\n[OK] {finalizadas} ficha(s) actualizada(s) como FINALIZADA")
            
            # Registrar eventos de término
            for id_area_iter, area_info in fichas_por_area.items():
                fichas_area = area_info["fichas"]
                nombre_area = area_info["nombre_area"]
                
                if fichas_area:
                    # Usar la última ficha actualizada
                    ultima_ficha = fichas_area[-1]
                    
                    # Registrar evento LOTE_TERMINADO
                    try:
                        registrar_evento_alerta(
                            tipo_evento="LOTE_TERMINADO",
                            id_area=id_area_iter,
                            nombre_area=nombre_area,
                            mensaje=f"Ficha {ultima_ficha['pa_tipo']}-{ultima_ficha['ficha']} terminada en ERP",
                            ficha=f"{ultima_ficha['pa_tipo']}-{ultima_ficha['ficha']}"
                        )
                        print(f"[INFO] Evento registrado para {nombre_area}")
                    except Exception as e:
                        print(f"[WARN] Error al registrar evento: {str(e)}")

        else:
            if modo_simulacion:
                print(f"\n[OK] [SIMULACION] Se terminarían {finalizadas} ficha(s)")

        # Resumen
        print(f"\n{'='*70}")
        print(f"RESUMEN:")
        print(f"  * Fichas activas en Kanban:     {total_activas}")
        print(f"  * Terminadas en ERP:            {finalizadas}")
        print(f"  * Aun abiertas en ERP:          {aun_abiertas}")
        print(f"  * No encontradas en ERP:        {no_encontradas_erp}")
        print(f"  * Diferencia/Pendiente verificar: {total_activas - finalizadas - aun_abiertas}")
        print(f"{'='*70}\n")

        return {
            "total_activas": total_activas,
            "finalizadas": finalizadas,
            "aun_abiertas": aun_abiertas,
            "no_encontradas": no_encontradas_erp
        }

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None

    finally:
        db.close()


if __name__ == "__main__":
    # Determinar modo
    modo_ejecucion = "--ejecutar" in sys.argv
    modo_simulacion = not modo_ejecucion

    if modo_simulacion:
        print("\n[ADVERTENCIA] MODO SIMULACION - Para ejecutar cambios reales, usa: --ejecutar")

    resultado = sincronizar_fichas_terminadas(modo_simulacion=modo_simulacion)

    if resultado:
        # Retornar código de salida basado en resultados
        if resultado["finalizadas"] > 0:
            sys.exit(0)  # Exito
        elif modo_simulacion:
            print("\n[INFO] Nota: En modo real se procesarían las fichas")
            sys.exit(0)
        else:
            sys.exit(0)  # Sin errores, pero sin cambios
