# 🚀 GUÍA OPERACIONAL: DESPLIEGUE A PRODUCCIÓN (192.168.39.28)

## 📋 TABLA DE CONTENIDOS
1. [Arquitectura de Producción](#arquitectura)
2. [Checklist Pre-Despliegue](#checklist-pre)
3. [Proceso de Despliegue Paso a Paso](#despliegue-pasos)
4. [Despliegue del WhatsApp Gateway](#gateway)
5. [Validación Post-Despliegue](#validacion)
6. [Troubleshooting](#troubleshooting)
7. [Mantenimiento Diario](#mantenimiento)
8. [Rollback en Caso de Error](#rollback)

---

## ARQUITECTURA `{#arquitectura}`

### Topología Producción
```
┌─────────────────────────────────────────────────────────────┐
│  SERVIDOR PRODUCCIÓN: 192.168.39.28 (Windows Server)       │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  App Kanban FastAPI                                  │  │
│  │  Puerto: 8000                                        │  │
│  │  Ruta: C:\app\kanban_produccion                     │  │
│  │  Servicio: NSSM o Task Scheduler (startup)          │  │
│  │  Logs: C:\app\kanban_produccion\logs\               │  │
│  └──────────────────────────────────────────────────────┘  │
│                       ↑                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  WhatsApp Gateway (Local)                            │  │
│  │  Puerto: 5000                                        │  │
│  │  Ruta: C:\app\whatsapp_gateway                      │  │
│  │  Servicio: NSSM o Task Scheduler (startup)          │  │
│  │  Logs: C:\app\whatsapp_gateway\logs\                │  │
│  └──────────────────────────────────────────────────────┘  │
│                       ↓                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tareas Programadas (Windows Task Scheduler)         │  │
│  │  ✓ Enviar-Alertas (cada 1 min)                       │  │
│  │  ✓ Insertar-Fichas (cada 5 min)                      │  │
│  │  ✓ Sincronizar-Fichas (cada 10 min)                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
           λ              λ              λ
           │              │              │
      Red Interna    SQL Server    Exterior
    (Users)          (192.168.     (WhatsApp
                     39.203)       API)
```

### Flujo de Datos
```
Usuario Browser (Red Interna)
    ↓
192.168.39.28:8000 (App Kanban)
    ├→ Lee/Escribe BD (SQL Server 192.168.39.203)
    ├→ Envía alertas → Gateway (localhost:5000)
    │                     ↓
    │              WhatsApp Business API
    └→ Tareas Cron (cada N minutos)
        ├→ cron_enviar_alertas.py
        ├→ cron_insertar_fichas.py
        └→ cron_sincronizar_fichas.py
```

---

## CHECKLIST PRE-DESPLIEGUE `{#checklist-pre}`

### Verificaciones de Código (En tu máquina)
- [ ] **Git**: Último commit de cambios
  ```powershell
  git status
  git add -A
  git commit -m "Pre-production deployment"
  ```

- [ ] **Tests**: Ejecutar pruebas locales
  ```powershell
  python -m pytest test_*py -v
  ```

- [ ] **Requirements**: Verificar dependencias
  ```powershell
  pip freeze > requirements.txt
  # Revisar que NO incluya: django, celery, channels (sobras de otro proyecto)
  ```

- [ ] **BD**: Ejecutar SQL updates (EN PRODUCCIÓN 192.168.39.203)
  ```sql
  # Ejecutar en SQL Server Management Studio:
  USE dbProduccion
  GO
  
  -- Desde archivo: sql_updates/vw_kb_productividad_base_updated.sql
  CREATE OR ALTER VIEW dbo.vw_kb_productividad_base AS
  [...]
  GO
  ```

### Credenciales y Secretos
- [ ] **API Keys**: Actualizar en .env.production
  - `WHATSAPP_GATEWAY_API_KEY`: Cambiar de `kanban123` a valor seguro
  - `WHATSAPP_DESTINO_DEFAULT`: Confirmar número correcto

- [ ] **SQL Server**: Verificar credenciales en DATABASE_URL
  - Usuario: `wyny`
  - Contraseña: `wyny` (REVISAR si es correcta en producción)
  - Host: `192.168.39.203`
  - BD: `dbProduccion`

### Acceso a Servidores
- [ ] **RDP a 192.168.39.28**: Credential guard, acceso admin confirmado
- [ ] **SQL Server 192.168.39.203**: Acceso desde 192.168.39.28

### Preparación de Archivos
- [ ] Crear carpeta `C:\app\` en servidor (si no existe)
- [ ] Copiar `.env.production` en la carpeta local (NO commitear credenciales)
- [ ] Confirmar acceso a repositorio Git desde servidor

---

## PROCESO DE DESPLIEGUE PASO A PASO `{#despliegue-pasos}`

### FASE 1: DESPLIEGUE DE APP KANBAN (Te toma 20 min)

#### Paso 1: Acceder al servidor
```powershell
# Desde tu máquina local
mstsc /v:192.168.39.28
# O vía SSH si está disponible
ssh usuario@192.168.39.28
```

#### Paso 2: Preparar directorios
```powershell
# En servidor 192.168.39.28
mkdir C:\app\
cd C:\app\

# Desde línea anterior, confirma permisos: ves carpeta?
ls
```

#### Paso 3: Descargar código desde Git
```powershell
cd C:\app\

# OPCIÓN A: Primera vez (clonar repositorio)
git clone https://github.com/tu-usuario/kanban-produccion.git kanban_produccion
cd kanban_produccion
git checkout main

# OPCIÓN B: Actualizar (si ya existe)
cd kanban_produccion
git pull origin main
```

#### Paso 4: Ejecutar despliegue automático
```powershell
cd C:\app\kanban_produccion

# IMPORTANTE: El script debe estar en el directorio
# Si falta: copiar deploy_to_production.ps1 desde GitHub o local

# Configurar permisos de PowerShell si es necesario
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Ejecutar despliegue
.\deploy_to_production.ps1 -Environment production -Branch main
```

**El script hará automáticamente:**
✓ Valida conexión al servidor
✓ Descarga código Git
✓ Crea/actualiza virtual environment
✓ Instala dependencias (pip install -r requirements.txt)
✓ Copia .env.production → .env
✓ Valida conexión a BD

#### Paso 5: Validar despliegue
```powershell
cd C:\app\kanban_produccion

# Ejecutar validación automática
.\validate_deployment.ps1 -ServerIP localhost -AppPort 8000
```

---

### FASE 2: DESPLIEGUE DE WHATSAPP GATEWAY (Te toma 15 min)

#### Paso 6: Desplegar Gateway en mismo servidor

```powershell
# En servidor 192.168.39.28

cd C:\app\

# Opción A: Clonar desde Git
git clone https://github.com/tu-usuario/whatsapp-gateway.git whatsapp_gateway
cd whatsapp_gateway

# Opción B: O copiar desde tu máquina
robocopy C:\Whatsapp_gateway \\192.168.39.28\c$\app\whatsapp_gateway /S /E
```

#### Paso 7: Setup del Gateway
```powershell
cd C:\app\whatsapp_gateway

# Crear venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Probar que funciona (test rápido)
python -c "from flask import Flask; print('OK')"
```

#### Paso 8: Crear servicio Windows para Gateway
```powershell
# Descargar NSSM (Non-Sucking Service Manager)
# https://nssm.cc/download
# Extraer a: C:\nssm\

$nssm = "C:\nssm\win64\nssm.exe"
$pythonExe = "C:\app\whatsapp_gateway\.venv\Scripts\python.exe"
$app = "C:\app\whatsapp_gateway\app.py"

# Instalar servicio
& $nssm install WhatsAppGateway $pythonExe $app
& $nssm set WhatsAppGateway AppDirectory "C:\app\whatsapp_gateway"
& $nssm set WhatsAppGateway AppOutput "C:\app\whatsapp_gateway\logs\gateway.log"
& $nssm set WhatsAppGateway AppError "C:\app\whatsapp_gateway\logs\error.log"

# Iniciar servicio
& $nssm start WhatsAppGateway

# Verificar estado
Get-Service -Name "WhatsAppGateway"
```

#### Paso 9: Verificar conectividad Gateway
```powershell
# Verificar que Gateway responda
curl -H "X-API-Key: kanban123" http://localhost:5000/health

# Debería mostrar: {"status": "ok"}
```

---

### FASE 3: TAREAS PROGRAMADAS (Te toma 5 min)

#### Paso 10: Configurar tareas programadas
```powershell
cd C:\app\kanban_produccion

# Ejecutar script de setup
.\setup_cron_tasks.ps1

# Script creará 3 tareas automáticamente:
# ✓ Enviar-Alertas-WhatsApp (cada 1 min)
# ✓ Insertar-Fichas (cada 5 min)
# ✓ Sincronizar-Fichas (cada 10 min)
```

---

## DESPLIEGUE DEL WHATSAPP GATEWAY `{#gateway}`

### Consideraciones Especiales

**¿Por qué en el mismo servidor?**
- DB local (sin latencia de red)
- Seguridad (no exponer API en red interna)
- Simplifica infraestructura
- Fácil de debuguear

### Configuración de Gateway para Producción

**Archivo: `C:\app\whatsapp_gateway\config.py`**
```python
# Config producción
API_PORT = 5000
DEBUG = False
LOG_LEVEL = "INFO"

# Credenciales Meta WhatsApp (obtener de https://meta.com)
META_API_TOKEN = os.getenv("META_API_TOKEN")
META_PHONE_ID = os.getenv("META_PHONE_ID")
META_API_VERSION = "v18.0"

# Logging
LOG_FILE = "logs/gateway.log"
LOG_MAX_SIZE = 10485760  # 10MB
```

**Archivo: `C:\app\whatsapp_gateway\.env`**
```env
META_API_TOKEN=EAAxxxxxxxxxxxxxxxxxx
META_PHONE_ID=123456789
WEBHOOK_SECRET=tu_webhook_secret_seguro
```

### Prueba de Gateway Post-Despliegue

```powershell
# Test 1: Gateway responde
curl -v http://localhost:5000/health

# Test 2: Enviar mensaje de prueba
curl -X POST http://localhost:5000/send-kanban `
  -H "X-API-Key: kanban123" `
  -H "Content-Type: application/json" `
  -d '{
    "telefono": "524772246411",
    "evento": "PRUEBA",
    "area": "Acabado",
    "fecha": "2026-04-15 14:30:00",
    "operario": "Test User"
  }'

# Debería responder con: {"ok": true, "status_code": 200}
```

---

## VALIDACIÓN POST-DESPLIEGUE `{#validacion}`

### Checklist de Validación

```powershell
# ❌ NO OLVIDAR ESTO:

# 1. App Kanban accesible
curl http://localhost:8000/

# 2. Gateway accesible
curl http://localhost:5000/health

# 3. Apps iniciadas con Task Scheduler o NSSM
Get-Service -Name "KanbanService" -ErrorAction SilentlyContinue
Get-Service -Name "WhatsAppGateway" -ErrorAction SilentlyContinue

# 4. Tareas cron configuradas
Get-ScheduledTask -TaskPath "\KanbanProduccion\"

# 5. BD funciona
sqlcmd -S 192.168.39.203 -U wyny -P wyny -Q "SELECT @@VERSION"

# 6. Logs sin errores
Get-Content "C:\app\kanban_produccion\logs\app_production.log" -Tail 50

# 7. WhatsApp Alert test
# Ir a http://localhost:8000/test/alerta
# Debería enviar mensaje a número en .env
```

### Test de Flujo Completo

1. **Entrar a la app:**
   ```
   Abrir: http://192.168.39.28:8000
   Ingresa como usuario de test
   ```

2. **Crear evento que genere alerta:**
   - Mover una ficha a "Acabado"
   - Debería generar evento de WhatsApp

3. **Verificar en DB:**
   ```sql
   SELECT TOP 5 * FROM kb_alertas_eventos 
   ORDER BY fecha_evento DESC
   ```

4. **Revisar logs:**
   ```powershell
   tail -f C:\app\kanban_produccion\logs\app_production.log
   tail -f C:\app\whatsapp_gateway\logs\gateway.log
   ```

---

## TROUBLESHOOTING `{#troubleshooting}`

### Problema: "Connection error to 192.168.39.203"

**Causas:**
- SQL Server no está corriendo
- Firewall bloqueando puerto 1433
- Credenciales incorrectas

**Solución:**
```powershell
# Verificar SQL Server
sqlcmd -S 192.168.39.203 -U wyny -P wyny -Q "SELECT @@VERSION"

# Verificar firewall (en servidor SQL)
netstat -ano | findstr 1433

# Verificar credenciales en .env
cat C:\app\kanban_produccion\.env | grep DATABASE_URL
```

### Problema: "WhatsApp Gateway no responde"

**Causas:**
- Servicio no iniciado
- Puerto 5000 bloqueado
- Error en credenciales Meta

**Solución:**
```powershell
# Verificar servicio
Get-Service WhatsAppGateway

# Iniciar si no está corriendo
Start-Service WhatsAppGateway

# Ver logs de error
Get-Content C:\app\whatsapp_gateway\logs\error.log -Tail 20

# Reiniciar
Restart-Service WhatsAppGateway
```

### Problema: "Tareas programadas no se ejecutan"

**Causas:**
- Tareas deshabilitadas
- Usuario sin permisos
- Ruta de script incorrecta

**Solución:**
```powershell
# Verificar estado
Get-ScheduledTask -TaskName "Enviar-Alertas-WhatsApp" | Select-Object State

# Habilitar si está deshabilitada
Enable-ScheduledTask -TaskName "Enviar-Alertas-WhatsApp"

# Ver últimas ejecuciones
Get-ScheduledTaskInfo -TaskName "Enviar-Alertas-WhatsApp"

# Ver logs de tarea
Get-EventLog -LogName "Microsoft-Windows-TaskScheduler/Operational" `
  -InstanceId 201 -After (Get-Date).AddMinutes(-30) | 
  Select-Object TimeGenerated, Message
```

---

## MANTENIMIENTO DIARIO `{#mantenimiento}`

### Checklist Diario (5 min)

```powershell
# ✓ Al inicio del turno:

# 1. Verificar servicios están corriendo
Get-Service -Name "KanbanService"
Get-Service -Name "WhatsAppGateway"

# 2. Revisar logs por errores
Get-Content "C:\app\kanban_produccion\logs\app_production.log" -Tail 20 | 
  Select-String "ERROR"

# 3. Verificar espacio en disco
Get-PSDrive C | Select-Object Name, @{n='FreeGB';e={[math]::Round($_.Free/1GB,2)}}

# 4. Prueba rápida de BD
sqlcmd -S 192.168.39.203 -U wyny -P wyny -Q "SELECT COUNT(*) FROM kb_alertas_eventos"
```

### Copias de Seguridad (Semanal)

```powershell
# Backup de logs
$date = Get-Date -Format "yyyy-MM-dd"
Copy-Item "C:\app\kanban_produccion\logs" -Destination "C:\backups\logs_$date" -Recurse

# Backup de .env (encriptado)
Copy-Item "C:\app\kanban_produccion\.env" -Destination "C:\backups\.env_$date"
```

### Rotación de Logs (Mensual)

```powershell
# Limpiar logs antiguos (>30 días)
Get-ChildItem "C:\app\kanban_produccion\logs" -Filter "*.log" | 
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
  Remove-Item -Confirm
```

---

## ROLLBACK EN CASO DE ERROR `{#rollback}`

### Si algo sale mal después de despliegue

```powershell
# OPCIÓN 1: Volver a versión anterior de código

cd C:\app\kanban_produccion

# Ver historial
git log --oneline -5

# Volver a commit anterior (ejemplo)
git reset --hard HEAD~1
git push origin main --force

# Reiniciar servicios
Restart-Service KanbanService

# Validar
.\validate_deployment.ps1
```

```powershell
# OPCIÓN 2: Reinstalar desde zero

# Detener servicios
Stop-Service KanbanService
Stop-Service WhatsAppGateway

# Respaldar carpeta actual
Move-Item "C:\app\kanban_produccion" "C:\backups\kanban_produccion_broken_$(Get-Date -Format yyyyMMdd)"

# Descargar versión anterior desde backup
Copy-Item "C:\backups\kanban_produccion_buenos" -Destination "C:\app\kanban_produccion" -Recurse

# Reiniciar
Start-Service KanbanService
Start-Service WhatsAppGateway
```

---

## NOTAS IMPORTANTES

⚠️ **ANTES DE DESPLEGAR**
- Respaldar carpeta actual: `robocopy C:\app C:\backups\app_pre_deploy`
- Avisar a usuarios que la app estará OFF durante despliegue
- Asegúrate de tener acceso R/W a `C:\app\`

⚠️ **DESPUÉS DE DESPLIEGUE**
- Revisar logs por 30 min
- Probar manualmente algunas operaciones
- Validar alertas WhatsApp llegan correctamente

⚠️ **SEGURIDAD**
- NUNCA commitear .env con credenciales reales
- Cambiar API keys regularmente
- Revisar logs por intentos fallidos

---

## CONTACTO Y ESCALATION

En caso de problemas:
1. Revisar logs (timestamps de error)
2. Ejecutar `validate_deployment.ps1`
3. Contactar a IT Ops
4. Si es crítico: rollback inmediato

---

**Última actualización:** 2026-04-15
**Versión:** 1.0
**Mantenedor:** DevOps Team
