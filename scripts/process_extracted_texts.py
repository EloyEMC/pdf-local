#!/usr/bin/env python3
"""
FASE 2: Procesa los textos extraídos con IA.
Lee los JSONs con texto extraído y genera las descripciones BC3.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils.bc3_extractor import BC3Extractor
from app.utils.ollama_client import OllamaClient

TEXTS_DIR = os.path.expanduser("~/Documents/extracted_texts")
OUTPUT_DIR = os.path.expanduser("~/Documents/processed_json")
MODEL = "deepseek-r1:latest"
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
            # Verificar si tiene descripción_corta (procesado con IA)
            try:
                with open(final_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('descripcion_corta'):
                        continue  # Ya procesado con IA
            except:
                pass  # Reintentar si hay error

        texts.append(json_file)

    return texts


def process_text_with_ai(json_file: Path) -> dict:
    """Procesa un texto extraído con IA."""
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

        # Crear extractor BC3
        extractor = BC3Extractor(model=MODEL, use_cache=True, timeout=600)

        # Detectar tipología desde la ruta
        pdf_path = data.get('pdf_path', '')

        # Extraer datos BC3 usando el texto ya extraído
        result = extractor.extract(
            pdf_text=texto,
            pdf_path=pdf_path,
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
            'ollama_model': MODEL,
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
    """Procesa textos extraídos con IA."""
    print(f"\n{'='*80}")
    print(f"FASE 2: PROCESAMIENTO CON IA")
    print(f"{'='*80}\n")

    print(f"📁 Entrada: {TEXTS_DIR}")
    print(f"💾 Salida: {OUTPUT_DIR}")
    print(f"🤖 Modelo: {MODEL}\n")

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

    # Procesar
    success = 0
    errors = 0
    total_time = 0

    for i, json_file in enumerate(texts, 1):
        codigo = json_file.stem

        print(f"\n[{i}/{len(texts)}] {codigo}", end="")

        result = process_text_with_ai(json_file)

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

        # Pequeña pausa para no sobrecalentar
        if i < len(texts):
            time.sleep(2)

    # Resumen
    print(f"\n{'='*80}")
    print(f"RESUMEN DE PROCESAMIENTO IA")
    print(f"{'='*80}")
    print(f"✅ Exitosos: {success}")
    print(f"❌ Errores: {errors}")
    print(f"⏱️  Tiempo total: {total_time/60:.1f} min")
    if success > 0:
        print(f"⏱️  Media: {total_time/success:.1f} s/texto")
    print(f"\n💾 Resultados guardados en: {OUTPUT_DIR}/")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv[1]) > 1 and sys.argv[1].isdigit() else None

    # Iniciar Ollama si no está corriendo
    print("🔍 Verificando Ollama...")
    try:
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'ollama.*serve'], capture_output=True)
        if result.returncode != 0:
            print("⚠️  Ollama no está corriendo. Inícialo con: ollama serve")
            sys.exit(1)
    except:
        pass

    try:
        main(cantidad)
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        print(f"💾 Los resultados procesados hasta ahora están guardados en {OUTPUT_DIR}/")
