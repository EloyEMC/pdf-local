# Changelog - PDF to BC3

Todos los cambios notables de este proyecto se documentan en este archivo.

## [3.0.0] - 2026-01-31

### Added - Procesamiento por Lotes con Anthropic
- **Nuevo sistema de procesamiento** con Claude Haiku API
- `app/utils/anthropic_extractor.py` - Cliente Anthropic con reintentos automáticos
- `app/utils/anthropic_batch_api.py` - Procesamiento por lotes optimizado
- `scripts/process_texts_batch_api.py` - Script principal de procesamiento
- Velocidad mejorada: ~18s/texto (15x más rápido que Ollama)
- Coste reducido: ~$0.50 cada 100 textos
- 100% tasa de éxito en 4,022 textos procesados

### Added - Flujo Híbrido PDF → JSON → BD
- `scripts/extract_text_only.py` - Extracción de texto sin IA
- `scripts/process_to_json.py` - Procesamiento a JSON intermedio
- `scripts/update_db_from_json.py` - Importación desde JSON
- Persistencia intermedia para evitar pérdida de datos
- Posibilidad de reanudar procesamientos interrumpidos

### Added - Scripts de Monitoreo
- `scripts/check_progress.py` - Verificar progreso de procesamiento
- `scripts/check_errors.py` - Revisar errores en procesamientos
- `scripts/retry_failed.py` - Reintentar procesamientos fallidos
- `scripts/monitor_progress.sh` - Monitoreo en tiempo real
- `scripts/generate_error_list.py` - Generar listado de errores

### Added - Exportación a Excel
- `scripts/export_to_excel.py` - Exportar base de datos completa
- Columnas renombradas para mejor legibilidad
- Ajuste automático de ancho de columnas
- Estadísticas incluidas en el Excel

### Changed - Base de Datos Optimizada
- Eliminados 9 campos obsoletos:
  - `ollama_processed`, `ollama_processed_at`, `descripcion_corta_ollama`
  - `ollama_model`, `descripcion_larga`
  - `texto_raw`, `texto_extraido`
  - `enlace_descarga`, `bc3_model`
- Rellenados 2,246 campos `img_url` usando patrón de `imagen`
- Cobertura de `img_url`: 66.5% → 93.6%
- Tamaño optimizado: 23 MB con VACUUM

### Changed - Mejoras en Documentación
- README.md actualizado con nueva información de Anthropic
- Nueva documentación: `docs/WORKFLOW_HIBRIDO.md`
- Comparativa de procesamiento (Ollama vs Anthropic)
- Estadísticas actualizadas de base de datos

### Fixed
- Error de UNIQUE constraint al recrear tablas
- Uso correcto de sintaxis `[CÓDIGO]` en SQLite
- Manejo de NaN en ajuste de ancho de columnas Excel
- Conversión correcta de letras de columnas (>26 columnas)

### Statistics
- **Total productos en BD**: 8,288
- **Productos con BC3**: 5,286 (63.8%)
- **Productos con imagen**: 7,758 (93.6%)
- **Textos procesados con Haiku**: 4,022
- **Tiempo total procesamiento**: ~20.2 horas
- **Coste total**: $20.11

---

## [2.0.0] - 2025-01-XX

### Added
- Sistema de caché MD5 para evitar reprocesamiento
- Chunking inteligente para PDFs largos
- Validación robusta de JSON con corrección automática
- Detección de tipología por ruta de archivo
- 9 certificaciones ISO obligatorias
- Soporte multiidioma (es, ca, eu, gl)

### Changed
- Migración de estructura monolítica a modular
- Nuevos utilitarios: `bc3_extractor.py`, `cache_manager.py`, `json_validator.py`
- Reorganización de scripts en carpetas temáticas

### Documentation
- README.md completo con instalación y uso
- docs/DOCS_BC3_EXTRACTOR.md
- docs/SCRAPER.md
- docs/TARIFAS.md

---

## [1.0.0] - 2024-XX-XX

### Initial Release
- Extracción básica de BC3 con Ollama
- Base de datos SQLite de productos Disano
- Interfaz web con Flask
- Scraper de Disano con Playwright
- Generación de archivos BC3

---

## Formato del Changelog

El formato se basa en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

### Categorías
- **Added** - Nuevas características
- **Changed** - Cambios en funcionalidad existente
- **Deprecated** - Características obsoletas (a eliminar)
- **Removed** - Características eliminadas
- **Fixed** - Correcciones de bugs
- **Security** - Issues de seguridad
