# Script PowerShell para crear la tarea en Windows Task Scheduler
# Ejecutar COMO ADMINISTRADOR

# Rutas
$ScriptPath = "C:\kanban_produccion\cron_enviar_alertas.py"
$PythonExe = "C:\kanban_produccion\.venv\Scripts\python.exe"
$TareaNombre = "Enviar Alertas WhatsApp"

# Verificar si ya existe
$TareaExistente = Get-ScheduledTask -TaskName $TareaNombre -ErrorAction SilentlyContinue

if ($TareaExistente) {
    Write-Host "⚠️  La tarea ya existe. Eliminando versión anterior..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TareaNombre -Confirm:$false
}

# Crear la tarea
Write-Host "🔧 Creando tarea: $TareaNombre" -ForegroundColor Cyan
Write-Host "   Frecuencia: Cada 1 minuto" -ForegroundColor Cyan
Write-Host "   Script: $ScriptPath" -ForegroundColor Cyan

# Configura para ejecutarse cada 1 minuto
$Trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 1) -Once -At (Get-Date)
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $ScriptPath
$Principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName $TareaNombre -Trigger $Trigger -Action $Action -Principal $Principal -Settings $Settings -Force

Write-Host "`n✅ Tarea creada exitosamente" -ForegroundColor Green
Write-Host "`nVerifica en:" -ForegroundColor Cyan
Write-Host "  1. Panel de Control > Herramientas administrativas > Programador de tareas" -ForegroundColor White
Write-Host "  2. Busca: $TareaNombre" -ForegroundColor White

# Mostrar estado
Write-Host "`n📊 Estado actual:" -ForegroundColor Cyan
$Tarea = Get-ScheduledTask -TaskName $TareaNombre
Write-Host "   Estado: $($Tarea.State)" -ForegroundColor White
Write-Host "   Próxima ejecución: (se verá en Programador de tareas)" -ForegroundColor White
