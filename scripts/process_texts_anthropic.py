#!/usr/bin/env python3
"""
Procesa textos extraídos con Anthropic Claude Haiku API.
Versión optimizada con API de Anthropic (15x más rápido que Ollama).
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import time
import random

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils.anthropic_extractor import AnthropicExtractor

TEXTS_DIR = os.path.expanduser("~/Documents/extracted_texts")
OUTPUT_DIR = os.path.expanduser("~/Documents/processed_json")
MODEL = "claude-3-5-haiku-latest"
TARGET_LANGUAGE = "es"


def get_texts_to_process():
    """Obtiene todos los textos extraídos que no han sido procesados con IA."""
    texts_dir = Path(TEXTS_DIR)
    output_dir = Path(OUTPUT_DIR)

    texts = []

    for json_file in texts_dir.glob("*.json"):
        if json_file.name.startswith('._'):
            continue

        codigo = json_file.stem

        # Saltar si ya está procesado en el directorio final
        final_json = output_dir / f"{codigo}.json"
        if final_json.exists():
            try:
                with open(final_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('descripcion_corta'):
                        continue  # Ya procesado con IA
            except:
                pass  # Reintentar si hay error

        texts.append(json_file)

    return texts


def process_text_with_ai(json_file: Path, extractor: AnthropicExtractor) -> dict:
    """Procesa un texto extraído con Anthropic Claude."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        codigo = data.get('codigo', json_file.stem)
        texto = data.get('texto_extraido', '')

        if not texto:
            raise ValueError("No hay texto extraído")

        print(f"\n{'='*80}")
        print(f"🤖 [{codigo}]")
        print(f"{'='*80}")
        print(f"📄 Texto: {len(texto)} chars")

        start = time.time()

        # Extraer datos BC3 usando Anthropic
        result = extractor.extract(
            pdf_text=texto,
            pdf_path=data.get('pdf_path'),
            target_language=TARGET_LANGUAGE
        )

        elapsed = time.time() - start

        print(f"✓ {result['product_type_name']} ({elapsed:.1f}s)")

        # Combinar datos
        final_data = {
            **data,  # Preservar todos los datos del texto extraído
            'descripcion_corta': result['descripcion_corta'],
            'descripcion_larga': result['descripcion_larga'],
            'product_type': result['product_type'],
            'tipologia': result['product_type_name'],
            'ai_model': result['model'],
            'ai_processed_at': datetime.now().isoformat(),
            'ai_processing_time': elapsed,
            'success': True
        }

        return final_data

    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        # Retornar datos con error pero preservando el texto extraído
        return {
            **data,
            'success': False,
            'ai_error': str(e),
            'ai_processed_at': datetime.now().isoformat()
        }


def main(cantidad: int = None):
    """Procesa textos extraídos con Anthropic Claude."""
    print(f"\n{'='*80}")
    print(f"PROCESAMIENTO CON ANTHROPIC CLAUDE HAIKU")
    print(f"{'='*80}\n")

    print(f"📁 Entrada: {TEXTS_DIR}")
    print(f"💾 Salida: {OUTPUT_DIR}")
    print(f"🤖 Modelo: {MODEL}")
    print(f"⚡ Velocidad: ~10s/PDF (15x más rápido que Ollama)\n")

    # Verificar API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ERROR: ANTHROPIC_API_KEY no está configurada")
        print("   Configúrala con: export ANTHROPIC_API_KEY=tu_api_key")
        return

    # Crear directorio de salida
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Obtener textos a procesar
    texts = get_texts_to_process()
    total = len(texts)

    print(f"📋 Textos a procesar: {total}")

    if cantidad:
        texts = texts[:cantidad]
        print(f"📊 Procesando: {cantidad} textos")

    if not texts:
        print("\n✅ No hay textos pendientes de procesar con IA")
        return

    # Crear extractor
    print(f"\n🔧 Inicializando Anthropic Claude...")
    extractor = AnthropicExtractor(model=MODEL)
    print(f"✅ Extractor listo\n")

    # Procesar
    success = 0
    errors = 0
    total_time = 0

    for i, json_file in enumerate(texts, 1):
        codigo = json_file.stem

        print(f"\n[{i}/{len(texts)}] {codigo}", end="")

        # Reintentar con backoff exponencial si hay errores de rate limit
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                result = process_text_with_ai(json_file, extractor)

                # Guardar en JSON final
                final_json = Path(OUTPUT_DIR) / f"{codigo}.json"
                with open(final_json, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                print(f"💾 Guardado: {final_json.name}")

                if result.get('success'):
                    success += 1
                    total_time += result.get('ai_processing_time', 0)
                else:
                    errors += 1

                # Éxito - salir del loop de reintentos
                break

            except Exception as e:
                error_msg = str(e).lower()
                # Si es error de rate limit, esperar y reintentar
                if 'rate' in error_msg or 'limit' in error_msg or '429' in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                        print(f"\n⏸️  Rate limit - esperando {wait_time:.1f}s antes de reintentar...")
                        time.sleep(wait_time)
                        continue
                # Si no es rate limit o se acabaron los reintentos, guardar error
                print(f"❌ Error: {str(e)[:100]}")

                # Guardar con error
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    result = {
                        **data,
                        'success': False,
                        'ai_error': str(e),
                        'ai_processed_at': datetime.now().isoformat()
                    }
                    final_json = Path(OUTPUT_DIR) / f"{codigo}.json"
                    with open(final_json, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                except:
                    pass

                errors += 1
                break

        # Pausa progresiva para no saturar la API
        # 1-2 segundos de espera aleatoria entre cada solicitud
        if i < len(texts):
            wait_time = random.uniform(1.0, 2.0)
            time.sleep(wait_time)

    # Resumen
    print(f"\n{'='*80}")
    print(f"RESUMEN DE PROCESAMIENTO")
    print(f"{'='*80}")
    print(f"✅ Exitosos: {success}")
    print(f"❌ Errores: {errors}")
    print(f"⏱️  Tiempo total: {total_time/60:.1f} min")
    if success > 0:
        print(f"⏱️  Media: {total_time/success:.1f} s/texto")
        print(f"💰 Costo estimado: ${success * 0.005:.2f} (aprox)")
    print(f"\n💾 Resultados guardados en: {OUTPUT_DIR}/")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None

    try:
        main(cantidad)
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        print(f"💾 Los resultados procesados hasta ahora están guardados en {OUTPUT_DIR}/")
