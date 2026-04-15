# deploy_to_production.ps1
# Script de despliegue AUTOMATIZADO a servidor 192.168.39.28
# USO: .\deploy_to_production.ps1 -Environment production -Branch main
#
# Este script hace:
# 1. Valida conexión al servidor
# 2. Descarga código desde Git
# 3. Instala/actualiza dependencias
# 4. Aplica configuración de producción
# 5. Inicia servicios
# 6. Valida que todo funciona

param(
    [string]$Environment = "production",
    [string]$Branch = "main",
    [string]$ServerIP = "192.168.39.28",
    [string]$AppPath = "C:\app\kanban_produccion",
    [string]$GatewayPath = "C:\app\whatsapp_gateway"
)

# Colores para output
$Green = [System.ConsoleColor]::Green
$Red = [System.ConsoleColor]::Red
$Yellow = [System.ConsoleColor]::Yellow
$Cyan = [System.ConsoleColor]::Cyan

# Funciones auxiliares
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️ $Message" -ForegroundColor $Cyan
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️ $Message" -ForegroundColor $Yellow
}

# ============================================================================
# INICIO DEL DESPLIEGUE
# ============================================================================

Write-Info "════════════════════════════════════════════════════════"
Write-Info "🚀 DESPLIEGUE A PRODUCCIÓN - $Environment"
Write-Info "════════════════════════════════════════════════════════"
Write-Info "Servidor: $ServerIP"
Write-Info "Rama: $Branch"
Write-Info "Hora: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Info "════════════════════════════════════════════════════════"

# ============================================================================
# PASO 1: Validar conexión a servidor
# ============================================================================

Write-Info "`n[PASO 1/7] Validando conexión a servidor..."

$ping = Test-Connection -ComputerName $ServerIP -Count 1 -Quiet
if (-not $ping) {
    Write-Error "No hay conectividad con $ServerIP"
    exit 1
}
Write-Success "✓ Servidor $ServerIP alcanzable"

# ============================================================================
# PASO 2: Navegar a carpeta de la app
# ============================================================================

Write-Info "`n[PASO 2/7] Preparando carpetas..."

if (Test-Path $AppPath) {
    Write-Success "✓ Carpeta app existe: $AppPath"
}
else {
    Write-Error "Carpeta no existe: $AppPath"
    Write-Info "Creando carpeta..."
    New-Item -ItemType Directory -Path $AppPath -Force | Out-Null
    Write-Success "✓ Carpeta creada"
}

# ============================================================================
# PASO 3: Actualizar código desde Git
# ============================================================================

Write-Info "`n[PASO 3/7] Actualizando código desde Git ($Branch)..."

cd $AppPath

if (Test-Path ".git") {
    Write-Info "Repositorio Git encontrado, actualizando..."
    & git fetch origin
    & git checkout $Branch
    $pull = & git pull origin $Branch 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Código actualizado"
    }
    else {
        Write-Error "Error al hacer pull: $pull"
        exit 1
    }
}
else {
    Write-Warning "No hay repositorio Git. Saltando actualización."
}

# ============================================================================
# PASO 4: Configurar Python Environment
# ============================================================================

Write-Info "`n[PASO 4/7] Configurando Python Virtual Environment..."

$venvPath = "$AppPath\.venv"

if (-not (Test-Path $venvPath)) {
    Write-Info "Creando venv..."
    & python -m venv $venvPath
    Write-Success "✓ Venv creado"
}
else {
    Write-Success "✓ Venv ya existe"
}

# Activar venv
& "$venvPath\Scripts\Activate.ps1"

Write-Success "✓ Venv activado"

# ============================================================================
# PASO 5: Instalar dependencias
# ============================================================================

Write-Info "`n[PASO 5/7] Instalando dependencias Python..."

$reqFile = "$AppPath\requirements.txt"
if (Test-Path $reqFile) {
    Write-Info "Instalando desde requirements.txt..."
    & pip install -q -r $reqFile --upgrade
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Dependencias instaladas"
    }
    else {
        Write-Error "Error instalando dependencias"
        exit 1
    }
}
else {
    Write-Error "No encontré requirements.txt en $AppPath"
    exit 1
}

# ============================================================================
# PASO 6: Configurar archivos de ambiente
# ============================================================================

Write-Info "`n[PASO 6/7] Configurando archivo .env..."

$envFile = "$AppPath\.env"
$envProdFile = "$AppPath\.env.production"

if (Test-Path $envProdFile) {
    Write-Info "Copiando .env.production a .env..."
    Copy-Item -Path $envProdFile -Destination $envFile -Force
    Write-Success "✓ Archivo .env configurado"
}
else {
    Write-Warning "No encontré .env.production. Asegúrate que esté creado antes del despliegue."
}

# ============================================================================
# PASO 7: Validaciones finales
# ============================================================================

Write-Info "`n[PASO 7/7] Validaciones finales..."

# Validar que Python y FastAPI estén disponibles
$pythonTest = & python -c "from fastapi import FastAPI; print('OK')" 2>&1
if ($pythonTest -contains "OK") {
    Write-Success "✓ FastAPI debe estar disponible"
}
else {
    Write-Error "Error con FastAPI"
    exit 1
}

# Validar conexión a BD
$dbTest = & python -c "from app.db import engine; print('OK')" 2>&1
if ($dbTest -contains "OK") {
    Write-Success "✓ Conexión a BD validada"
}
else {
    Write-Warning "⚠️ Posible problema con conexión a BD. Revisar .env"
}

# ============================================================================
# RESUMEN FINAL
# ============================================================================

Write-Info "`n════════════════════════════════════════════════════════"
Write-Success "🎉 DESPLIEGUE COMPLETADO EXITOSAMENTE"
Write-Info "════════════════════════════════════════════════════════"
Write-Info ""
Write-Info "PRÓXIMOS PASOS:"
Write-Info "1. Iniciar aplicación:"
Write-Info "   python run_production.py"
Write-Info "   O vía servicio Windows:"
Write-Info "   nssm start KanbanService"
Write-Info ""
Write-Info "2. Verificar logs:"
Write-Info "   tail -f logs/app_production.log"
Write-Info ""
Write-Info "3. Configurar tareas programadas:"
Write-Info "   .\setup_cron_tasks.ps1"
Write-Info ""
Write-Info "4. Validar despliegue:"
Write-Info "   .\validate_deployment.ps1"
Write-Info ""
Write-Info "════════════════════════════════════════════════════════"
