# Flujo de Trabajo Híbrido: PDF → JSON → BD

## 📋 Descripción

Este enfoque procesa los PDFs en dos pasos separados:
1. **Extracción**: PDF → Ollama → JSON
2. **Importación**: JSON → Base de datos

## ✨ Ventajas

- **Persistencia**: Los resultados de Ollama se guardan en JSON
- **Reanudable**: Si falla, puedes continuar desde donde quedó
- **Auditable**: Puedes revisar los JSONs manualmente
- **Flexible**: Puedes corregir el script de importación sin reprocesar PDFs
- **Backup**: Los JSONs sirven de respaldo de las extracciones

## 🔄 Flujo de Trabajo

### Paso 1: Procesar PDFs a JSON

```bash
# Procesar todos los PDFs pendientes
python scripts/process_to_json.py

# Procesar una cantidad específica (ej: 10 PDFs)
python scripts/process_to_json.py 10
```

**Salida**: Archivos JSON en `/outputs/processed_json/`

**Formato del JSON**:
```json
{
  "codigo": "41269100",
  "ruta": "/path/to/pdf/41269100.pdf",
  "texto_extraido": "Texto extraído del PDF...",
  "descripcion_corta": "Suministro y montaje de...",
  "descripcion_larga": "INFORMACIÓN GENERAL\n...",
  "product_type": "luminaria",
  "processed_at": "2026-01-27T10:30:00",
  "model": "qwen3:4b",
  "success": true,
  "elapsed_time": 45.2
}
```

### Paso 2: Importar JSONs a la Base de Datos

```bash
python scripts/update_db_from_json.py
```

**Características**:
- ✅ Una sola conexión a la BD (optimizado)
- ✅ Commit cada 100 importaciones
- ✅ Muestra progreso en tiempo real
- ✅ Cierra conexión correctamente

## 📁 Estructura de Directorios

```
/Volumes/WEBS/Pdf-local/
├── outputs/
│   └── processed_json/        # JSONs generados
│       ├── 41269100.json
│       ├── 2204081200.json
│       └── ...
├── scripts/
│   ├── process_to_json.py      # Paso 1: Extraer a JSON
│   └── update_db_from_json.py  # Paso 2: Importar a BD
└── database/
    └── tarifa_disano.db        # Base de datos SQLite
```

## 🛠️ Scripts Disponibles

### 1. `process_to_json.py`

**Uso**:
```bash
# Procesar todos los pendientes
python scripts/process_to_json.py

# Procesar N PDFs específicos
python scripts/process_to_json.py 50
```

**Características**:
- ✅ Filtra archivos ocultos de macOS (`._*`)
- ✅ Omite PDFs ya procesados (existe JSON)
- ✅ Muestra tiempo de procesamiento por PDF
- ✅ Guarda JSON inmediatamente después de procesar
- ✅ Se puede interrumpir con `Ctrl+C` sin perder datos

### 2. `update_db_from_json.py`

**Uso**:
```bash
python scripts/update_db_from_json.py
```

**Características**:
- ✅ Una sola conexión a BD (optimizado)
- ✅ Commit cada 100 importaciones
- ✅ Solo importa JSONs con `success: true`
- ✅ Muestra productos ya procesados en BD

## 📊 Monitoreo del Progreso

### Ver cuántos JSONs hay generados

```bash
ls -1 outputs/processed_json/*.json | wc -l
```

### Ver cuántos productos están procesados en BD

```bash
sqlite3 database/tarifa_disano.db "SELECT COUNT(*) FROM productos WHERE ollama_processed = 1;"
```

### Ver JSONs fallidos

```bash
grep -l '"success": false' outputs/processed_json/*.json
```

## 🚨 Manejo de Errores

### Si Ollama se cuelga o timeout

1. **Los JSONs procesados hasta el momento están guardados**
2. **Vuelve a ejecutar** `process_to_json.py` - continuará desde donde quedó
3. **Los JSONs ya existentes se saltan automáticamente**

### Si la importación a BD falla

1. **Vuelve a ejecutar** `update_db_from_json.py`
2. **El script marca automáticamente los ya importados** (busca por `ollama_processed = 1`)
3. **O puedes eliminar JSONs importados** si quieres reprocesar

### Si quieres reprocesar un PDF específico

```bash
# 1. Eliminar el JSON
rm outputs/processed_json/41269100.json

# 2. Volver a procesar (solo ese PDF)
python scripts/process_to_json.py 1
```

## ⚡ Comparativa de Rendimiento

| Enfoque | Ventajas | Desventajas |
|---------|----------|-------------|
| **Híbrido (JSON)** | Persistencia, reanudable, auditable | Dos pasos |
| **Directo a BD** | Un solo paso, más rápido | Si falla, pierde datos |

## 📈 Ejemplo de Uso Completo

```bash
# 1. Procesar los primeros 100 PDFs
python scripts/process_to_json.py 100

# 2. Verificar resultados
ls -1 outputs/processed_json/*.json | wc -l

# 3. Importar a BD
python scripts/update_db_from_json.py

# 4. Continuar con los siguientes 100
python scripts/process_to_json.py 100

# 5. Importar los nuevos
python scripts/update_db_from_json.py

# 6. Al final, procesar todos los pendientes
python scripts/process_to_json.py

# 7. Importación final
python scripts/update_db_from_json.py
```

## 🔍 Auditoría

### Revisar un JSON específico

```bash
cat outputs/processed_json/41269100.json | jq .
```

### Ver estadísticas de procesamiento

```bash
# Total JSONs
find outputs/processed_json -name "*.json" | wc -l

# Exitosos
grep -l '"success": true' outputs/processed_json/*.json | wc -l

# Fallidos
grep -l '"success": false' outputs/processed_json/*.json | wc -l

# Tiempo promedio (requiere jq)
grep '"elapsed_time"' outputs/processed_json/*.json | jq -s 'add/length'
```

## 💾 Limpieza

### Eliminar JSONs ya importados

```bash
# Solo si estás seguro que todo se importó correctamente
rm outputs/processed_json/*.json
```

### Eliminar JSONs fallidos

```bash
for f in outputs/processed_json/*.json; do
  if grep -q '"success": false' "$f"; then
    echo "Eliminando: $f"
    rm "$f"
  fi
done
```

## 🎯 Recomendaciones

1. **Procesar en lotes pequeños** (50-100 PDFs)
2. **Importar después de cada lote**
3. **Verificar resultados antes de continuar**
4. **Mantener los JSONs como backup** hasta finalizar todo
5. **Documentar cualquier error** para mejorar el script
