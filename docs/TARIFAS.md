# Sistema de Gestión de Tarifas

Sistema completo para importar tarifas de productos, procesar sus fichas técnicas en PDF con Ollama y exportar los resultados.

## Características

- ✅ Importar tarifas desde Excel o CSV
- ✅ Base de datos SQLite para almacenar productos
- ✅ Extracción automática de datos de PDFs con Ollama
- ✅ Exportar a Excel con todos los datos
- ✅ Interfaz web para gestionar productos

## Estructura de Datos

### Tabla `products`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | Primary key |
| code | String(100) | Código único del producto |
| name | String(500) | Nombre del producto |
| description | Text | Descripción |
| pdf_url | String(1000) | URL del PDF |
| price | Float | Precio |
| unit | String(50) | Unidad |
| processed | Boolean | Si ha sido procesado |
| processing_status | String(50) | Estado del procesamiento |

### Tabla `extracted_data`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | Primary key |
| product_id | Integer | Foreign key a products |
| codigo_producto | String(100) | Código extraído del PDF |
| nombre | String(500) | Nombre extraído |
| descripcion | Text | Descripción extraída |
| dimensiones_* | String(100) | Dimensiones (alto, ancho, etc.) |
| caracteristicas_electricas | String(100) | Tensión, potencia, etc. |
| materiales | Text | JSON array de materiales |
| normas | Text | JSON array de normas |
| ollama_model | String(100) | Modelo usado |
| processing_time | Float | Tiempo de procesamiento |

## Uso

### 1. Importar una Tarifa

**Formato del archivo Excel/CSV:**

| Código | Nombre | Descripción | PDF URL | Precio | Unidad |
|--------|--------|-------------|---------|--------|--------|
| PROD001 | Lámpara LED | Lámpara de 10W | https://ejemplo.com/ficha.pdf | 25.50 | U |

**Columnas requeridas:**
- `código` o `code`
- `nombre` o `name`

**Columnas opcionales:**
- `descripción` o `description`
- `pdf_url`, `pdf`, `url` o `ficha`
- `precio` o `price`
- `unidad`, `unit` o `u`

### 2. Procesar Productos

Cada producto se puede procesar individualmente:
1. Ve a `/tarifas`
2. Haz clic en "Procesar" junto al producto
3. El sistema descargará el PDF y extraerá los datos con Ollama

### 3. Exportar Datos

Exporta todos los productos con sus datos extraídos a Excel:
1. Ve a `/tarifas`
2. Haz clic en "Exportar Excel"
3. El archivo incluirá tanto los datos originales como los extraídos por Ollama

## Rutas de la Aplicación

| Ruta | Descripción |
|------|-------------|
| `/` | Conversor individual PDF a BC3 |
| `/tarifas` | Listado de productos |
| `/tarifas/upload` | Importar tarifa |
| `/tarifas/product/<id>` | Detalle de producto |
| `/tarifas/export` | Exportar a Excel |
| `/tarifas/product/<id>/process` | Procesar producto con Ollama |

## Base de Datos

La base de datos SQLite se guarda en:
```
/Volumes/WEBS/Pdf-local/database/tarifas.db
```

Para consultar la base de datos directamente:
```bash
sqlite3 database/tarifas.db
```

Ejemplos de consultas SQL:
```sql
-- Ver todos los productos
SELECT * FROM products;

-- Productos pendientes de procesar
SELECT * FROM products WHERE processed = 0;

-- Productos con PDF
SELECT code, name, pdf_url FROM products WHERE pdf_url IS NOT NULL;

-- Estadísticas
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as procesados,
    SUM(CASE WHEN processed = 0 THEN 1 ELSE 0 END) as pendientes
FROM products;
```

## API Endpoints

### Procesar Producto
```http
POST /tarifas/product/{id}/process
Content-Type: multipart/form-data

model=llama3.2:3b
```

Respuesta:
```json
{
  "success": true,
  "data": {
    "codigo_producto": "PROD001",
    "nombre": "Lámpara LED",
    "dimensiones": {...},
    ...
  }
}
```

## Ejemplo de Flujo Completo

1. **Preparar el archivo de tarifa**
   ```csv
   código,nombre,descripción,pdf_url,precio,unidad
   L001,Lámpara LED 10W,Lámpara empotrable,https://marca.com/fichas/l001.pdf,29.90,U
   L002,Lámpara LED 15W,Lámpara de alto rendimiento,https://marca.com/fichas/l002.pdf,35.50,U
   ```

2. **Importar la tarifa**
   - Ve a `http://localhost:5001/tarifas/upload`
   - Sube el archivo
   - El sistema importará los productos

3. **Procesar los PDFs**
   - Ve a `http://localhost:5001/tarifas`
   - Haz clic en "Procesar" en cada producto
   - Ollama extraerá los datos automáticamente

4. **Exportar los resultados**
   - Haz clic en "Exportar Excel"
   - Obtendrás un archivo con todos los datos originales + extraídos

## Notas

- Los PDFs pueden ser URLs o archivos locales
- Ollama debe estar corriendo (`ollama serve`)
- Se recomienda el modelo `llama3.2:3b` para速度快
- Los datos extraídos se guardan incluso si falla el procesamiento parcial
- Puedes reprocesar un producto múltiples veces
