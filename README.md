# PDF to BC3 - Procesamiento de Fichas Técnicas con IA

Sistema completo para procesar fichas técnicas en PDF y extraer información estructurada en formato BC3 utilizando modelos de lenguaje local (Ollama) y Anthropic Claude API.

## 🎯 Características Principales

### Extracción BC3
- **Dos peticiones independientes** para generación óptima:
  - Descripción corta: Párrafo de presupuesto (3-4 líneas)
  - Descripción larga: Detalles técnicos estructurados por secciones
- **Detección automática de tipología** de producto (basada en ruta del archivo)
- **Soporte multiidioma**: Español, Catalán, Euskera, Gallego
- **9 certificaciones ISO obligatorias** + certificaciones específicas del PDF
- **Sistema de caché** para evitar reprocesamiento
- **Chunking inteligente** para PDFs largos

### Procesamiento por Lotes con Anthropic
- **Procesamiento masivo** con Claude Haiku API
- **Velocidad optimizada**: ~18 segundos/texto (15x más rápido que Ollama)
- **Coste eficiente**: ~$0.50 por cada 100 textos
- **Flujo híbrido**: PDF → JSON → Base de datos
- **Reintentos automáticos** con exponential backoff
- **Persistencia intermedia** en JSON para evitar pérdida de datos

### Gestión de Tarifas
- **Base de datos SQLite** con 8,288 productos de Disano
- **Procesamiento por lotes** de todas las fichas técnicas
- **Actualización incremental** (saltar ya procesados)
- **Interfaz web** con Flask para visualizar y gestionar productos
- **Exportación a Excel** con datos completos

### Scraper
- **Scraper de Disano** con Playwright
- **Extracción de fichas técnicas** desde la web
- **Descarga automática** de PDFs

## 📋 Requisitos Previos

### 1. Python 3.11+
```bash
python --version  # Debe ser 3.11 o superior
```

### 2. Ollama (Opcional - Para procesamiento local)

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Descargar desde [ollama.com](https://ollama.com/download)

### 3. Anthropic API Key (Recomendado para procesamiento por lotes)
Crear archivo `.env`:
```
ANTHROPIC_API_KEY=your_key_here
```

## 🚀 Instalación

```bash
# Clonar el repositorio
cd /Volumes/WEBS/Pdf-local

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt
```

## 📁 Estructura del Proyecto

```
pdf-local/
├── app/                        # Aplicación Flask
│   ├── bc3/                   # Generación de archivos BC3
│   ├── static/                # CSS, JS, favicon
│   ├── templates/             # Plantillas HTML
│   ├── utils/                 # Utilidades principales
│   │   ├── bc3_extractor.py   # Extractor BC3 (2 peticiones)
│   │   ├── cache_manager.py   # Sistema de caché
│   │   ├── json_validator.py  # Validación de JSON
│   │   ├── ollama_client.py   # Cliente de Ollama
│   │   ├── anthropic_extractor.py  # Cliente Anthropic
│   │   ├── pdf_extractor.py   # Extracción de texto de PDFs
│   │   └── __init__.py
│   ├── config.py              # Configuración
│   └── main.py                # Punto de entrada
│
├── scripts/                    # Scripts utilitarios
│   ├── batch/                 # Procesamiento por lotes
│   │   ├── process_all_pdfs.py
│   │   ├── process_to_json.py
│   │   ├── process_texts_batch_api.py
│   │   └── update_db_from_json.py
│   ├── monitoring/            # Scripts de monitoreo
│   │   ├── check_progress.py
│   │   ├── check_errors.py
│   │   └── retry_failed.py
│   └── utils/                 # Scripts utilitarios
│       ├── export_to_excel.py
│       ├── diagnose.py
│       └── debug_process.py
│
├── tests/                      # Tests
├── docs/                       # Documentación detallada
│   ├── WORKFLOW_HIBRIDO.md    # Flujo PDF→JSON→BD
│   ├── DOCS_BC3_EXTRACTOR.md  # Documentación del extractor BC3
│   ├── SCRAPER.md             # Documentación del scraper
│   └── TARIFAS.md             # Documentación de tarifas
│
├── database/                   # Bases de datos
│   └── tarifa_disano.db       # BD principal (8,288 productos, 23MB)
│
├── cache/                      # Caché de procesamientos
├── uploads/                    # PDFs subidos vía web
├── samples/                    # Ejemplos de PDFs
├── outputs/                    # Archivos BC3 generados
├── requirements.txt            # Dependencias Python
├── CHANGELOG.md                # Historial de cambios
└── README.md                   # Este archivo
```

## 🎮 Uso

### 1. Interfaz Web

```bash
# Iniciar aplicación
python app/main.py

# Acceder a
http://localhost:5001
```

**Rutas disponibles:**
- `/` - Página principal
- `/upload` - Subir y procesar PDF
- `/tarifas` - Ver tarifas de Disano
- `/tarifas/product/<id>` - Ver detalle de producto

### 2. Procesamiento por Lotes (Recomendado)

**Flujo completo en 3 pasos:**

```bash
# Paso 1: Extraer textos de PDFs
python scripts/extract_text_only.py

# Paso 2: Procesar con Anthropic Haiku
python scripts/process_texts_batch_api.py

# Paso 3: Importar a base de datos
python scripts/update_db_from_json.py
```

**O process todo en uno:**
```bash
python scripts/process_all_pdfs.py
```

### 3. Monitoreo de Proceso

```bash
# Ver progreso actual
tail -f /tmp/anthropic_all.log

# Script de monitoreo
bash scripts/monitor_progress.sh

# Ver errores
python scripts/check_errors.py
```

### 4. Exportar a Excel

```bash
# Exportar base de datos completa
python scripts/export_to_excel.py

# Guarda en ~/Documents/tarifa_disano_YYYYMMDD_HHMMSS.xlsx
```

### 5. Probar un PDF Individual

```bash
# Prueba el extractor BC3 con un PDF específico
python tests/test_bc3_extractor.py ruta/al/pdf.pdf

# Con idioma específico (es, ca, eu, gl)
python tests/test_bc3_extractor.py ruta/al/pdf.pdf ca
```

## ⚙️ Configuración

### Anthropic API (Recomendado)

**Archivo:** `.env`
```
ANTHROPIC_API_KEY=sk-ant-...
```

**Configuración en `scripts/process_texts_batch_api.py`:**
```python
INPUT_DIR = os.path.expanduser("~/Documents/extracted_texts")
OUTPUT_DIR = os.path.expanduser("~/Documents/processed_json")
MODEL = "claude-3-5-haiku-latest"
TARGET_LANGUAGE = "es"
BATCH_SIZE = 100
MAX_CONSECUTIVE_ERRORS = 5
RETRY_DELAYS = [2, 5, 10, 30, 60]  # segundos
```

### Modelo de Ollama (Alternativa local)

**Archivo:** `app/config.py`

```python
OLLAMA_MODEL = "deepseek-r1:latest"  # Modelo por defecto

AVAILABLE_MODELS = {
    "deepseek-r1:latest": "DeepSeek R1 - Mejor calidad",
    "llama3.2:3b": "Llama 3.2 3B - Ligero y rápido",
    "llama3.2:latest": "Llama 3.2 - Equilibrado",
    "mistral:7b": "Mistral 7B - Buen rendimiento",
}
```

### Configuración de Chunking

**Archivo:** `app/utils/pdf_extractor.py`

```python
MAX_CHARS_PER_CHUNK = 8000  # Máximo de caracteres por chunk
MAX_PAGES_PER_CHUNK = 5     # Máximo de páginas por chunk
OVERLAP_CHARS = 500         # Superposición entre chunks
```

## 📊 Base de Datos

### Esquema Actual (39 campos)

```sql
CREATE TABLE productos (
    MARCA TEXT,
    [CÓDIGO] TEXT PRIMARY KEY,
    [CÓDIGO WEB] TEXT,
    REFERENCIA TEXT,
    [EAN 13] REAL,
    DESCRIPCION TEXT,
    [U.P.LOG] REAL,
    [U.CAJA] INTEGER,
    [DTO.] TEXT,
    [CLASE ETIM] TEXT,
    RAEE_A REAL, RAEE_L REAL, RAEE_T REAL,
    [Peso bruto KG] REAL, [Peso bruto GR] REAL,
    [Peso neto KG] REAL, [Peso neto GR] REAL,
    [Longitud M] REAL, [Longitud MM] REAL,
    [Ancho M] REAL, [Ancho MM] REAL,
    [Alto M] REAL, [Altura MM] REAL,
    [Volumen DM3] REAL, CM3 REAL,
    Serie_familia_1 TEXT,
    Familia_WEB TEXT,
    Familia_Catalogo TEXT,
    Familia_Catalogo_PTL TEXT,
    imagen TEXT,
    Url_ficha_tec TEXT,
    descontinuado INTEGER,
    descripcion_corta TEXT,
    img_url TEXT,
    [PVP_26_01_26] REAL,

    -- Campos BC3 (5,286 productos procesados)
    bc3_descripcion_corta TEXT,
    bc3_descripcion_larga TEXT,
    bc3_product_type TEXT,  -- 'columna' o 'articulacion'
    bc3_processed_at TIMESTAMP
);
```

### Estadísticas Actuales

- **Total productos**: 8,288
- **Con BC3 procesado**: 5,286 (63.8%)
- **Con URL de imagen**: 7,758 (93.6%)
- **Tamaño BD**: 23 MB (optimizado)

### Consultas Útiles

```bash
# Ver productos con BC3
sqlite3 database/tarifa_disano.db "
SELECT COUNT(*) FROM productos
WHERE bc3_descripcion_corta IS NOT NULL;"

# Ver distribución de tipos
sqlite3 database/tarifa_disano.db "
SELECT bc3_product_type, COUNT(*)
FROM productos
WHERE bc3_product_type IS NOT NULL
GROUP BY bc3_product_type;"

# Buscar un producto específico
sqlite3 database/tarifa_disano.db "
SELECT * FROM productos
WHERE [CÓDIGO] = '33036139';"
```

## 🔧 Extracción BC3

### Tipologías de Productos Soportadas

El sistema detecta automáticamente la tipología:

**Tipologías:**
- `luminaria` - Luminarias LED, fluorescentes, etc.
- `equipo_alimentacion` - Drivers, transformadores, balastos
- `accesorio_mecanico` - Articulaciones, soportes, proyectores
- `columna` - Columnas luminosas, báculos, postes

### Estructura de la Descripción Corta

```
Suministro y montaje de [TIPO] igual o equivalente a [NOMBRE] (Código: [CÓDIGO]).
[DESCRIPCIÓN GENERAL] de última generación con [CARACTERÍSTICAS PRINCIPALES].
Incluye [DATOS TÉCNICOS CLAVE].
con certificaciones ISO 9001, ISO 14001, ISO 14002, y ISO 45001.
```

### Estructura de la Descripción Larga

```
INFORMACIÓN GENERAL
Artículo: [Nombre]
Código: [Código]

DIMENSIONES Y PESO
Altura: [Valor] mm
Diámetro: [Valor] mm
...

CARACTERÍSTICAS ELÉCTRICAS
Potencia: [Valor] W
Tensión: [Valor] V
...

NORMAS Y CUMPLIMIENTO
Certificado ISO 9001
Certificado ISO 14001
...
[Certificaciones específicas del PDF]
```

## 🌐 Multi-Idioma

El extractor BC3 soporta 4 idiomas:

```python
from app.utils import extract_bc3_from_pdf

# Español (por defecto)
result = extract_bc3_from_pdf(pdf_path, target_language='es')

# Catalán
result = extract_bc3_from_pdf(pdf_path, target_language='ca')

# Euskera
result = extract_bc3_from_pdf(pdf_path, target_language='eu')

# Gallego
result = extract_bc3_from_pdf(pdf_path, target_language='gl')
```

## 📈 Comparativa de Procesamiento

### Anthropic Claude Haiku (Recomendado)
- ✅ **Velocidad**: ~18s/texto
- ✅ **Coste**: ~$0.50 cada 100 textos
- ✅ **Calidad**: Excelente comprensión técnica
- ✅ **Consistencia**: 100% éxito en 4,022 textos
- ✅ **Escalar**: Procesa miles sin degradación

### Ollama DeepSeek R1 (Local)
- ✅ **Coste**: Gratis (solo computación)
- ✅ **Privacidad**: Todo es local
- ⚠️ **Velocidad**: ~45-90s/texto
- ⚠️ **Requiere**: GPU para buen rendimiento

## 🐛 Solución de Problemas

### Anthropic API Rate Limit

```bash
# El script ya incluye reintentos automáticos
# Si persiste, aumentar RETRY_DELAYS en process_texts_batch_api.py
```

### Ollama no responde

```bash
# Verificar que Ollama está ejecutándose
ps aux | grep ollama

# Reiniciar Ollama
killall ollama
ollama serve
```

### Error de memoria en PDFs largos

```bash
# Reducir tamaño de chunk en app/utils/pdf_extractor.py
MAX_CHARS_PER_CHUNK = 6000  # en lugar de 8000
```

## 📚 Documentación Adicional

- [docs/WORKFLOW_HIBRIDO.md](docs/WORKFLOW_HIBRIDO.md) - Flujo híbrido PDF→JSON→BD
- [docs/DOCS_BC3_EXTRACTOR.md](docs/DOCS_BC3_EXTRACTOR.md) - Documentación detallada del extractor BC3
- [docs/SCRAPER.md](docs/SCRAPER.md) - Documentación del scraper de Disano
- [docs/TARIFAS.md](docs/TARIFAS.md) - Documentación del sistema de tarifas
- [CHANGELOG.md](CHANGELOG.md) - Historial de cambios

## 📄 Licencia

Este proyecto es para uso interno y procesamiento de fichas técnicas de Disano.

---

**Última actualización:** Enero 2026
**Versión:** 3.0.0
**Modelo recomendado:** Claude 3.5 Haiku (API) o DeepSeek R1 (local)
