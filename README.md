# PDF to BC3 - Procesamiento de Fichas Técnicas con Ollama

Sistema completo para procesar fichas técnicas en PDF y extraer información estructurada en formato BC3 utilizando modelos de lenguaje local (Ollama).

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

### Gestión de Tarifas
- **Base de datos SQLite** con productos de Disano
- **Procesamiento por lotes** de todas las fichas técnicas
- **Actualización incremental** (saltar ya procesados)
- **Interfaz web** con Flask para visualizar y gestionar productos

### Scraper
- **Scraper de Disano** con Playwright
- **Extracción de fichas técnicas** desde la web
- **Descarga automática** de PDFs

## 📋 Requisitos Previos

### 1. Python 3.8+
```bash
python --version  # Debe ser 3.8 o superior
```

### 2. Ollama Instalado

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

### 3. Modelo Recomendado: DeepSeek R1
```bash
# Iniciar Ollama
ollama serve

# Descargar modelo recomendado
ollama pull deepseek-r1:latest

# Modelo alternativo (más ligero)
ollama pull llama3.2:3b
```

## 🚀 Instalación

```bash
# Clonar el repositorio (si aplica)
cd /Volumes/WEBS/Pdf-local

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## 📁 Estructura del Proyecto

```
pdf-local/
├── app/                        # Aplicación Flask
│   ├── bc3/                   # Generación de archivos BC3
│   │   ├── __init__.py
│   │   └── generator.py
│   ├── static/                # CSS, JS, favicon
│   ├── templates/             # Plantillas HTML
│   ├── utils/                 # Utilidades principales
│   │   ├── bc3_extractor.py   # Extractor BC3 (2 peticiones)
│   │   ├── cache_manager.py   # Sistema de caché
│   │   ├── json_validator.py  # Validación de JSON
│   │   ├── ollama_client.py   # Cliente de Ollama
│   │   ├── pdf_extractor.py   # Extracción de texto de PDFs
│   │   ├── tariff_processor.py # Procesador de tarifas
│   │   ├── disano_scraper.py  # Scraper de Disano
│   │   └── __init__.py
│   ├── config.py              # Configuración
│   ├── main.py                # Punto de entrada
│   └── models.py              # Modelos de BD
│
├── scripts/                    # Scripts utilitarios
│   ├── process_all_pdfs.py    # Procesar todas las fichas técnicas
│   ├── comparar_modelos.py    # Comparar modelos de Ollama
│   ├── diagnose.py            # Diagnóstico del sistema
│   └── investigate_structure.py # Investigar estructura de BD
│
├── tests/                      # Tests
│   ├── test_bc3_extractor.py
│   ├── test_playwright_scraper.py
│   └── test_scraper_*.py
│
├── docs/                       # Documentación
│   ├── DOCS_BC3_EXTRACTOR.md  # Documentación del extractor BC3
│   ├── SCRAPER.md             # Documentación del scraper
│   ├── TARIFAS.md             # Documentación de tarifas
│   └── INICIO.md              # Documentación de inicio
│
├── database/                   # Bases de datos
│   └── tarifa_disano.db       # BD principal de productos
│
├── cache/                      # Caché de procesamientos
├── uploads/                    # PDFs subidos vía web
├── samples/                    # Ejemplos de PDFs
├── outputs/                    # Archivos BC3 generados
├── requirements.txt            # Dependencias Python
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

### 2. Procesar Todas las Fichas Técnicas

```bash
# Procesar todas las fichas de una carpeta y actualizar BD
python scripts/process_all_pdfs.py

# El script:
# - Escanea /Volumes/WEBS/disano-scraper/data/output/fichas_tecnicas
# - Extrae texto y datos BC3 de cada PDF
# - Actualiza la BD con los resultados
# - Salta PDFs ya procesados
```

**Configuración en `process_all_pdfs.py`:**
```python
PDF_FOLDER = "/Volumes/WEBS/disano-scraper/data/output/fichas_tecnicas"
DB_PATH = "database/tarifa_disano.db"
MODEL = "deepseek-r1:latest"
TARGET_LANGUAGE = "es"
```

### 3. Probar un PDF Individual

```bash
# Prueba el extractor BC3 con un PDF específico
python tests/test_bc3_extractor.py ruta/al/pdf.pdf

# Con idioma específico (es, ca, eu, gl)
python tests/test_bc3_extractor.py ruta/al/pdf.pdf ca
```

### 4. Comparar Modelos de Ollama

```bash
# Comparar calidad de salida entre modelos
python scripts/comparar_modelos.py
```

## ⚙️ Configuración

### Modelo de Ollama

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

### Configuración de Caché

**Archivo:** `app/utils/cache_manager.py`

```python
CACHE_TTL_HOURS = 24  # Tiempo de vida del caché
CACHE_DIR = "cache"   # Directorio de caché
```

## 📊 Base de Datos

### Esquema de `productos`

```sql
CREATE TABLE productos (
    "CÓDIGO" TEXT PRIMARY KEY,
    REFERENCIA TEXT,
    FAMILIA TEXT,
    SUBFAMILIA TEXT,
    NOMBRE TEXT,
    PVP REAL,
    -- ... más campos ...

    -- Campos BC3 (añadidos)
    texto_extraido TEXT,
    bc3_descripcion_corta TEXT,
    bc3_descripcion_larga TEXT,
    bc3_product_type TEXT,
    ollama_processed INTEGER DEFAULT 0,
    ollama_processed_at TIMESTAMP,
    ollama_model TEXT
);
```

### Consultas Útiles

```bash
# Ver productos procesados
sqlite3 database/tarifa_disano.db "SELECT COUNT(*) FROM productos WHERE ollama_processed = 1;"

# Ver un producto específico
sqlite3 database/tarifa_disano.db "SELECT * FROM productos WHERE \"CÓDIGO\" = '15641639';"

# Ver descripciones BC3
sqlite3 database/tarifa_disano.db "SELECT \"CÓDIGO\", NOMBRE, bc3_descripcion_corta FROM productos WHERE ollama_processed = 1 LIMIT 5;"
```

## 🔧 Extracción BC3

### Tipologías de Productos Soportadas

El sistema detecta automáticamente la tipología basándose en:
1. **Ruta del archivo** (prioridad)
2. **Contenido del PDF** (fallback)

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

## 🧹 Limpieza de Caché

```bash
# Eliminar todo el caché
rm -rf cache/*

# O usar el script de diagnóstico
python scripts/diagnose.py --clear-cache
```

## 📝 Notas de Implementación

### Mejoras Implementadas

1. **Sistema de Caché MD5**: Evita reprocesar PDFs ya procesados
2. **Chunking Inteligente**: Divide PDFs largos en fragmentos con superposición
3. **Validación Robusta de JSON**: Corrige errores comunes en respuestas de Ollama
4. **Detección por Ruta**: Prioriza detección de tipología por estructura de carpetas
5. **9 Certificaciones ISO**: Siempre incluidas en NORMAS Y CUMPLIMIENTO
6. **Limpieza de Markdown**: Elimina negritas y formato Markdown de las respuestas

### Configuración de Modelos

**DeepSeek R1 (Recomendado):**
- ✅ Mejor calidad de salida
- ✅ Sin secciones duplicadas
- ✅ Captura tablas de combinaciones
- ❌ Más lento (requiere más recursos)

**Llama 3.2 3B (Alternativa ligera):**
- ✅ Rápido y ligero
- ⚠️ Calidad aceptable pero inferior
- ✅ Bueno para pruebas

## 🐛 Solución de Problemas

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

### Errores de JSON en Ollama

El sistema incluye `JSONValidator` que corrige automáticamente:
- Comillas simples → dobles
- Trailing commas
- Comentarios de JavaScript
- Valores sin comillas

## 📚 Documentación Adicional

- [docs/DOCS_BC3_EXTRACTOR.md](docs/DOCS_BC3_EXTRACTOR.md) - Documentación detallada del extractor BC3
- [docs/SCRAPER.md](docs/SCRAPER.md) - Documentación del scraper de Disano
- [docs/TARIFAS.md](docs/TARIFAS.md) - Documentación del sistema de tarifas
- [docs/INICIO.md](docs/INICIO.md) - Guía de inicio rápido

## 📄 Licencia

Este proyecto es para uso interno y procesamiento de fichas técnicas de Disano.

---

**Última actualización:** Enero 2025
**Versión:** 2.0.0
**Modelo recomendado:** DeepSeek R1
