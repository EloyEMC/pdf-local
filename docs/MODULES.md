# Módulos de la Aplicación

Documentación detallada de cada módulo del proyecto.

---

## app/utils/bc3_extractor.py

**Propósito**: Extraer datos BC3 usando dos peticiones independientes a Ollama.

### Clase Principal: BC3Extractor

```python
from app.utils.bc3_extractor import BC3Extractor

extractor = BC3Extractor(model="deepseek-r1:latest", use_cache=True)
result = extractor.extract(pdf_text, pdf_path="ruta/a/archivo.pdf", target_language='es')
```

### Función Auxiliar

```python
from app.utils import extract_bc3_from_pdf

result = extract_bc3_from_pdf(
    pdf_path="ruta/a/archivo.pdf",
    model="deepseek-r1:latest",
    target_language='es',
    use_cache=True
)

# Resultado:
# {
#     'descripcion_corta': 'Suministro y montaje de...',
#     'descripcion_larga': 'INFORMACIÓN GENERAL\n...',
#     'product_type': 'luminaria',
#     'product_type_name': 'Luminaria'
# }
```

### Tipologías Soportadas

| Tipo | Keywords Carpeta | Descripción |
|------|-----------------|-------------|
| `luminaria` | alumbrado publico, decoracion, emergencia, empotrables, interiores, luminarias viales, pantallas estancas, proyectores, residenciales, suspension, iluminacion uv | Luminarias LED, fluorescentes, etc. |
| `equipo_alimentacion` | accesorio electrico, kit de emergencia | Drivers, transformadores, balastos |
| `accesorio_mecanico` | accesorio de columna, accesorio de iluminacion, accesorio mecanico, accesorio del sistema de carril | Articulaciones, soportes, proyectores |
| `columna` | columna | Columnas luminosas, báculos, postes |

### Secciones por Tipología

**Luminaria**: INFORMACIÓN GENERAL, DIMENSIONES Y PESO, INSTALACIÓN, CARACTERÍSTICAS ELÉCTRICAS Y CONTROLES, DATOS FOTOMÉTRICOS, CARACTERÍSTICAS MECÁNICAS, MATERIALES Y COLORES, NORMAS Y CUMPLIMIENTO, GARANTÍA

**Equipo de Alimentación**: INFORMACIÓN GENERAL, DIMENSIONES Y PESO, CARACTERÍSTICAS ELÉCTRICAS, PROTECCIONES, INSTALACIÓN, MATERIALES, NORMAS Y CUMPLIMIENTO, GARANTÍA

**Accesorio Mecánico**: INFORMACIÓN GENERAL, DIMENSIONES Y PESO, MATERIALES Y ACABADOS, CAPACIDAD DE CARGA, INSTALACIÓN, NORMAS Y CUMPLIMIENTO, GARANTÍA

**Columna**: INFORMACIÓN GENERAL, DIMENSIONES Y PESO, MATERIALES Y ACABADOS, CAPACIDAD DE CARGA, FUNDAMENTACIÓN, INSTALACIÓN, NORMAS Y CUMPLIMIENTO, GARANTÍA

### 9 Certificaciones ISO Obligatorias

Siempre se incluyen en NORMAS Y CUMPLIMIENTO (en este orden):

1. Certificado ISO 9001
2. Certificado ISO 14001
3. Certificado ISO 14002
4. Certificado ISO 45001
5. Certificado ISO 50001
6. Certificado que acredite el cumplimiento de las directivas RoHS y RAEE
7. Certificado que acredite la inscripción del fabricante en un Sistema Integrado de Gestión (SIG) de residuos
8. Certificado de Productor de Producto
9. Nota: Declaración Ambiental del Producto (DAP) se debe consultar siempre su disponibilidad para cada código

Inmediatamente después, se añaden las certificaciones específicas del PDF (EN60598-1, CE, RG0, Etiqueta Energética, etc.).

---

## app/utils/ollama_client.py

**Propósito**: Cliente de Ollama para comunicación con el modelo LLM.

### Clase Principal: OllamaClient

```python
from app.utils.ollama_client import OllamaClient

client = OllamaClient(model="deepseek-r1:latest", use_cache=True)

# Chat simple
response = client.chat("¿Qué es una luminaria LED?")
print(response)

# Extraer datos de PDF
data = client.extract_data_from_pdf(pdf_text, pdf_path="ruta.pdf")
```

### Configuración

```python
MODEL = "deepseek-r1:latest"  # Modelo por defecto
OLLAMA_API_URL = "http://localhost:11434/api/chat"  # Endpoint de Ollama
```

### Métodos

- `chat(prompt, system_prompt=None)` - Envía un prompt a Ollama y obtiene respuesta
- `extract_data_from_pdf(pdf_text, pdf_path=None)` - Extrae datos estructurados de un PDF
- `generate_bc3_description(pdf_text, product_type)` - Genera descripción BC3 (deprecated, usar bc3_extractor)

---

## app/utils/pdf_extractor.py

**Propósito**: Extraer texto de PDFs usando pdfplumber con eliminación de cabeceras/pies.

### Funciones Principales

```python
from app.utils.pdf_extractor import extract_pdf_text, extract_pdf_text_chunked

# Extracción simple
text = extract_pdf_text("ruta/a/archivo.pdf", remove_headers=True)

# Extracción con chunking (para PDFs largos)
chunks = extract_pdf_text_chunked("ruta/a/archivo.pdf", remove_headers=True)
# Devuelve: [{"text": "...", "pages": [1, 2], "chunk_id": 0, "is_complete": bool}, ...]
```

### Configuración de Chunking

```python
MAX_CHARS_PER_CHUNK = 8000  # Máximo de caracteres por chunk
OVERLAP_CHARS = 500         # Superposición entre chunks
MAX_PAGES_PER_CHUNK = 5     # Máximo de páginas por chunk
```

### Función BC3

```python
from app.utils import extract_bc3_from_pdf

# Extrae datos BC3 usando el sistema de dos peticiones
result = extract_bc3_from_pdf(
    pdf_path="ruta/a/archivo.pdf",
    model="deepseek-r1:latest",
    target_language='es',
    use_cache=True
)
```

### Funciones Auxiliares

- `validate_pdf(pdf_path)` - Valida que el archivo sea un PDF válido
- `get_pdf_info(pdf_path)` - Obtiene información básica (número de páginas, tamaño, necesita chunking)
- `extract_pdf_to_dict(pdf_path)` - Extrae datos estructurados usando Ollama

---

## app/utils/cache_manager.py

**Propósito**: Sistema de caché MD5 para evitar reprocesar PDFs.

### Clase Principal: CacheManager

```python
from app.utils.cache_manager import CacheManager

cache = CacheManager(cache_dir="cache", ttl_hours=24)

# Guardar en caché
cache.set(pdf_path="ruta.pdf", model="deepseek-r1:latest", data={"key": "value"})

# Recuperar del caché
cached_data = cache.get(pdf_path="ruta.pdf", model="deepseek-r1:latest")

# Invalidar caché
cache.invalidate(pdf_path="ruta.pdf")  # Un PDF específico
cache.invalidate()  # Todo el caché
```

### Funcionamiento

1. **Genera hash MD5** del contenido del PDF
2. **Clave de caché**: `{md5_hash}_{model}`
3. **TTL**: 24 horas por defecto (configurable)
4. **Formato**: JSON en disco

### Estructura de Archivos

```
cache/
├── a1b2c3d4e5f6_deepseek-r1_latest.json
├── f7e8d9c0b1a2_llama3.2_3b.json
└── ...
```

---

## app/utils/json_validator.py

**Propósito**: Valida y corrige respuestas JSON de Ollama.

### Clase Principal: JSONValidator

```python
from app.utils.json_validator import JSONValidator

# Extraer y validar JSON
response = """
{
    nombre: 'Lámpara LED',
    potencia: 45W,
    materiales: ['Aluminio'],
}
"""

validated = JSONValidator.extract_and_validate(response)
# Corrige automáticamente:
# - Comillas simples → dobles
# - Trailing commas
# - Valores sin comillas
```

### Errores Corregidos

1. **Comillas simples** → Comillas dobles
2. **Trailing commas** → Eliminadas
3. **Comentarios JavaScript** → Eliminados
4. **Valores sin comillas** → Entrecomillados
5. **Markdown** → Eliminado

### Schema Esperado

```python
EXPECTED_SCHEMA = {
    "codigo_producto": str,
    "nombre": str,
    "descripcion": str,
    "dimensiones": dict,
    "caracteristicas_electricas": dict,
    "materiales": list,
    "colores": list,
    "normas": list,
    "garantia": (str, type(None)),
    "observaciones": (str, type(None))
}
```

---

## app/main.py

**Propósito**: Aplicación Flask con interfaz web.

### Rutas Principales

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/` | GET | Página principal |
| `/upload` | POST | Subir y procesar PDF |
| `/tarifas` | GET | Listado de productos |
| `/tarifas/product/<id>` | GET | Detalle de producto |
| `/tarifas/product/<id>/process` | POST | Procesar PDF de producto |

### Iniciar Aplicación

```bash
python app/main.py
# Acceder a http://localhost:5001
```

### Configuración

```python
DEBUG = True
SECRET_KEY = 'tu-clave-secreta'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
```

---

## app/config.py

**Propósito**: Configuración centralizada de la aplicación.

### Configuración de Modelos

```python
OLLAMA_MODEL = "deepseek-r1:latest"

AVAILABLE_MODELS = {
    "deepseek-r1:latest": "DeepSeek R1 - Mejor calidad",
    "llama3.2:3b": "Llama 3.2 3B - Ligero y rápido",
    "llama3.2:latest": "Llama 3.2 - Equilibrado",
    "mistral:7b": "Mistral 7B - Buen rendimiento",
}
```

### Otras Configuraciones

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, '../uploads')
DATABASE_FOLDER = os.path.join(BASE_DIR, '../database')
```

---

## scripts/process_all_pdfs.py

**Propósito**: Procesar todas las fichas técnicas y actualizar la base de datos.

### Uso

```bash
python scripts/process_all_pdfs.py
```

### Configuración

```python
PDF_FOLDER = "/Volumes/WEBS/disano-scraper/data/output/fichas_tecnicas"
DB_PATH = "database/tarifa_disano.db"
MODEL = "deepseek-r1:latest"
TARGET_LANGUAGE = "es"
```

### Funcionamiento

1. Escanea recursivamente la carpeta de PDFs
2. Por cada PDF:
   - Extrae texto (eliminando cabeceras/pies)
   - Extrae datos BC3 (2 peticiones a Ollama)
   - Actualiza la base de datos
3. Salta PDFs ya procesados (`ollama_processed = 1`)
4. Muestra progreso y resumen final

### Campos Actualizados en BD

- `texto_extraido` - Texto completo del PDF (limitado a 50KB)
- `bc3_descripcion_corta` - Párrafo de presupuesto
- `bc3_descripcion_larga` - Detalles técnicos estructurados
- `bc3_product_type` - Tipo de producto (luminaria, columna, etc.)
- `ollama_processed` - Marcado como 1 (procesado)
- `ollama_processed_at` - Timestamp de procesamiento
- `ollama_model` - Modelo usado (ej: deepseek-r1:latest)

---

## tests/test_bc3_extractor.py

**Propósito**: Test del extractor BC3.

### Uso

```bash
# Probar con un PDF específico
python tests/test_bc3_extractor.py /ruta/a/archivo.pdf

# Con idioma específico
python tests/test_bc3_extractor.py /ruta/a/archivo.pdf ca
```

### Salida

```
============================================================
Extractor BC3 - Dos Peticiones
============================================================

📄 PDF: /ruta/a/archivo.pdf
🌐 Idioma: es

Procesando...

✓ Tipología detectada: Luminaria

------------------------------------------------------------
PARTE 1: DESCRIPCIÓN CORTA (Párrafo de Presupuesto)
------------------------------------------------------------
Suministro y montaje de luminaria igual o equivalente a...

------------------------------------------------------------
PARTE 2: DESCRIPCIÓN LARGA (Detalles Técnicos)
------------------------------------------------------------
INFORMACIÓN GENERAL
Artículo: ...
```

---

## Dependencias

### requirements.txt

```
flask==3.0.0
flask-sqlalchemy==3.1.1
pdfplumber==0.10.3
requests==2.31.0
playwright==1.40.0
```

### Instalación

```bash
pip install -r requirements.txt
playwright install
```

---

## Notas de Desarrollo

### Buenas Prácticas

1. **Usar extract_bc3_from_pdf** en lugar de llamar directamente al extractor
2. **Activar caché** (`use_cache=True`) para evitar reprocesamiento
3. **Usar DeepSeek R1** para mejor calidad de salida
4. **Especificar target_language** si no es español
5. **Manejar excepciones** siempre que se trabaje con PDFs

### Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `Connection refused` | Ollama no está ejecutándose | `ollama serve` |
| `Model not found` | Modelo no descargado | `ollama pull deepseek-r1:latest` |
| `PDF has no pages` | PDF corrupto o vacío | Verificar archivo PDF |
| `JSON invalid` | Respuesta de Ollama malformada | JSONValidator lo corrige automáticamente |
| `Out of memory` | PDF muy largo | Reducir `MAX_CHARS_PER_CHUNK` |

---

**Última actualización:** Enero 2025
