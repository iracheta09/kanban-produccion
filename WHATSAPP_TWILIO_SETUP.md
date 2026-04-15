# Sistema de Alertas WhatsApp con Twilio - DOCUMENTACIÓN

## 🎯 Resumen

Sistema completo que envía alertas automáticas del Kanban por WhatsApp usando **Twilio**.

### ✅ Características

- ✅ Envía mensajes a cualquier número sin verificación previa
- ✅ Anti-spam automático (5 segundos mínimo entre eventos)
- ✅ Reintentos automáticos (hasta 3 intentos)
- ✅ Ejecuta cada minuto automáticamente
- ✅ Almacena estado de envío en BD
- ✅ Escalable a múltiples números destino

---

## 📁 Archivos Creados

### 1. **config_twilio.py**
   - Configuración de credenciales de Twilio
   - Lista de números destino
   - Parámetros de reintentos y anti-spam

### 2. **whatsapp_service.py**
   - Servicio central para enviar mensajes
   - Función `enviar_alerta_whatsapp()` - envía a un número específico
   - Función `enviar_alerta_batch()` - envía múltiples mensajes

### 3. **cron_whatsapp_twilio.py**
   - Lee eventos pendientes de la BD
   - Envía automáticamente por WhatsApp
   - Actualiza estado de envío en BD
   - Se ejecuta cada minuto

### 4. **test_twilio_completo.py**
   - Script de prueba
   - Crea evento → espera → envía
   - Valida todo el sistema

### 5. **crear_tarea_scheduler.bat**
   - Script para crear tarea automatizada
   - Ejecutar como Administrador

---

## 🚀 Uso

### Opción 1: Prueba Manual
```bash
python test_twilio_completo.py
```

### Opción 2: Configurar Automático (Task Scheduler)

**Windows (Admin):**
```bash
# Ejecutar como Administrator
crear_tarea_scheduler.bat
```

Verifica en Task Scheduler → "Enviar Alertas Kanban WhatsApp"

### Opción 3: Envío Directo desde Código
```python
from whatsapp_service import enviar_alerta_whatsapp

# Enviar a número específico
enviar_alerta_whatsapp("Hola, esto es una prueba", "+5214777301376")

# Enviar a todos los números configurados
enviar_alerta_whatsapp("Alerta del Kanban")
```

---

## 📊 Base de Datos

Los eventos se almacenan en `kb_alertas_eventos` con campos:

- `id_alerta_evento` - ID único
- `tipo_evento` - Tipo de evento (INICIO_FICHA, FIN_OPERACION, etc)
- `mensaje` - Contenido del mensaje
- `fecha_evento` - Cuándo ocurrió
- `enviado_whatsapp` - 0=pendiente, 1=enviado
- `fecha_envio_whatsapp` - Cuándo se envió
- `intentos_envio` - Número de intentos realizados

---

## ⚙️ Configuración

Editar `config_twilio.py` para:

1. **Agregar más números destino:**
```python
NUMEROS_DESTINO = [
    "+5214777301376",  # Cesar
    "+5214777730123",  # Otro supervisor
    "+5214777730456",  # Otro más
]
```

2. **Cambiar parámetros de reintentos:**
```python
MAX_REINTENTOS = 5  # Más intentos
SEGUNDOS_ENTRE_REINTENTOS = 10  # Más espera
```

3. **Cambiar anti-spam:**
```python
SEGUNDOS_MINIMOS_PARA_ENVIO = 10  # Esperar 10s entre eventos
```

---

## 🔐 Credenciales (Ya Configuradas)

- Account SID: `ACd2f2c4ea6849754261613134d6cb085a`
- Auth Token: `9457f520cee19e8abda8c2b7fcb242bd`
- Número Twilio: `+14155238886` (Sandbox para WhatsApp)

⚠️ **IMPORTANTE:** Proteger estos valores en producción

---

## 📝 Logs

Los logs se guardan en consola con formato:

```
INFO - 🚀 Iniciando cron_whatsapp_twilio.py
INFO - 📨 Eventos pendientes: 3
INFO - 📤 Procesando evento 21...
INFO - ✅✅ Intento 1/3: OK
```

Para guardar en archivo, modificar `cron_whatsapp_twilio.py`:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_alerts.log'),
        logging.StreamHandler()
    ]
)
```

---

## ✅ Verificación

Comandos para verificar:

```bash
# Ver eventos pendientes
python -c "from app.db import SessionLocal; from sqlalchemy import text; db = SessionLocal(); print(db.execute(text('SELECT COUNT(*) FROM kb_alertas_eventos WHERE enviado_whatsapp=0')).fetchone())"

# Ver última tarea ejecutada
schtasks /query /tn "Enviar Alertas Kanban WhatsApp"

# Ver logs de último envío
python cron_whatsapp_twilio.py
```

---

## 🎯 Próximos Pasos

1. ✅ **Probar en producción** - Crear evento real en Kanban
2. ✅ **Agregar más números** - Supervisores, jefes, etc
3. ✅ **Personalizar mensajes** - Por tipo de evento
4. ✅ **Dashboard web** - Para monitorear envíos

---

## 📞 Soporte

Si hay errores:

1. Revisar logs de cron
2. Verifica credenciales en `config_twilio.py`
3. Prueba con `test_twilio_completo.py`
4. Revisa estado en Task Scheduler

¡Listo para usar! 🚀
