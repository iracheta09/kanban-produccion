# 📱 Plantilla de Eventos WhatsApp - Kanban

## Estructura del Mensaje

Cada mensaje de WhatsApp contiene los siguientes campos:

```json
{
  "evento": "Tipo de Evento",
  "area": "Nombre del Área",
  "ficha": "Número de Ficha",
  "pa_tipo": "Tipo de Partida",
  "fecha": "YYYY-MM-DD HH:MM",
  "operario": "Nombre del Operario",
  "pzas": "Cantidad de Piezas"
}
```

---

## 🎯 Eventos Configurados

### 1. **INICIO_FICHA** - Cuando un operario inicia una ficha

| Campo | Valor | Ejemplo |
|-------|-------|---------|
| **evento** | "Inicio de ficha" | Inicio de ficha |
| **area** | Nombre del área | ACABADO |
| **ficha** | Número de ficha | 12345 |
| **pa_tipo** | Tipo de partida | PU-001 |
| **fecha** | Fecha y hora actual | 2026-03-23 14:30 |
| **operario** | Nombre del operario | Juan Pérez |
| **pzas** | Cantidad de piezas | 100 |

**Ejemplo de mensaje:**
```
🔵 Inicio de ficha
Área: ACABADO
Ficha: 12345 (PU-001)
Operario: Juan Pérez
Fecha: 2026-03-23 14:30
Piezas: 100 pzas
```

---

### 2. **FIN_OPERACION** - Cuando se termina una operación

| Campo | Valor | Ejemplo |
|-------|-------|---------|
| **evento** | "Fin de operación" | Fin de operación |
| **area** | Nombre del área | ESTAMPADO |
| **ficha** | Número de ficha | 12345 |
| **pa_tipo** | Tipo de partida | PU-001 |
| **fecha** | Fecha y hora actual | 2026-03-23 15:45 |
| **operario** | Nombre del operario | María García |
| **pzas** | Cantidad de piezas procesadas | 85 |

**Ejemplo de mensaje:**
```
✅ Fin de operación
Área: ESTAMPADO
Ficha: 12345 (PU-001)
Operario: María García
Fecha: 2026-03-23 15:45
Piezas: 85 pzas
```

---

### 3. **LOTE_TERMINADO** - Cuando se cierra el lote en Acabado

| Campo | Valor | Ejemplo |
|-------|-------|---------|
| **evento** | "Lote terminado" | Lote terminado |
| **area** | Nombre del área | ACABADO |
| **ficha** | Número de ficha | 12345 |
| **pa_tipo** | Tipo de partida | PU-001 |
| **fecha** | Fecha y hora actual | 2026-03-23 16:20 |
| **operario** | Nombre del operario | Carlos López |
| **pzas** | Cantidad total de piezas | 100 |

**Ejemplo de mensaje:**
```
🏁 Lote terminado
Área: ACABADO
Ficha: 12345 (PU-001)
Operario: Carlos López
Fecha: 2026-03-23 16:20
Piezas: 100 pzas (Completadas)
```

---

### 4. **LLEGADA_FICHAS** - Cuando llegan fichas nuevas

| Campo | Valor | Ejemplo |
|-------|-------|---------|
| **evento** | "Llegada de fichas" | Llegada de fichas |
| **area** | Nombre del área | ACABADO |
| **ficha** | N/A (múltiples fichas) | - |
| **pa_tipo** | N/A | - |
| **fecha** | Fecha y hora actual | 2026-03-23 08:00 |
| **operario** | "Sistema" | Sistema |
| **pzas** | Cantidad de fichas nuevas | 5 |

**Ejemplo de mensaje:**
```
📥 Llegada de fichas
Área: ACABADO
Cantidad: 5 fichas nuevas
Fecha: 2026-03-23 08:00
```

---

## 🔧 Variables Disponibles

```python
# En alerta_service.py - registrar_evento_alerta()

pa_tipo: str              # Tipo de partida (ej: PU-001)
ficha: str                # Número de ficha (ej: 12345)
id_operacion: int         # ID de operación interna
nombre_operacion: str     # Nombre de la operación
id_operario: str          # ID del operario
nombre_operario: str      # Nombre del operario
pzas: float              # Cantidad de piezas (NUEVO ✨)
```

---

## 📊 Campos Mapeados en BD

```sql
-- Tabla: kb_alertas_eventos
SELECT
    tipo_evento,        -- INICIO_FICHA, FIN_OPERACION, etc.
    id_area,           -- ID del área
    nombre_area,       -- Nombre del área
    pa_tipo,           -- Tipo de partida ✨
    ficha,             -- Número de ficha ✨
    id_operacion,      -- ID de operación
    nombre_operacion,  -- Nombre de operación
    id_operario,       -- ID del operario
    nombre_operario,   -- Nombre del operario
    mensaje,           -- Descripción del evento
    fecha_evento,      -- Fecha/hora del evento
    created_at         -- Timestamp creación
FROM dbo.kb_alertas_eventos;
```

---

## ✅ Cambios Recientes

- ✨ Agregados campos: `ficha`, `pa_tipo`, `pzas` al payload de WhatsApp
- ✨ `whatsapp_client.py` actualizado para aceptar parámetros opcionales
- ✨ `alerta_service.py` actualizado para pasar datos completos
- ✨ Todos los eventos ahora envían información detallada

---

## 🚀 Próximas Mejoras (Opcionales)

- [ ] Notificaciones por área específica
- [ ] Múltiples números de teléfono
- [ ] Plantillas personalizables por evento
- [ ] Emojis según tipo de evento
- [ ] Adjuntos (imágenes, reportes)
