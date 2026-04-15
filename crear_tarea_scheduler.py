"""
Script para crear automáticamente la tarea en Windows Task Scheduler
Ejecutar como Administrador
"""

import subprocess
import os

def crear_tarea_scheduled():
    """Crea la tarea en Windows Task Scheduler"""
    
    script_path = r"C:\kanban_produccion\cron_enviar_alertas.py"
    python_path = r"C:\kanban_produccion\.venv\Scripts\python.exe"
    tarea_nombre = "Enviar Alertas WhatsApp"
    
    # Comando para crear la tarea (cada 1 minuto)
    cmd = f'''
    schtasks /create /tn "{tarea_nombre}" ^
        /tr "{python_path} {script_path}" ^
        /sc minute /mo 1 ^
        /ru SYSTEM ^
        /f
    '''
    
    print("🔧 Creando tarea en Windows Task Scheduler...")
    print(f"   Nombre: {tarea_nombre}")
    print(f"   Frecuencia: Cada 1 minuto")
    print(f"   Script: {script_path}")
    
    try:
        resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if resultado.returncode == 0:
            print("\n✅ Tarea creada exitosamente")
            print("\nVerifica en:")
            print("  1. Panel de Control > Herramientas administrativas > Programador de tareas")
            print("  2. O ejecuta: tasklist /v | findstr Alertas")
            return True
        else:
            print(f"\n❌ Error: {resultado.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False


if __name__ == "__main__":
    # Verificar si se ejecuta como administrador
    import ctypes
    try:
        es_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        es_admin = False
    
    if not es_admin:
        print("⚠️  ERROR: Este script debe ejecutarse como Administrador")
        print("\nPasos:")
        print("  1. Abre PowerShell como Administrador")
        print("  2. Ejecuta: python crear_tarea_scheduler.py")
        exit(1)
    
    crear_tarea_scheduled()
