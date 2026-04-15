# setup_cron_tasks.ps1
# Configura tareas programadas en Windows Task Scheduler para ejecutar cron jobs
# USO: .\setup_cron_tasks.ps1

param(
    [string]$AppPath = "C:\app\kanban_produccion"
)

$Green = [System.ConsoleColor]::Green
$Red = [System.ConsoleColor]::Red
$Yellow = [System.ConsoleColor]::Yellow
$Cyan = [System.ConsoleColor]::Cyan

function Write-Success { param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $Green
}

function Write-Error { param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $Red
}

function Write-Info { param([string]$Message)
    Write-Host "ℹ️ $Message" -ForegroundColor $Cyan
}

function Write-Warning { param([string]$Message)
    Write-Host "⚠️ $Message" -ForegroundColor $Yellow
}

Write-Info "════════════════════════════════════════════════════════"
Write-Info "🔄 Configurando Tareas Programadas (Cron Jobs)"
Write-Info "════════════════════════════════════════════════════════"

$pythonExe = "$AppPath\.venv\Scripts\python.exe"
$taskFolder = "\KanbanProduccion\"

# Crear carpeta de tareas si no existe
Write-Info "`nCreando carpeta de tareas: $taskFolder"
$taskFolderPath = (Get-ScheduledTask | Where-Object { $_.Name -eq "KanbanProduccion" }).TaskPath
if ($null -eq $taskFolderPath) {
    try {
        $taskService = New-Object -ComObject Schedule.Service
        $taskService.Connect()
        $taskFolder = $taskService.GetFolder("\")
        $taskFolder.CreateFolder("KanbanProduccion") | Out-Null
        Write-Success "✓ Carpeta creada"
    }
    catch {
        Write-Warning "Carpeta podría ya existir, continuando..."
    }
}

# ============================================================================
# TAREA 1: Enviar Alertas WhatsApp (Cada 1 minuto)
# ============================================================================

Write-Info "`n[TAREA 1/3] Enviando Alertas WhatsApp (cada 1 minuto)..."

$taskName = "KanbanProduccion\Enviar-Alertas-WhatsApp"
$scriptPath = "$AppPath\cron_enviar_alertas.py"

if (Test-Path $scriptPath) {
    # Eliminar tarea anterior si existe
    $existingTask = Get-ScheduledTask -TaskName "Enviar-Alertas-WhatsApp" -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName "Enviar-Alertas-WhatsApp" -Confirm:$false
        Write-Info "Eliminada tarea anterior"
    }

    $action = New-ScheduledTaskAction -Execute $pythonExe -Argument $scriptPath -WorkingDirectory $AppPath
    $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 1) `
                                        -RepetitionDuration (New-TimeSpan -Days 365)
    $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
    
    Register-ScheduledTask -TaskName "Enviar-Alertas-WhatsApp" `
                          -Action $action `
                          -Trigger $trigger `
                          -Settings $settings `
                          -RunLevel Highest `
                          -ErrorAction SilentlyContinue | Out-Null
    
    Write-Success "✓ Tarea registrada: Enviar-Alertas-WhatsApp (cada 1 min)"
}
else {
    Write-Error "Script no encontrado: $scriptPath"
}

# ============================================================================
# TAREA 2: Insertar Fichas (Cada 5 minutos)
# ============================================================================

Write-Info "`n[TAREA 2/3] Insertando Fichas (cada 5 minutos)..."

$taskName2 = "KanbanProduccion\Insertar-Fichas"
$scriptPath2 = "$AppPath\cron_insertar_fichas.py"

if (Test-Path $scriptPath2) {
    $existingTask = Get-ScheduledTask -TaskName "Insertar-Fichas" -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName "Insertar-Fichas" -Confirm:$false
        Write-Info "Eliminada tarea anterior"
    }

    $action = New-ScheduledTaskAction -Execute $pythonExe -Argument $scriptPath2 -WorkingDirectory $AppPath
    $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) `
                                        -RepetitionDuration (New-TimeSpan -Days 365)
    $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

    Register-ScheduledTask -TaskName "Insertar-Fichas" `
                          -Action $action `
                          -Trigger $trigger `
                          -Settings $settings `
                          -RunLevel Highest `
                          -ErrorAction SilentlyContinue | Out-Null
    
    Write-Success "✓ Tarea registrada: Insertar-Fichas (cada 5 min)"
}
else {
    Write-Error "Script no encontrado: $scriptPath2"
}

# ============================================================================
# TAREA 3: Sincronizar Fichas Terminadas (Cada 10 minutos)
# ============================================================================

Write-Info "`n[TAREA 3/3] Sincronizando Fichas Terminadas (cada 10 minutos)..."

$taskName3 = "KanbanProduccion\Sincronizar-Fichas"
$scriptPath3 = "$AppPath\cron_sincronizar_fichas_terminadas.py"

if (Test-Path $scriptPath3) {
    $existingTask = Get-ScheduledTask -TaskName "Sincronizar-Fichas" -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName "Sincronizar-Fichas" -Confirm:$false
        Write-Info "Eliminada tarea anterior"
    }

    $action = New-ScheduledTaskAction -Execute $pythonExe -Argument $scriptPath3 -WorkingDirectory $AppPath
    $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 10) `
                                        -RepetitionDuration (New-TimeSpan -Days 365)
    $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 15)

    Register-ScheduledTask -TaskName "Sincronizar-Fichas" `
                          -Action $action `
                          -Trigger $trigger `
                          -Settings $settings `
                          -RunLevel Highest `
                          -ErrorAction SilentlyContinue | Out-Null
    
    Write-Success "✓ Tarea registrada: Sincronizar-Fichas (cada 10 min)"
}
else {
    Write-Error "Script no encontrado: $scriptPath3"
}

# ============================================================================
# VERIFICACIÓN
# ============================================================================

Write-Info "`n════════════════════════════════════════════════════════"
Write-Success "🎉 Tareas Programadas Configuradas"
Write-Info "════════════════════════════════════════════════════════"

Write-Info "`nTareas activas:"
Get-ScheduledTask -TaskPath "\KanbanProduccion\" | Select-Object -Property TaskName, State, Triggers | 
    Format-Table -AutoSize | Out-String | Write-Host

Write-Info "`nPara editar/visualizar tareas:"
Write-Info "  Abre: Windows > Task Scheduler"
Write-Info "  Navega a: Task Scheduler Library > KanbanProduccion"
Write-Info ""
Write-Info "Para deshabilitar una tarea:"
Write-Info "  Disable-ScheduledTask -TaskName 'Enviar-Alertas-WhatsApp'"
Write-Info ""
Write-Info "Para eliminar todas:"
Write-Info "  Get-ScheduledTask -TaskPath '\KanbanProduccion\' | Unregister-ScheduledTask -Confirm:$false"
Write-Info ""
Write-Info "════════════════════════════════════════════════════════"
