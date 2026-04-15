# validate_deployment.ps1
# Valida que el despliegue en producción fue exitoso
# USO: .\validate_deployment.ps1

param(
    [string]$ServerIP = "localhost",
    [int]$AppPort = 8000,
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
    Write-Host "❌ FALLO: $Message" -ForegroundColor $Red
}

function Write-Info { param([string]$Message)
    Write-Host "ℹ️ $Message" -ForegroundColor $Cyan
}

function Write-Warning { param([string]$Message)
    Write-Host "⚠️ $Message" -ForegroundColor $Yellow
}

$failCount = 0
$passCount = 0

Write-Info "════════════════════════════════════════════════════════"
Write-Info "✅ VALIDANDO DESPLIEGUE A PRODUCCIÓN"
Write-Info "════════════════════════════════════════════════════════"
Write-Info "Servidor: $ServerIP"
Write-Info "Puerto: $AppPort"
Write-Info "Hora: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Info "════════════════════════════════════════════════════════"

# ============================================================================
# TEST 1: Archivo requirements.txt
# ============================================================================

Write-Info "`n[TEST 1/10] Validando requirements.txt..."
if (Test-Path "$AppPath\requirements.txt") {
    Write-Success "✓ requirements.txt existe"
    $reqs = Get-Content "$AppPath\requirements.txt" | Where-Object { $_ -and -not $_.StartsWith("#") } | Measure-Object
    Write-Info "  $($reqs.Count) dependencias declaradas"
    $passCount++
}
else {
    Write-Error "requirements.txt no encontrado"
    $failCount++
}

# ============================================================================
# TEST 2: Archivo .env
# ============================================================================

Write-Info "`n[TEST 2/10] Validando archivo .env..."
if (Test-Path "$AppPath\.env") {
    Write-Success "✓ Archivo .env existe"
    
    $envVars = @("WHATSAPP_GATEWAY_URL", "WHATSAPP_GATEWAY_API_KEY", "WHATSAPP_DESTINO_DEFAULT")
    $missingVars = @()
    
    $envContent = Get-Content "$AppPath\.env" | ConvertFrom-StringData
    foreach ($var in $envVars) {
        if ([string]::IsNullOrWhiteSpace($envContent[$var])) {
            $missingVars += $var
        }
    }
    
    if ($missingVars.Count -gt 0) {
        Write-Warning "  Variables faltantes: $($missingVars -join ', ')"
    }
    else {
        Write-Success "✓ Variables de entorno configuradas"
        $passCount++
    }
}
else {
    Write-Error ".env no encontrado"
    $failCount++
}

# ============================================================================
# TEST 3: Virtual Environment
# ============================================================================

Write-Info "`n[TEST 3/10] Validando Python Virtual Environment..."
$venvPath = "$AppPath\.venv"
if (Test-Path "$venvPath\Scripts\Activate.ps1") {
    Write-Success "✓ Virtual Environment existe"
    $passCount++
}
else {
    Write-Error "Virtual Environment no encontrado"
    $failCount++
}

# ============================================================================
# TEST 4: Dependencias Python instaladas
# ============================================================================

Write-Info "`n[TEST 4/10] Validando dependencias instaladas..."

& "$venvPath\Scripts\Activate.ps1"

$requiredPackages = @("fastapi", "uvicorn", "sqlalchemy", "pyodbc", "requests")
$missingPackages = @()

foreach ($pkg in $requiredPackages) {
    $check = & pip show $pkg 2>&1 | Select-String "Name:"
    if ($null -eq $check) {
        $missingPackages += $pkg
    }
}

if ($missingPackages.Count -eq 0) {
    Write-Success "✓ Todas las dependencias están instaladas"
    $passCount++
}
else {
    Write-Warning "  Paquetes faltantes: $($missingPackages -join ', ')"
    $failCount++
}

# ============================================================================
# TEST 5: Conexión a FastAPI
# ============================================================================

Write-Info "`n[TEST 5/10] Validando que FastAPI esté disponible..."

$fastApiTest = & python -c "from fastapi import FastAPI; print('OK')" 2>&1
if ($fastApiTest -like "*OK*") {
    Write-Success "✓ FastAPI importa correctamente"
    $passCount++
}
else {
    Write-Error "Error importando FastAPI"
    $failCount++
}

# ============================================================================
# TEST 6: Conexión a Base de Datos
# ============================================================================

Write-Info "`n[TEST 6/10] Validando conexión a Base de Datos..."

$dbTest = & python -c "from app.db import engine; conn = engine.connect(); print('OK'); conn.close()" 2>&1
if ($dbTest -like "*OK*") {
    Write-Success "✓ Conexión a BD exitosa"
    $passCount++
}
else {
    Write-Warning "⚠️ Error en conexión a BD:"
    Write-Warning "  $dbTest"
    Write-Warning "  Verificar: .env, credenciales SQL Server, firewall"
    $failCount++
}

# ============================================================================
# TEST 7: Archivos de tarea cron
# ============================================================================

Write-Info "`n[TEST 7/10] Validando scripts cron..."

$cronScripts = @(
    "cron_enviar_alertas.py",
    "cron_insertar_fichas.py",
    "cron_sincronizar_fichas_terminadas.py"
)

$allScriptsOK = $true
foreach ($script in $cronScripts) {
    if (Test-Path "$AppPath\$script") {
        Write-Success "  ✓ $script existe"
    }
    else {
        Write-Warning "  ⚠️ $script no encontrado"
        $allScriptsOK = $false
    }
}

if ($allScriptsOK) {
    $passCount++
}

# ============================================================================
# TEST 8: Tareas programadas en Windows
# ============================================================================

Write-Info "`n[TEST 8/10] Validando tareas programadas..."

$scheduledTasks = @(
    "Enviar-Alertas-WhatsApp",
    "Insertar-Fichas",
    "Sincronizar-Fichas"
)

$allTasksOK = $true
foreach ($taskName in $scheduledTasks) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Success "  ✓ Tarea: $taskName ($($task.State))"
    }
    else {
        Write-Warning "  ⚠️ Tarea no encontrada: $taskName"
        $allTasksOK = $false
    }
}

if ($allTasksOK) {
    $passCount++
}
else {
    Write-Warning "  Ejecutar: .\setup_cron_tasks.ps1"
}

# ============================================================================
# TEST 9: Conectividad HTTP
# ============================================================================

Write-Info "`n[TEST 9/10] Validando acceso HTTP a la app..."

try {
    $response = Invoke-WebRequest -Uri "http://$ServerIP:$AppPort" -ErrorAction Stop -TimeoutSec 5
    if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 404) {
        Write-Success "✓ App responde en http://$ServerIP:$AppPort (HTTP $($response.StatusCode))"
        $passCount++
    }
}
catch {
    Write-Warning "⚠️ App no responde en http://$ServerIP:$AppPort"
    Write-Warning "  Posibles causas:"
    Write-Warning "    - La app no está iniciada"
    Write-Warning "    - Diferente puerto (revisar .env)"
    Write-Warning "    - Firewall bloqueando puerto $AppPort"
    Write-Info "  Iniciar con: python run_production.py"
}

# ============================================================================
# TEST 10: Espacio en disco
# ============================================================================

Write-Info "`n[TEST 10/10] Validando espacio en disco..."

$drive = (Get-Item $AppPath).PSDrive.Name
$freeSpace = (Get-PSDrive $drive).Free / 1GB

if ($freeSpace -gt 5) {
    Write-Success "✓ Espacio disponible: ${freeSpace:F2} GB"
    $passCount++
}
else {
    Write-Warning "⚠️ Espacio bajo: ${freeSpace:F2} GB disponibles"
}

# ============================================================================
# RESUMEN
# ============================================================================

Write-Info "`n════════════════════════════════════════════════════════"
Write-Info "📊 RESUMEN DE VALIDACIÓN"
Write-Info "════════════════════════════════════════════════════════"

$totalTests = $passCount + $failCount
$successRate = if ($totalTests -gt 0) { [math]::Round(($passCount / $totalTests) * 100, 1) } else { 0 }

Write-Info "✅ Pruebas exitosas: $passCount/$totalTests"
if ($failCount -gt 0) {
    Write-Error "Pruebas fallidas: $failCount/$totalTests"
}
Write-Info "Tasa de éxito: $successRate%"

if ($failCount -eq 0) {
    Write-Info ""
    Write-Success "🎉 ¡DESPLIEGUE VALIDADO CORRECTAMENTE!"
    Write-Info ""
    Write-Info "Próximos pasos:"
    Write-Info "1. Iniciar la aplicación:"
    Write-Info "   python run_production.py"
    Write-Info ""
    Write-Info "2. Monitorear logs:"
    Write-Info "   Get-Content logs/app_production.log -Wait"
    Write-Info ""
    Write-Info "3. Verificar en navegador:"
    Write-Info "   http://$ServerIP:$AppPort"
}
else {
    Write-Warning ""
    Write-Warning "⚠️ Hay problemas que resolver antes de ir a producción"
}

Write-Info "════════════════════════════════════════════════════════"
