# 🎯 TUTORIAL PASO A PASO - TU PRIMER DESPLIEGUE A PRODUCCIÓN
## Como nunca lo has hecho antes - Guía para "No Técnicos" que quieren ser "DevOps"

---

## 📍 UBICACIÓN: Dónde estamos ahora vs. dónde vamos

```
AHORA (Tu máquina):        DESPUÉS (Producción):
┌──────────────────┐       ┌──────────────────────┐
│ C:\kanban_       │       │ 192.168.39.28        │
│ produccion\      │  →→→  │ C:\app\kanban_       │
│ app/             │       │ produccion\app/      │
│ .env (local)     │       │ .env (producción)    │
└──────────────────┘       └──────────────────────┘
```

---

## ✅ FASE 1: PREPARACIÓN EN TU MÁQUINA (30 minutos)

### Paso 1.1: Abrir PowerShell EN ESTA CARPETA

```powershell
# Abre PowerShell desde VS Code (abajo)
# O presiona: Windows + X → Windows PowerShell (Admin)
# O busca: "powershell" en el menú Start

# Cuando se abra, copia este comando (pega con Ctrl+V):

cd C:\kanban_produccion

# Presiona ENTER
# Deberías ver: PS C:\kanban_produccion>
```

**¿Qué hiciste?** Entraste en la carpeta donde está tu proyecto.

---

### Paso 1.2: Crear el archivo requirements.txt

**YA ESTÁ HECHO** ✅ (lo hice por ti)

Pero verifiquemos que esté correcto:

```powershell
# En la misma PowerShell, escribe:

cat requirements.txt

# Deberías ver un listado de dependencias como:
# fastapi==0.135.1
# uvicorn==0.42.0
# sqlalchemy==2.0.48
# [...]
```

**¿Qué es esto?** Un archivo que dice "necesito estos paquetes Python". Asegura que en el servidor instale exactamente lo mismo.

---

### Paso 1.3: Verificar .env.production

```powershell
# Abre el archivo
code .env.production

# Se abrirá en VS Code
```

**Dentro del archivo, verás:**

```env
WHATSAPP_GATEWAY_API_KEY=kanban123_CHANGE_IN_PRODUCTION
WHATSAPP_GATEWAY_URL=http://localhost:5000
# etc.
```

**ACCIÓN REQUERIDA:** 
- Cambia `kanban123_CHANGE_IN_PRODUCTION` por algo único y seguro, ej: `prod_gateway_2026_4_seguro123`
- Guardar: `Ctrl+S`

**Ejemplo cómo debe quedar:**
```env
WHATSAPP_GATEWAY_API_KEY=prod_gateway_2026_4_seguro123
```

---

### Paso 1.4: Verificar credenciales SQL Server

En el mismo archivo `.env.production`, revisa esta línea:

```env
DATABASE_URL=mssql+pyodbc://wyny:wyny@192.168.39.203/dbProduccion?driver=ODBC+Driver+17+for+SQL+Server
```

**PREGUNTA:** ¿Las credenciales SQL son `wyny:wyny`?

- ✅ **SÍ** → Todo bien, no cambies nada
- ❌ **NO** → Dime cuál es el usuario/contraseña correcto

---

### Paso 1.5: Hacer Commit a Git

Vuelve a PowerShell y ejecuta:

```powershell
# Ver qué cambió
git status

# Deberías ver algo como:
# modified:   requirements.txt
# new file:   deploy_to_production.ps1
# etc.
```

Ahora agrega los cambios:

```powershell
# Agregar todos los archivos nuevos
git add requirements.txt
git add deploy_to_production.ps1
git add setup_cron_tasks.ps1
git add validate_deployment.ps1
git add run_production.py
git add DEPLOYMENT_PRODUCTION.md
git add QUICK_START_DEPLOYMENT.md
git add DEPLOYMENT_CHECKLIST.txt
git add ANTES_DESPUES_RESUMEN.md

# NO AGREGAR .env.production (tiene credenciales)

# Crear el commit
git commit -m "🚀 Preparación despliegue a producción - Scripts automáticos"

# Ver si salió bien
git log --oneline -5

# Deberías ver tu commit arriba
```

Sube a GitHub:

```powershell
# Enviar a GitHub
git push origin main

# Te pedirá login si no está configurado
```

**¿Qué hiciste?** Guardaste todos los cambios en GitHub. Así el servidor puede descargarlos.

---

## 🖥️ FASE 2: ACCESO AL SERVIDOR (5 minutos)

### Paso 2.1: Conectar RDP

Necesitas acceso remoto al servidor 192.168.39.28.

**Opción A: Si estás en WINDOWS LOCAL**

Presiona `Windows + R`, escribe:

```
mstsc
```

Se abrirá "Conexión a Escritorio Remoto". Escribe:

```
Nombre del equipo: 192.168.39.28
Usuario: [tu usuario admin]
Contraseña: [tu password]
```

Clic en "Conectar".

**Opción B: Si tienes SSH**

```powershell
ssh usuario@192.168.39.28
# Te pedirá contraseña
```

---

### Paso 2.2: Confirmar acceso

Una vez conectado al servidor (192.168.39.28), deberías ver el escritorio del servidor.

Abre PowerShell en el servidor:

```powershell
# Windows + X → Windows PowerShell (Admin)
# O similar
```

Verifica que estés en el servidor:

```powershell
hostname

# Debería mostrar el nombre del servidor (probablemente algo como: PROD-SERVER)
```

✅ **Si llegaste hasta aquí, tenemos acceso.**

---

## 📦 FASE 3: CREAR ESTRUCTURA DE CARPETAS (3 minutos)

En la PowerShell del servidor, ejecuta:

```powershell
# Crear la carpeta de aplicaciones
mkdir C:\app

# Verificar que se creó
dir C:\

# Deberías ver carpeta "app" (azul, es carpeta)
```

**¿Qué hiciste?** Preparaste una carpeta (`C:\app`) donde vivirán tus 2 aplicaciones (Kanban + Gateway).

---

## 🚀 FASE 4: DESCARGAR Y DESPLEGAR APP KANBAN (45 minutos)

### Paso 4.1: Descargar el código desde Git

```powershell
# Entrar a la carpeta de apps
cd C:\app

# Descargar el repositorio
git clone https://github.com/tu-usuario/kanban-produccion.git kanban_produccion

# Esperar a que termine (toma 10-30 segundos)
# Deberías ver: "Cloning into 'kanban_produccion'..."
# Y al final: "done"

# Entrar en la carpeta descargada
cd kanban_produccion

# Verificar que todo se descargó bien
dir

# Deberías ver: app/, requirements.txt, deploy_to_production.ps1, etc.
```

**¿Qué hiciste?** Descargaste el código de tu app desde GitHub al servidor.

---

### Paso 4.2: Ejecutar el SCRIPT DE DESPLIEGUE AUTOMÁTICO

Este es el paso más importante. **EL SCRIPT HACE TODO SOLO.**

```powershell
# Asegurate de estar en: C:\app\kanban_produccion
# Verificar:
pwd

# Si dice "C:\app\kanban_produccion" → bien
# Si no → cd C:\app\kanban_produccion

# EJECUTAR EL SCRIPT DE DESPLIEGUE
.\deploy_to_production.ps1

# El script pedirá permisos para ejecutar
# Si dice "No execution policy": ejecuta esto primero:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Luego vuelve a ejecutar:
.\deploy_to_production.ps1
```

**¿Qué hace el script?**

```
✓ Valida conexión al servidor
✓ Descarga código Git
✓ Crea Python Virtual Environment (.venv)
✓ Instala dependencias (pip install -r requirements.txt)
✓ Copia .env.production → .env
✓ Valida conexión a BD
✓ Muestra resumen
```

**Espera de 5-10 minutos mientras el script trabaja.**

**Verás output como:**

```
✅ Servidor 192.168.39.28 alcanzable
ℹ️  Preparando carpetas...
✅ Carpeta app existe: C:\app\kanban_produccion
ℹ️  Actualizando código desde Git...
✓ Código actualizado
ℹ️  Configurando Python Virtual Environment...
✓ Venv activado
ℹ️  Instalando dependencias Python...
✓ Dependencias instaladas
[... más output ...]
✅ 🎉 DESPLIEGUE COMPLETADO EXITOSAMENTE
```

**¿Qué hiciste?** Descargaste, preparaste y instalaste tu app en el servidor SIN hacer nada manual.

---

### Paso 4.3: VALIDAR QUE TODO FUNCIONA

Ahora verifica que el despliegue fue exitoso:

```powershell
# Asegurate de estar en: C:\app\kanban_produccion
cd C:\app\kanban_produccion

# Ejecutar validation
.\validate_deployment.ps1

# Espera 30 segundos
```

**Deberías ver algo como:**

```
ℹ️ [TEST 1/10] Validando requirements.txt...
✅ requirements.txt existe
ℹ️ [TEST 2/10] Validando archivo .env...
✅ Archivo .env existe
✅ Variables de entorno configuradas
[... más tests ...]
✅ 🎉 ¡DESPLIEGUE VALIDADO CORRECTAMENTE!
✅ Pruebas exitosas: 9/10
```

**Si ves ✅ 9 o 10 de 10** → ¡Perfecto!

**Si ves ❌ errores:**
1. Anota el número de test que falló
2. Scroll up y lee el error
3. Común: "No puedo conectar a BD" → Revisar DATABASE_URL en .env
4. Común: "Falta paquete Python" → El pip install no terminó bien

---

## 🔔 FASE 5: DESPLEGAR WHATSAPP GATEWAY (30 minutos)

### Paso 5.1: Descargar el código del Gateway

```powershell
# Vuelve a la carpeta de apps
cd C:\app

# Descargar el repositorio del gateway
git clone https://github.com/tu-usuario/whatsapp-gateway.git whatsapp_gateway

# Esperar que termine (10-30 seg)

# Entrar en la carpeta
cd whatsapp_gateway

# Verificar que está todo
dir

# Deberías ver: app.py, requirements.txt, config.py, etc.
```

**¿Qué hiciste?** Descargaste el código de la app WhatsApp en el servidor.

---

### Paso 5.2: Crear Virtual Environment para Gateway

```powershell
# Asegurate de estar en: C:\app\whatsapp_gateway
cd C:\app\whatsapp_gateway

# Crear venv
python -m venv .venv

# Esperar 20-30 segundos mientras se crea
```

**¿Qué es venv?** Un "entorno aislado" de Python. Cada app tiene el suyo.

---

### Paso 5.3: Activar venv e instalar dependencias

```powershell
# Activar el venv
.\.venv\Scripts\Activate.ps1

# Deberías ver: "(.venv) PS C:\app\whatsapp_gateway"

# Instalar dependencias
pip install -r requirements.txt

# Esperar 1-2 minutos mientras descarga paquetes
# Al final debería decir: "Successfully installed ..."
```

---

### Paso 5.4: Probar que el Gateway funciona

```powershell
# Probar que Python puede importar la app
python -c "from app import app; print('OK')"

# Si ves "OK" → Perfecto
# Si ves error → Hay problema con dependencias
```

---

### Paso 5.5: Crear Servicio Windows para el Gateway

Aquí lo haremos "simple" al principio:

La opción profesional es NSSM, pero es más complejo. Por ahora, haremos que se inicie con Task Scheduler.

**Abre Task Scheduler:**

```powershell
# Escribe en PowerShell:
taskschd.msc

# Se abrirá la ventana de Task Scheduler (gráfico)
```

**Clic derecho en "Task Scheduler Library" → "Create Basic Task":**

```
Nombre: WhatsApp-Gateway-Startup
Desencadenador: "At Startup" (al iniciar)
Acción:
  Programa: C:\app\whatsapp_gateway\.venv\Scripts\python.exe
  Argumentos: C:\app\whatsapp_gateway\app.py
  Iniciar en: C:\app\whatsapp_gateway
```

✅ Clic en "OK"

---

### Paso 5.6: Iniciar el Gateway manualmente (Test)

```powershell
# En PowerShell, asegúrate de estar en la carpeta del gateway
cd C:\app\whatsapp_gateway
.\.venv\Scripts\Activate.ps1

# Iniciar la app
python app.py

# Deberías ver algo como:
# WARNING: This is a development server. Do not use it in production.
# Running on: http://127.0.0.1:5000/
```

**Ahora el gateway está CORRIENDO en puerto 5000.**

Para probarlo, **ABRE OTRA POWERSHELL** (sin cerrar esta):

```powershell
# En la NUEVA PowerShell:
curl http://localhost:5000/health

# Deberías ver: {"status":"ok"}
```

✅ **¡El Gateway funciona!**

Vuelve a la primera PowerShell y presiona `Ctrl+C` para detenerlo:

```powershell
# En la PowerShell donde corre Gateway, presiona:
Ctrl+C

# Debería decir: "KeyboardInterrupt"
# Y volver al prompt
```

---

## ⚙️ FASE 6: CONFIGURAR TAREAS PROGRAMADAS CRON (10 minutos)

Vuelve a la PowerShell del servidor:

```powershell
# Vuelve a la carpeta de Kanban
cd C:\app\kanban_produccion

# Ejecutar script de setup
.\setup_cron_tasks.ps1

# El script creará 3 tareas automáticamente
```

**¿Qué hace?**

Crea 3 tareas que se ejecutan cada X minutos:

```
✓ Enviar-Alertas-WhatsApp     (cada 1 minuto)
✓ Insertar-Fichas             (cada 5 minutos)
✓ Sincronizar-Fichas          (cada 10 minutos)
```

Verifica que se crearon:

```powershell
# Ver tareas creadas
Get-ScheduledTask -TaskPath "\KanbanProduccion\" | Select-Object TaskName, State

# Deberías ver:
# TaskName                          State
# ----                              -----
# Enviar-Alertas-WhatsApp         Ready
# Insertar-Fichas                 Ready
# Sincronizar-Fichas              Ready
```

✅ **Perfecto, las 3 tareas están creadas.**

---

## ✅ FASE 7: PRUEBAS INICIALES (20 minutos)

### Paso 7.1: Verificar que todo está corriendo

```powershell
# 1. ¿App Kanban responde?
curl http://localhost:8000

# Deberías ver HTML o error 404 (pero que responde)

# 2. ¿Gateway responde?
curl http://localhost:5000/health

# Deberías ver: {"status":"ok"}

# 3. ¿Se puede conectar a BD?
sqlcmd -S 192.168.39.203 -U wyny -P wyny -Q "SELECT @@VERSION"

# Deberías ver la versión de SQL Server
```

---

### Paso 7.2: Acceder a la APP desde navegador

En el navegador del servidor (o desde tu máquina):

```
http://192.168.39.28:8000
```

Deberías ver tu aplicación Kanban cargada.

✅ **¡Funciona!**

---

### Paso 7.3: Revisar Logs

```powershell
# Ver últimas líneas del log
Get-Content C:\app\kanban_produccion\logs\app_production.log -Tail 20

# Buscar errores (no debería haber)
Get-Content C:\app\kanban_produccion\logs\app_production.log | Select-String "ERROR"

# Si sale vacío → sin errores ✅
```

---

## 🎉 FASE 8: RESUMEN - YA ESTÁ EN PRODUCCIÓN

**Lo que hiciste:**

```
✅ Descargaste código desde Git
✅ Instalaste dependencias Python
✅ Configuraste variables de entorno
✅ Desplegaste app Kanban (puerto 8000)
✅ Desplegaste WhatsApp Gateway (puerto 5000)
✅ Configuraste 3 tareas cron automáticas
✅ Validaste conectividad
✅ Probaste desde navegador
```

**Dónde está todo:**

```
C:\app\
├── kanban_produccion/
│   ├── app/
│   ├── .venv/
│   ├── .env
│   ├── logs/
│   └── run_production.py
│
└── whatsapp_gateway/
    ├── app/
    ├── .venv/
    ├── .env
    └── app.py
```

**URLs de acceso:**

```
App Kanban:       http://192.168.39.28:8000
Gateway Health:   http://192.168.39.28:5000/health
BD SQL Server:    192.168.39.203
```

---

## 🆘 PROBLEMAS COMUNES Y SOLUCIONES

### ❌ "No puedo conectar a BD"

```powershell
# Revisar credenciales en .env
cat C:\app\kanban_produccion\.env | findstr DATABASE_URL

# Debería mostrar:
# mssql+pyodbc://wyny:wyny@192.168.39.203/dbProduccion

# Si ve diferente, editar archivo:
notepad C:\app\kanban_produccion\.env

# Y actualizar la línea correctamente
```

---

### ❌ "ERROR: pip install no funciona"

```powershell
# Verificar que Python está instalado
python --version

# Debería mostrar: Python 3.9.x o superior

# Si no aparece Python, ir a https://python.org y descargar

# Verificar que pip también está
pip --version
```

---

### ❌ "No puedo conectar con RDP"

```powershell
# Verificar IP del servidor es correcta
ping 192.168.39.28

# Si responde → problema es credenciales/firewall
# Si no responde → servidor no está en esa IP o está apagado
```

---

### ❌ "El Gateway no inicia"

```powershell
# Ver logs de error
cd C:\app\whatsapp_gateway
Get-Content logs/error.log -Tail 20

# Error común: Puerto 5000 ya está en uso
# Solución: netstat -ano | findstr :5000
#          Matar proceso o cambiar puerto
```

---

## 📋 CHECKLIST RÁPIDO

Imprime esto y marca conforme avances:

```
PRE-DESPLIEGUE:
[ ] .env.production actualizado
[ ] Código pushado a GitHub

SERVIDOR:
[ ] RDP conectado a 192.168.39.28
[ ] mkdir C:\app
[ ] git clone kanban
[ ] deploy_to_production.ps1 ejecutado
[ ] validate_deployment.ps1 pasó (9-10/10)

GATEWAY:
[ ] git clone whatsapp_gateway
[ ] venv creado e instalado
[ ] python app.py funciona (curl health = ok)

TAREAS CRON:
[ ] setup_cron_tasks.ps1 ejecutado
[ ] 3 tareas visibles en Task Scheduler

VALIDACIÓN FINAL:
[ ] curl http://localhost:8000 → responde
[ ] curl http://localhost:5000/health → {"status":"ok"}
[ ] Acceso en navegador: http://192.168.39.28:8000
[ ] Logs sin errores críticos

✅ DESPLIEGUE EXITOSO
```

---

## 🎓 CONCEPTO: ¿Qué pasó?

**Lo que hiciste fue:**

1. **Copiar** tu código desde tu PC al servidor (git clone)
2. **Instalar** las dependencias de Python en el servidor (pip install)
3. **Configurar** variables de entorno (.env)
4. **Iniciar** dos aplicaciones:
   - App Kanban (FastAPI en puerto 8000)
   - Gateway WhatsApp (Flask en puerto 5000)
5. **Programar** 3 trabajos automáticos (cron jobs)
6. **Validar** que todo funciona

**Ahora:**

- Usuarios en la red interna acceden a `http://192.168.39.28:8000`
- Se conecta a BD SQL Server en `192.168.39.203`
- Cada 1 minuto manda alertas a WhatsApp
- Todo funciona 24/7

**Si hace reboot el servidor:**
- Las tareas cron se iniciarán automáticamente (Task Scheduler)
- La app Kanban se iniciará automáticamente (vía tarea programada)
- El Gateway se iniciará automáticamente (vía tarea programada en startup)

---

## 🚨 ¿ALGO SALIÓ MAL?

Si algo no funciona:

1. **Revisa el paso que falló** (arriba hay checklist)
2. **Lee el mensaje de error** completo
3. **Copia el error en Google** (95% de problemas ya tienen solución en StackOverflow)
4. **Consulta DEPLOYMENT_PRODUCTION.md sección "Troubleshooting"**
5. **Rollback (volver atrás):**

```powershell
# Detener todo
Stop-Service KanbanService -ErrorAction SilentlyContinue

# Restaurar backup (previamente hiciste):
cd C:\
dir backups\

# Si existe backup:
robocopy backups\app_pre_deploy C:\app /S /E

# Reiniciar
Start-Service KanbanService
```

---

## 🎊 ¿LLEGASTE HASTA AQUÍ?

**¡FELICIDADES! 🎉**

Ya hiciste tu primer despliegue profesional a producción. Eso es algo que muchos devs nunca hacen.

Ahora tienes:
- ✅ App en producción
- ✅ Gateway en producción
- ✅ Alertas automáticas
- ✅ Escalabilidad para el futuro

**Próximos pasos opcionales (después):**
- Agregar monitoreo (Slack alerts si app cae)
- Agregar CI/CD (despliegue automático)
- Agregar staging environment (test antes de prod)

---

**¿Preguntas?** Estoy aquí para lo que necesites. 🚀
