@echo off
REM Script para crear tarea en Windows Task Scheduler
REM Ejecutar como Administrador

echo Creando tarea en Task Scheduler...
schtasks /create /tn "Enviar Alertas Kanban WhatsApp" /tr "C:\kanban_produccion\.venv\Scripts\python.exe C:\kanban_produccion\cron_whatsapp_twilio.py" /sc minute /mo 1 /ru SYSTEM /f

if %ERRORLEVEL% == 0 (
    echo.
    echo ✅ Tarea creada correctamente
    echo La tarea se ejecutará cada minuto automáticamente
) else (
    echo.
    echo ❌ Error al crear la tarea
    echo Asegúrate de ejecutar este archivo como Administrador
)

pause
