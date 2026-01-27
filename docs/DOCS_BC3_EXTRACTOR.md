# Sistema BC3 Extractor con Ollama

Documentación completa del sistema de extracción de datos BC3 utilizando Ollama para procesamiento local de fichas técnicas en PDF.

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Componentes Principales](#componentes-principales)
4. [Flujo de Trabajo](#flujo-de-trabajo)
5. [Guía de Uso](#guía-de-uso)
6. [Configuración](#configuración)
7. [API de Referencia](#api-de-referencia)
8. [Ejemplos Prácticos](#ejemplos-prácticos)
9. [Solución de Problemas](#solución-de-problemas)

---

## Descripción General

El **Sistema BC3 Extractor** es una solución integral para extraer información técnica de fichas de producto en PDF y generar descripciones estructuradas en formato BC3 (formato estándar español para presupuestos de construcción). El sistema utiliza **Ollama** para ejecutar modelos de lenguaje localmente, garantizando privacidad y procesamiento sin dependencias externas.

### Características Principales

- **Sistema de dos peticiones**: Genera descripción corta (párrafo de presupuesto) y descripción larga (detalles técnicos)
- **Detección automática de tipología**: Identifica automáticamente el tipo de producto (luminaria, equipo de alimentación, accesorio, columna)
- **Caché inteligente**: Almacena resultados basado en hash MD5 del PDF para evitar reprocesamiento
- **Validación JSON robusta**: Corrige automáticamente errores comunes en respuestas del modelo
- **Chunking inteligente**: Procesa PDFs largos dividiéndolos en fragmentos con superposición de contexto
- **Soporte multiidioma**: Genera descripciones en español, catalán, euskera o gallego

### Arquitectura

```
┌─────────────────┐
│   PDF Input     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│         PDF Extractor (pdfplumber)              │
│  - Extracción de texto                          │
│  - Eliminación de headers/footers               │
│  - Chunking inteligente                         │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│          BC3 Extractor                          │
│  - Detección de tipología                       │
│  - Sistema de dos peticiones a Ollama           │
│    1. Descripción corta (párrafo BC3)          │
│    2. Descripción larga (detalles técnicos)     │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│       Ollama Client                             │
│  - Comunicación con modelo local                │
│  - Gestión de caché                            │
│  - Validación de respuestas                     │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│       JSON Validator                            │
│  - Extracción de JSON                          │
│  - Corrección de errores                        │
│  - Validación de schema                        │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│       Cache Manager                             │
│  - Hash MD5 del PDF                            │
│  - TTL configurable                            │
│  - Invalidación selectiva                      │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│      Output BC3                                 │
│  - descripcion_corta (párrafo)                 │
│  - descripcion_larga (estructura técnica)       │
│  - product_type (tipología detectada)           │
└─────────────────────────────────────────────────┘
```

---

## Arquitectura del Sistema

### Flujo de Datos Completo

```
1. INPUT: PDF de ficha técnica
   │
   ├─> [PDF Extractor] Extrae texto del PDF
   │   ├─> Elimina cabeceras/pies comunes
   │   └─> Divide en chunks si > 5 páginas
   │
2. [Cache Manager] Verifica si ya existe resultado
   ├─> Calcula hash MD5 del PDF
   ├─> Busca en directorio cache/
   └─> Si existe y no expiró → RETURN CACHE
   │
3. [BC3 Extractor] Procesa el texto
   ├─> Detecta tipología (luminaria, equipo, etc.)
   │
   ├─> PETICIÓN 1: Descripción Corta
   │   ├─> Prompt: "Genera párrafo de presupuesto..."
   │   ├─> Template según tipología
   │   └─> Output: Párrafo BC3 (3-4 líneas)
   │
   ├─> PETICIÓN 2: Descripción Larga
   │   ├─> Prompt: "Extrae información técnica..."
   │   ├─> Secciones según tipología
   │   └─> Output: Estructura técnica (Clave: Valor)
   │
4. [JSON Validator] Valida y limpia
   ├─> Extrae JSON de respuesta
   ├─> Corrige errores comunes
   └─> Valida schema esperado
   │
5. [Cache Manager] Guarda resultado
   ├─> Archivo: {hash}_{modelo}.json
   └─> TTL: 24 horas por defecto
   │
6. OUTPUT: Diccionario BC3
   ├─> descripcion_corta: "Suministro y montaje de..."
   ├─> descripcion_larga: "INFORMACIÓN GENERAL\n..."
   ├─> product_type: "luminaria"
   └─> product_type_name: "Luminaria"
```

---

## Componentes Principales

### 1. BC3 Extractor (`bc3_extractor.py`)

Clase principal que coordina todo el proceso de extracción BC3.

**Responsabilidades:**
- Detectar tipología de producto automáticamente
- Coordinar las dos peticiones a Ollama
- Generar prompts especializados según tipología e idioma
- Limpiar y formatear respuestas

**Tipologías Soportadas:**

| Tipología | Keywords | Template |
|-----------|----------|----------|
| **Luminaria** | luminaria, lámpara, light, luminaire, led, fluorescente, arcón | "Suministro y montaje de luminaria igual o equivalente a" |
| **Equipo de Alimentación** | alimentación, power supply, driver, transformador, balasto | "Suministro y montaje de equipo de alimentación igual o equivalente a" |
| **Accesorio Mecánico** | soporte, bracket, accesorio, colgador, suspensión | "Suministro y montaje de accesorio mecánico igual o equivalente a" |
| **Columna** | columna, poste, báculo, columna luminosa | "Suministro y montaje de columna igual o equivalente a" |
| **General** | (default) | "Suministro y montaje de producto igual o equivalente a" |

### 2. PDF Extractor (`pdf_extractor.py`)

Maneja la extracción de texto de PDFs usando `pdfplumber`.

**Características:**
- Extracción de texto con pdfplumber
- Eliminación automática de cabeceras y pies de página
- Chunking inteligente para PDFs largos
- Superposición de contexto entre chunks (500 caracteres)

**Constantes de Configuración:**
```python
MAX_CHARS_PER_CHUNK = 8000  # Máximo por chunk
OVERLAP_CHARS = 500         # Superposición
MAX_PAGES_PER_CHUNK = 5     # Umbral para chunking
```

### 3. Ollama Client (`ollama_client.py`)

Cliente para comunicarse con Ollama localmente.

**Funcionalidades:**
- Chat simple con el modelo
- Extracción de datos con validación JSON
- Procesamiento de chunks con merge inteligente
- Generación de estructura BC3

**Modelos Soportados:**
- `llama3.2:latest` (recomendado)
- `llama3.2:3b` (más rápido)
- `mistral:7b`
- `phi3`
- `gemma:7b`

### 4. Cache Manager (`cache_manager.py`)

Sistema de caché basado en hash MD5 del PDF.

**Características:**
- Hash MD5 único por PDF
- TTL configurable (24 horas por defecto)
- Invalidación selectiva por PDF o global
- Estadísticas de uso

**Estructura de Cache:**
```
cache/
├── {md5_hash}_llama3.2_latest.json
├── {md5_hash}_mistral_7b.json
└── ...
```

### 5. JSON Validator (`json_validator.py`)

Valida y corrige respuestas JSON de Ollama.

**Correcciones Automáticas:**
- Eliminación de bloques markdown (```json...```)
- Comillas simples a dobles
- Trailing commas
- Comentarios de JavaScript
- Valores sin comillas
- Validación de schema

**Schema Esperado:**
```python
{
    "codigo_producto": str,
    "nombre": str,
    "descripcion": str,
    "dimensiones": dict,
    "caracteristicas_electricas": dict,
    "materiales": list,
    "colores": list,
    "normas": list,
    "garantia": str | None,
    "observaciones": str | None
}
```

---

## Flujo de Trabajo

### Proceso Paso a Paso

#### 1. Extracción del PDF

```python
from app.utils.pdf_extractor import extract_pdf_text_chunked

chunks = extract_pdf_text_chunked("ficha_tecnica.pdf")
# Resultado:
# [
#   {
#     "text": "texto del chunk 1...",
#     "pages": [1, 2, 3],
#     "chunk_id": 0,
#     "is_complete": False
#   },
#   ...
# ]
```

#### 2. Detección de Tipología

El sistema analiza el texto del PDF buscando palabras clave:

```python
pdf_text = "Luminaria LED de alta eficiencia..."
# → Detecta "luminaria" → Tipología: Luminaria
```

#### 3. Primera Petición: Descripción Corta

Genera un párrafo de presupuesto BC3:

```
Prompt:
"Genera un único párrafo de presupuesto para BC3.
El párrafo debe empezar obligatoriamente con:
'Suministro y montaje de luminaria igual o equivalente a'
..."

Respuesta Ollama:
"Suministro y montaje de luminaria igual o equivalente a
MODELO X-200 (Código: LUM-200) luminaria LED de alta
eficiencia para alumbrado público con óptica asimétrica
y flujo luminoso de 15000 lm. IP66, IK10. con certificaciones
ISO 9001, ISO 14001, ISO 14002, y ISO 45001."
```

#### 4. Segunda Petición: Descripción Larga

Genera estructura técnica detallada:

```
Prompt:
"Extrae la información técnica detallada en formato estructurado.
Organiza la información en estas secciones:
- INFORMACIÓN GENERAL
- DIMENSIONES Y PESO
- INSTALACIÓN
- CARACTERÍSTICAS ELÉCTRICAS Y CONTROLES
..."
```

Respuesta Ollama:
```
INFORMACIÓN GENERAL
Artículo:     MODELO X-200
Código:      LUM-200

DIMENSIONES Y PESO
Longitud:     650 mm
Altura:       85 mm
Peso:         4.5 kg

INSTALACIÓN
Montaje:      Brazo万能
...
```

#### 5. Validación y Caché

```python
# Validar JSON
validated_data = JSONValidator.extract_and_validate(response)

# Guardar en caché
cache_manager.set(pdf_path, model, result)
```

---

## Guía de Uso

### Instalación de Dependencias

```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo recomendado
ollama pull llama3.2:latest

# Instalar dependencias Python
pip install pdfplumber ollama
```

### Uso Básico

#### Ejemplo 1: Extraer datos BC3 de un PDF

```python
from app.utils.pdf_extractor import extract_bc3_from_pdf

# Extraer datos BC3
result = extract_bc3_from_pdf(
    pdf_path="ficha_tecnica.pdf",
    model="llama3.2:latest",
    target_language="es",  # es, ca, eu, gl
    use_cache=True
)

# Resultado
print(result["descripcion_corta"])
# "Suministro y montaje de luminaria igual o equivalente a..."

print(result["descripcion_larga"])
# "INFORMACIÓN GENERAL\nArtículo: ...\n..."

print(result["product_type"])
# "luminaria"

print(result["product_type_name"])
# "Luminaria"
```

#### Ejemplo 2: Usar el extractor directamente

```python
from app.utils.bc3_extractor import BC3Extractor

# Crear extractor
extractor = BC3Extractor(
    model="llama3.2:latest",
    use_cache=True
)

# Extraer datos
pdf_text = open("ficha_tecnica.txt").read()
result = extractor.extract(
    pdf_text=pdf_text,
    pdf_path="ficha_tecnica.pdf",  # Opcional, para caché
    target_language="ca"  # Catalán
)

# Acceder a resultados
descripcion_corta = result["descripcion_corta"]
descripcion_larga = result["descripcion_larga"]
```

#### Ejemplo 3: Procesar múltiples PDFs

```python
from pathlib import Path
from app.utils.pdf_extractor import extract_bc3_from_pdf

pdf_dir = Path("fichas_tecnicas")
results = []

for pdf_file in pdf_dir.glob("*.pdf"):
    print(f"Procesando {pdf_file.name}...")

    try:
        result = extract_bc3_from_pdf(
            pdf_path=str(pdf_file),
            target_language="es"
        )
        results.append({
            "file": pdf_file.name,
            "data": result
        })
    except Exception as e:
        print(f"Error: {e}")

# Guardar resultados
import json
with open("resultados_bc3.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
```

#### Ejemplo 4: Trabajo sin caché

```python
from app.utils.pdf_extractor import extract_bc3_from_pdf

# Forzar reprocesamiento
result = extract_bc3_from_pdf(
    pdf_path="ficha_tecnica.pdf",
    use_cache=False  # Ignorar caché existente
)
```

### Uso Avanzado

#### Gestión de Caché

```python
from app.utils.cache_manager import CacheManager

# Crear gestor de caché
cache = CacheManager(
    cache_dir="mi_cache",
    ttl_hours=48  # 48 horas
)

# Obtener información del caché
info = cache.get_cache_info()
print(f"Archivos cacheados: {info['cached_files']}")
print(f"Tamaño total: {info['total_size_mb']} MB")

# Invalidar caché de un PDF específico
cache.invalidate("ficha_tecnica.pdf")

# Invalidar todo el caché
cache.invalidate()
```

#### Validación JSON

```python
from app.utils.json_validator import JSONValidator

# Respuesta de Ollama con markdown
response = """```json
{
    "nombre": "Luminaria X-200",
    "codigo": "LUM-200",
}
```"""

# Extraer y validar JSON
data = JSONValidator.extract_and_validate(response)
# Resultado: {"nombre": "Luminaria X-200", "codigo": "LUM-200", ...}

# Validación parcial
partial_data = {
    "nombre": "Producto",
    "codigo": "PROD-001"
}

validated = JSONValidator.validate_partial(
    partial_data,
    required_fields=["nombre", "codigo"]
)
```

#### Procesamiento de PDFs largos

```python
from app.utils.pdf_extractor import extract_pdf_text_chunked
from app.utils.ollama_client import OllamaClient

# Extraer en chunks
chunks = extract_pdf_text_chunked("manual_completo.pdf")

# Información de chunks
for chunk in chunks:
    print(f"Chunk {chunk['chunk_id']}: páginas {chunk['pages']}")
    print(f"Longitud: {len(chunk['text'])} caracteres")
    print(f"Completo: {chunk['is_complete']}")

# Procesar con Ollama
client = OllamaClient()
data = client.extract_data_from_pdf_chunked(chunks)
```

---

## Configuración

### Configuración de Modelos Ollama

```python
# En ollama_client.py o en tu código
MODEL = "llama3.2:latest"

# Alternativas según necesidades:
# - llama3.2:latest (recomendado, mejor calidad)
# - llama3.2:3b (más rápido, menos calidad)
# - mistral:7b (buen balance)
# - phi3 (muy rápido, decente calidad)
# - gemma:7b (alternativa a mistral)
```

### Configuración de Chunking

```python
# En pdf_extractor.py
MAX_CHARS_PER_CHUNK = 8000  # Caracteres máximos por chunk
OVERLAP_CHARS = 500         # Caracteres de superposición
MAX_PAGES_PER_CHUNK = 5     # Páginas máximas sin chunking

# Ajustar según necesidades:
# - PDFs cortos: aumentar MAX_PAGES_PER_CHUNK a 10
# - Modelos pequeños: reducir MAX_CHARS_PER_CHUNK a 5000
# - Más contexto: aumentar OVERLAP_CHARS a 1000
```

### Configuración de Caché

```python
from app.utils.cache_manager import CacheManager

cache = CacheManager(
    cache_dir="./cache",  # Directorio de caché
    ttl_hours=24          # Tiempo de vida en horas
)

# TTL según uso:
# - Desarrollo: ttl_hours=1 (caché corto)
# - Producción: ttl_hours=168 (una semana)
# - Testing: ttl_hours=0 (siempre invalidar)
```

### Configuración de Idiomas

```python
# Idiomas soportados
IDIOMAS = {
    'es': 'Español',      # Por defecto
    'ca': 'Catalán',      # Cataluña
    'eu': 'Euskera',      # País Vasco
    'gl': 'Gallego'       # Galicia
}

# Uso:
result = extract_bc3_from_pdf(
    pdf_path="ficha.pdf",
    target_language='ca'  # Catalán
)
```

---

## API de Referencia

### BC3Extractor

#### `__init__(model: str, use_cache: bool)`

Inicializa el extractor BC3.

**Parámetros:**
- `model`: Modelo de Ollama a usar (default: "llama3.2:latest")
- `use_cache`: Si True, usa caché (default: True)

**Ejemplo:**
```python
extractor = BC3Extractor(model="llama3.2:latest", use_cache=True)
```

#### `extract(pdf_text: str, pdf_path: str, target_language: str) -> Dict[str, Any]`

Extrae datos del PDF usando dos peticiones separadas.

**Parámetros:**
- `pdf_text`: Texto extraído del PDF
- `pdf_path`: Ruta del PDF (para caché, opcional)
- `target_language`: Idioma de destino ('es', 'ca', 'eu', 'gl')

**Retorna:**
```python
{
    'descripcion_corta': str,      # Párrafo BC3
    'descripcion_larga': str,      # Estructura técnica
    'product_type': str,           # Tipo (luminaria, equipo, etc.)
    'product_type_name': str       # Nombre legible
}
```

**Ejemplo:**
```python
result = extractor.extract(
    pdf_text=pdf_text,
    pdf_path="ficha.pdf",
    target_language="es"
)
```

### PDF Extractor

#### `extract_pdf_text(pdf_path: str, remove_headers: bool) -> str`

Extrae el texto de un PDF.

**Parámetros:**
- `pdf_path`: Ruta al archivo PDF
- `remove_headers`: Si True, elimina cabeceras (default: True)

**Retorna:**
- `str`: Texto extraído del PDF

#### `extract_pdf_text_chunked(pdf_path: str, remove_headers: bool) -> List[Dict]`

Extrae texto del PDF en chunks si es muy largo.

**Retorna:**
```python
[
    {
        "text": str,           # Texto del chunk
        "pages": List[int],    # Páginas incluidas
        "chunk_id": int,       # ID del chunk
        "is_complete": bool    # Si es el último chunk
    },
    ...
]
```

#### `extract_bc3_from_pdf(pdf_path: str, model: str, target_language: str, use_cache: bool) -> Dict[str, Any]`

Extrae datos BC3 completo usando el sistema de dos peticiones.

**Parámetros:**
- `pdf_path`: Ruta al archivo PDF
- `model`: Modelo de Ollama (default: "llama3.2:latest")
- `target_language`: Idioma de destino (default: "es")
- `use_cache`: Si True, usa caché (default: True)

**Retorna:**
- `Dict`: Con `descripcion_corta`, `descripcion_larga`, `product_type`, `product_type_name`

### OllamaClient

#### `__init__(model: str, use_cache: bool)`

Inicializa el cliente de Ollama.

#### `chat(prompt: str, system_prompt: str) -> str`

Envía un mensaje al modelo y devuelve la respuesta.

#### `extract_data_from_pdf(pdf_text: str, pdf_path: str) -> Dict[str, Any]`

Extrae datos estructurados del texto de un PDF.

### CacheManager

#### `__init__(cache_dir: str, ttl_hours: int)`

Inicializa el gestor de caché.

**Parámetros:**
- `cache_dir`: Directorio de caché (default: "./cache")
- `ttl_hours`: Tiempo de vida en horas (default: 24)

#### `get(pdf_path: str, model: str) -> Optional[Dict[str, Any]]`

Obtiene resultado cacheado si existe y es válido.

#### `set(pdf_path: str, model: str, data: Dict[str, Any])`

Guarda resultado en caché.

#### `invalidate(pdf_path: str = None)`

Invalida caché (un PDF específico o todo).

#### `get_cache_info() -> Dict[str, Any]`

Obtiene información sobre el caché.

**Retorna:**
```python
{
    'cache_dir': str,           # Directorio de caché
    'cached_files': int,        # Número de archivos
    'total_size_bytes': int,    # Tamaño total en bytes
    'total_size_mb': float,     # Tamaño total en MB
    'ttl_hours': float          # TTL en horas
}
```

### JSONValidator

#### `extract_and_validate(response: str) -> Dict[str, Any]`

Extrae JSON de la respuesta de Ollama y lo valida.

#### `validate_partial(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]`

Valida datos parciales (no todos los campos son requeridos).

---

## Ejemplos Prácticos

### Ejemplo 1: Flujo Completo

```python
from pathlib import Path
from app.utils.pdf_extractor import extract_bc3_from_pdf
from app.utils.cache_manager import CacheManager

# Configurar
pdf_path = "fichas_tecnicas/luminaria_x200.pdf"
output_dir = Path("resultados_bc3")
output_dir.mkdir(exist_ok=True)

# Extraer datos
print(f"Procesando {pdf_path}...")
result = extract_bc3_from_pdf(
    pdf_path=pdf_path,
    model="llama3.2:latest",
    target_language="es",
    use_cache=True
)

# Guardar resultados
output_file = output_dir / f"{Path(pdf_path).stem}_bc3.txt"

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=== DESCRIPCIÓN CORTA (Párrafo BC3) ===\n\n")
    f.write(result["descripcion_corta"])
    f.write("\n\n")
    f.write("=== DESCRIPCIÓN LARGA (Detalles Técnicos) ===\n\n")
    f.write(result["descripcion_larga"])
    f.write("\n\n")
    f.write(f"=== METADATOS ===\n")
    f.write(f"Tipología: {result['product_type_name']}\n")
    f.write(f"Código tipo: {result['product_type']}\n")

print(f"✓ Resultado guardado en {output_file}")
```

**Salida esperada:**
```
Procesando fichas_tecnicas/luminaria_x200.pdf...
✓ Tipología detectada: Luminaria
  → Generando descripción corta...
  → Generando descripción larga...
✓ Resultado guardado en resultados_bc3/luminaria_x200_bc3.txt
```

### Ejemplo 2: Multiidioma

```python
from app.utils.pdf_extractor import extract_bc3_from_pdf

pdf_path = "ficha_tecnica.pdf"
idiomas = ['es', 'ca', 'eu', 'gl']

resultados = {}

for idioma in idiomas:
    print(f"Generando descripción en {idioma}...")

    result = extract_bc3_from_pdf(
        pdf_path=pdf_path,
        target_language=idioma,
        use_cache=False  # Forzar reprocesamiento
    )

    resultados[idioma] = result

# Mostrar comparación
print("\n=== COMPARACIÓN DE IDIOMAS ===\n")
for idioma, result in resultados.items():
    print(f"\n[{idioma.upper()}]")
    print(result["descripcion_corta"][:100] + "...")
```

### Ejemplo 3: Procesamiento por Lotes

```python
from pathlib import Path
from app.utils.pdf_extractor import extract_bc3_from_pdf
import json

def procesar_lote(directorio_pdf, directorio_salida):
    """Procesa múltiples PDFs y genera resultados BC3."""

    pdf_dir = Path(directorio_pdf)
    out_dir = Path(directorio_salida)
    out_dir.mkdir(exist_ok=True)

    resultados = []
    errores = []

    for pdf_file in pdf_dir.glob("*.pdf"):
        print(f"\n{'='*60}")
        print(f"Procesando: {pdf_file.name}")
        print(f"{'='*60}")

        try:
            # Extraer datos BC3
            result = extract_bc3_from_pdf(
                pdf_path=str(pdf_file),
                target_language="es"
            )

            # Guardar archivo individual
            output_file = out_dir / f"{pdf_file.stem}_bc3.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result["descripcion_corta"])
                f.write("\n\n" + "="*60 + "\n\n")
                f.write(result["descripcion_larga"])

            # Agregar a resultados
            resultados.append({
                "archivo": pdf_file.name,
                "tipologia": result["product_type_name"],
                "output": str(output_file),
                "descripcion_corta": result["descripcion_corta"][:200] + "..."
            })

            print(f"✓ Completado: {result['product_type_name']}")

        except Exception as e:
            errores.append({
                "archivo": pdf_file.name,
                "error": str(e)
            })
            print(f"✗ Error: {e}")

    # Guardar resumen
    resumen = {
        "procesados": len(resultados),
        "errores": len(errores),
        "resultados": resultados,
        "lista_errores": errores
    }

    with open(out_dir / "resumen.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"RESUMEN:")
    print(f"  Procesados: {len(resultados)}")
    print(f"  Errores: {len(errores)}")
    print(f"  Salida: {out_dir}")
    print(f"{'='*60}")

# Uso
procesar_lote(
    directorio_pdf="fichas_tecnicas",
    directorio_salida="resultados_bc3"
)
```

### Ejemplo 4: Integración con API Flask

```python
from flask import Flask, request, jsonify
from app.utils.pdf_extractor import extract_bc3_from_pdf
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/api/extract_bc3', methods=['POST'])
def extract_bc3_api():
    """API endpoint para extraer datos BC3."""

    # Verificar archivo
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    # Guardar archivo
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Parámetros
    target_language = request.form.get('language', 'es')
    use_cache = request.form.get('cache', 'true').lower() == 'true'

    try:
        # Extraer datos BC3
        result = extract_bc3_from_pdf(
            pdf_path=filepath,
            target_language=target_language,
            use_cache=use_cache
        )

        # Limpiar archivo temporal
        os.remove(filepath)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        # Limpiar archivo temporal
        if os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)
```

**Uso con curl:**
```bash
curl -X POST http://localhost:5000/api/extract_bc3 \
  -F "file=@ficha_tecnica.pdf" \
  -F "language=ca" \
  -F "cache=true"
```

---

## Solución de Problemas

### Problema: Ollama no responde

**Síntomas:**
```
Error comunicando con Ollama: Connection refused
```

**Soluciones:**

1. Verificar que Ollama está ejecutándose:
```bash
ollama list
```

2. Iniciar Ollama si no está corriendo:
```bash
ollama serve
```

3. Verificar que el modelo está instalado:
```bash
ollama list
# Si no aparece, instalar:
ollama pull llama3.2:latest
```

### Problema: PDF muy largo

**Síntomas:**
```
PDF con 50 páginas. Dividiendo en chunks...
Chunk 0: páginas [1, 2, 3, 4, 5], ~7500 caracteres
...
```

**Solución:**
El sistema automáticamente divide el PDF en chunks. Si necesitas ajustar el tamaño:

```python
# En pdf_extractor.py
MAX_CHARS_PER_CHUNK = 10000  # Aumentar para chunks más grandes
MAX_PAGES_PER_CHUNK = 8      # Aumentar para más páginas por chunk
```

### Problema: Caché no funciona

**Síntomas:**
```
✓ Usando resultado cacheado para ficha.pdf
```
Pero el resultado es antiguo.

**Soluciones:**

1. Invalidar caché del PDF específico:
```python
from app.utils.cache_manager import CacheManager
cache = CacheManager()
cache.invalidate("ficha.pdf")
```

2. Invalidar todo el caché:
```python
cache.invalidate()  # Sin parámetros
```

3. Reducir TTL:
```python
cache = CacheManager(ttl_hours=1)  # 1 hora en lugar de 24
```

4. Forzar reprocesamiento:
```python
result = extract_bc3_from_pdf(
    pdf_path="ficha.pdf",
    use_cache=False
)
```

### Problema: JSON inválido

**Síntomas:**
```
Error validando respuesta de Ollama: JSON inválido después de correcciones
```

**Soluciones:**

1. El validador ya corrige errores comunes automáticamente. Si persiste:

2. Probar con otro modelo:
```python
result = extract_bc3_from_pdf(
    pdf_path="ficha.pdf",
    model="mistral:7b"  # Modelo alternativo
)
```

3. Ajustar prompt del sistema:
```python
from app.utils.bc3_extractor import BC3Extractor

extractor = BC3Extractor(model="llama3.2:latest")
extractor.system_prompt = "Eres un experto... Responde SOLO con el JSON solicitado, sin texto adicional."

result = extractor.extract(pdf_text, pdf_path)
```

### Problema: Detección incorrecta de tipología

**Síntomas:**
```
✓ Tipología detectada: Producto General
```
Pero debería ser "Luminaria".

**Solución:**
Añadir keywords en `bc3_extractor.py`:

```python
"luminaria": {
    "keywords": [
        "luminaria", "lámpara", "light", "luminaire",
        "led", "fluorescente", "arcón",
        "nueva_keyword"  # Añadir aquí
    ],
    ...
}
```

### Problema: Memoria insuficiente

**Síntomas:**
```
Killed
```
o errores de memoria en Ollama.

**Soluciones:**

1. Usar modelo más pequeño:
```python
result = extract_bc3_from_pdf(
    pdf_path="ficha.pdf",
    model="llama3.2:3b"  # Modelo más ligero
)
```

2. Reducir tamaño de chunks:
```python
# En pdf_extractor.py
MAX_CHARS_PER_CHUNK = 5000  # Reducir de 8000
```

3. Procesar sin caché:
```python
result = extract_bc3_from_pdf(
    pdf_path="ficha.pdf",
    use_cache=False
)
```

---

## Mejores Prácticas

### 1. Selección de Modelos

| Caso de Uso | Modelo Recomendado | Razón |
|-------------|-------------------|--------|
| Producción (calidad) | `llama3.2:latest` | Mejor calidad de respuesta |
| Desarrollo/testing | `llama3.2:3b` | Más rápido, menos recursos |
| Balance | `mistral:7b` | Buen compromiso calidad/velocidad |
| Hardware limitado | `phi3` | Muy ligero, decente calidad |

### 2. Gestión de Caché

```python
# Desarrollo: Caché corto
cache = CacheManager(ttl_hours=1)

# Producción: Caché largo
cache = CacheManager(ttl_hours=168)  # 1 semana

# Testing: Sin caché
extractor = BC3Extractor(use_cache=False)
```

### 3. Manejo de Errores

```python
from app.utils.pdf_extractor import extract_bc3_from_pdf

def safe_extract(pdf_path, max_retries=3):
    """Extracción con reintentos."""

    for intento in range(max_retries):
        try:
            return extract_bc3_from_pdf(
                pdf_path=pdf_path,
                target_language="es",
                use_cache=(intento == 0)  # Solo caché en primer intento
            )
        except Exception as e:
            if intento == max_retries - 1:
                raise
            print(f"Intento {intento + 1} falló: {e}")
            print("Reintentando...")

    return None
```

### 4. Validación de Resultados

```python
def validar_resultado_bc3(result):
    """Valida que el resultado tenga todos los campos."""

    campos_requeridos = [
        'descripcion_corta',
        'descripcion_larga',
        'product_type',
        'product_type_name'
    ]

    for campo in campos_requerios:
        if campo not in result:
            raise ValueError(f"Campo faltante: {campo}")

    # Validar longitud mínima
    if len(result['descripcion_corta']) < 50:
        print("⚠ Advertencia: Descripción corta muy corta")

    if len(result['descripcion_larga']) < 100:
        print("⚠ Advertencia: Descripción larga muy corta")

    return True
```

### 5. Logging y Monitoreo

```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bc3_extractor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('BC3Extractor')

# Usar en el código
try:
    result = extract_bc3_from_pdf(pdf_path)
    logger.info(f"Extracción exitosa: {result['product_type_name']}")
except Exception as e:
    logger.error(f"Error extrayendo {pdf_path}: {e}")
```

---

## Referencias Técnicas

### Formato BC3

El formato BC3 es el estándar español para intercambio de datos de presupuestos de construcción. Los principales tipos de registros son:

- **~V**: Versión del formato
- **~C**: Conceptos/Capítulos
- **~D**: Desglose de precios
- **~T**: Textos/Observaciones
- **~U**: Unidades
- **~P**: Precios

### Modelos Ollama Soportados

| Modelo | Parámetros | RAM Recomendada | Caso de Uso |
|--------|-----------|-----------------|-------------|
| llama3.2:latest | ~9B | 8GB | Producción |
| llama3.2:3b | 3B | 4GB | Desarrollo |
| mistral:7b | 7B | 8GB | Balance |
| phi3 | 3.8B | 4GB | Hardware limitado |
| gemma:7b | 7B | 8GB | Alternativa |

### Dependencias del Sistema

```
pdfplumber  - Extracción de texto de PDFs
ollama      - Cliente Python para Ollama
hashlib     - Generación de hash MD5
json        - Validación y manipulación JSON
re          - Expresiones regulares para limpieza
datetime    - Gestión de TTL de caché
```

---

## Licencia y Créditos

Este sistema está basado en el prompt original de Claude Haaku para generación de descripciones BC3, adaptado para funcionar con modelos Ollama locales.

**Autor:** Claude (Anthropic)
**Año:** 2025
**Versión:** 1.0

---

## Soporte y Contribuciones

Para reportar problemas o sugerir mejoras, contactar con el equipo de desarrollo o abrir un issue en el repositorio del proyecto.

**Documentación generada:** 2025-01-26
**Versión del sistema:** 1.0.0
