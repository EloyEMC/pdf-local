#!/usr/bin/env python3
"""
Procesa textos extraídos con Anthropic Claude usando BATCH API (50% descuento).

La Batch API permite:
- Procesamiento asíncrono en paralelo
- 50% descuento en tokens
- Más rápido que procesamiento síncrono
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils.anthropic_batch_api import AnthropicBatchAPI

TEXTS_DIR = os.path.expanduser("~/Documents/extracted_texts")
OUTPUT_DIR = os.path.expanduser("~/Documents/processed_json")
MODEL = "claude-3-5-haiku-latest"
TARGET_LANGUAGE = "es"


def get_texts_to_process(cantidad=None):
    """Obtiene todos los textos extraídos que no han sido procesados con IA."""
    texts_dir = Path(TEXTS_DIR)
    output_dir = Path(OUTPUT_DIR)

    texts = []

    for json_file in texts_dir.glob("*.json"):
        if json_file.name.startswith('._'):
            continue

        codigo = json_file.stem

        # Saltar si ya está procesado
        final_json = output_dir / f"{codigo}.json"
        if final_json.exists():
            try:
                with open(final_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('descripcion_corta'):
                        continue
            except:
                pass

        texts.append(json_file)

    if cantidad:
        texts = texts[:cantidad]

    return texts


def create_batch_prompt(texto_extraido):
    """Crea el prompt para una solicitud batch."""
    prompt = f"""
Tu tarea es procesar una ficha técnica de una luminaria y generar una descripción en dos partes, separadas por `---`.

**Parte 1: Párrafo de Presupuesto**
Genera un único párrafo que empiece **obligatoriamente** con "Suministro y montaje de luminaria igual o equivalente a".
Este párrafo debe incluir:
- Nombre del producto y código.
- Descripción general, aplicaciones y materiales.
- Datos técnicos clave: Flujo Luminoso (lm), Potencia (W), y CCT (K).
- Si tiene Emergencia integrada, inclúyelo al final del párrafo.
- Siempre añade al final del párrafo "con certificaciones ISO 9001, ISO 14001, ISO 14002, y ISO 45001."

**Parte 2: Detalles Técnicos Estructurados**
Extrae el resto de la información técnica en formato de secciones y campos `Clave: Valor`.
Incluye la sección `INFORMACIÓN GENERAL` con los campos `Artículo`, `Código` y `Descripción` con valores simples y directos.

INFORMACIÓN GENERAL
DIMENSIONES Y PESO
INSTALACIÓN
CARACTERÍSTICAS ELÉCTRICAS Y CONTROLES
DATOS FOTOMÉTRICOS
CARACTERÍSTICAS MECÁNICAS
MATERIALES Y COLORES
NORMAS Y CUMPLIMIENTO
GARANTÍA

- En CARACTERÍSTICAS ELÉCTRICAS Y CONTROLES debe incluir el campo de Emergencia si está presente en la ficha técnica.
- En NORMAS Y CUMPLIMIENTO incluye siempre las certificaciones:
Certificado ISO 9001
Certificado ISO 14001
Certificado ISO 14002
Certificado ISO 45001
Certificado ISO 50001
Certificado que acredite el cumplimiento de las directivas RoHS y RAEE (WEEE)
Certificado que acredite la inscripción del fabricante en un Sistema Integrado de Gestión (SIG) de residuos
Certificado de Productor de Producto
Declaración Ambiental del Producto (DAP) se debe consultar siempre su disponibilidad para cada código, antes de realizar la prescripción

**Instrucciones Finales:**
- No añadas ninguna introducción o frase de saludo en tu respuesta.
- La respuesta debe empezar directamente con el párrafo de la Parte 1.

**Ficha técnica a procesar:**
{texto_extraido}
"""
    return prompt


def process_batch_with_api(texts, batch_api):
    """Procesa un lote de textos usando la Batch API de Anthropic."""
    print(f"\n🚀 Creando solicitud batch para {len(texts)} textos...")

    # Crear solicitudes batch
    requests_batch = []
    for json_file in texts:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            codigo = data.get('codigo', json_file.stem)
            texto = data.get('texto_extraido', '')

            if not texto:
                continue

            prompt = create_batch_prompt(texto)
            req = batch_api.create_batch_request(codigo, prompt)
            requests_batch.append(req)

        except Exception as e:
            print(f"   ⚠️  Error leyendo {json_file.name}: {str(e)[:50]}")
            continue

    if not requests_batch:
        print("❌ No hay solicitudes válidas para procesar")
        return

    print(f"✅ {len(requests_batch)} solicitudes creadas")
    print(f"💰 Costo estimado: ~${len(requests_batch) * 0.002:.2f} (50% descuento)")

    # Enviar batch
    print("\n📤 Enviando a Batch API...")
    batch_id = batch_api.submit_batch(requests_batch)
    print(f"✅ Batch enviado con ID: {batch_id}")

    # Esperar resultados
    final_status = batch_api.wait_for_completion(batch_id, check_interval=30, timeout=7200)

    # Procesar resultados
    results = batch_api.retrieve_results(batch_id)

    success_count = 0
    error_count = 0

    print(f"\n📝 Procesando {len(results)} resultados...")

    for result in results:
        custom_id = result["custom_id"]
        json_file = Path(TEXTS_DIR) / f"{custom_id}.json"

        # Leer datos originales
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            continue

        if result["result_type"] == "succeeded":
            # Extraer contenido del mensaje
            content = result["message"].get("content", [{}])[0].get("text", "")

            # Limpiar frases introductorias
            content = re.sub(
                r'^(?:Basándome en.*?:|Aquí (?:está|tienes).*?:|Claro,.*?:)\s*',
                '',
                content,
                flags=re.IGNORECASE
            ).strip()

            # Separar descripción corta y larga
            if '---' in content:
                parts = content.split('---', 1)
                desc_corta = parts[0].strip()
                desc_larga = parts[1].strip()
            else:
                desc_corta = content
                desc_larga = ""

            # Actualizar datos
            data.update({
                'descripcion_corta': desc_corta,
                'descripcion_larga': desc_larga,
                'ai_model': MODEL,
                'ai_batch_id': batch_id,
                'ai_processed_at': datetime.now().isoformat(),
                'success': True
            })

            success_count += 1
            print(f"   ✅ {custom_id}")
        else:
            error_msg = result.get("error", {}).get("message", "Error desconocido")
            data.update({
                'ai_error': error_msg,
                'ai_batch_id': batch_id,
                'ai_processed_at': datetime.now().isoformat(),
                'success': False
            })
            error_count += 1
            print(f"   ❌ {custom_id}: {error_msg[:50]}")

        # Guardar JSON final
        final_json = Path(OUTPUT_DIR) / f"{custom_id}.json"
        with open(final_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*80}")
    print(f"RESUMEN BATCH {batch_id}")
    print(f"{'='*80}")
    print(f"✅ Exitosos: {success_count}")
    print(f"❌ Errores: {error_count}")
    print(f"💰 Costo: ~${len(requests_batch) * 0.002:.2f} (50% descuento)")
    print(f"{'='*80}\n")


def main(cantidad=None):
    """Procesa textos usando Batch API."""
    print(f"\n{'='*80}")
    print(f"PROCESAMIENTO CON ANTHROPIC BATCH API (50% DESCUENTO)")
    print(f"{'='*80}\n")

    # Verificar API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY no está configurada")
        print("   Configúrala con: export ANTHROPIC_API_KEY=tu_api_key")
        return

    # Crear cliente Batch API
    print(f"🔧 Inicializando Batch API...")
    batch_api = AnthropicBatchAPI(api_key=api_key)
    print(f"✅ Batch API lista\n")

    # Obtener textos
    texts = get_texts_to_process(cantidad)
    total = len(texts)

    print(f"📋 Textos a procesar: {total}")
    print(f"💰 Costo estimado: ~${total * 0.002:.2f} (con 50% descuento)")

    if not texts:
        print("\n✅ No hay textos pendientes")
        return

    # Crear directorio de salida
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Procesar en lotes de 50 (límite de Batch API)
    batch_size = 50
    start_time = time.time()

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(texts) + batch_size - 1) // batch_size

        print(f"\n{'='*80}")
        print(f"🔄 LOTE {batch_num}/{total_batches} ({len(batch)} textos)")
        print(f"{'='*80}")

        process_batch_with_api(batch, batch_api)

        # Pequeña pausa entre lotes si no es el último
        if i + batch_size < len(texts):
            print(f"\n⏸️  Pausa de 5 segundos antes del siguiente lote...")
            time.sleep(5)

    elapsed = time.time() - start_time

    print(f"\n{'='*80}")
    print(f"✅ PROCESAMIENTO COMPLETADO")
    print(f"{'='*80}")
    print(f"⏱️  Tiempo total: {elapsed/60:.1f} minutos")
    print(f"💾 Resultados en: {OUTPUT_DIR}/")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None

    try:
        main(cantidad)
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        print(f"💾 Los resultados procesados hasta ahora están guardados en {OUTPUT_DIR}/")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
