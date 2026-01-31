#!/usr/bin/env python3
"""
Reintenta procesar los PDFs que fallaron.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils import extract_pdf_text, extract_bc3_from_pdf
from app.utils.ollama_client import OllamaClient

PDF_FOLDER = "/Volumes/WEBS/disano-scraper/data/output/fichas_tecnicas"
OUTPUT_DIR = os.path.expanduser("~/Documents/processed_json")
MODEL = "deepseek-r1:latest"
TARGET_LANGUAGE = "es"


def find_pdf_by_codigo(codigo: str, pdf_folder: str) -> str:
    """Busca un PDF por su código en la carpeta de PDFs."""
    pdf_path = Path(pdf_folder)

    # Primero intentar búsqueda exacta
    for pdf_file in pdf_path.rglob("*.pdf"):
        if pdf_file.name.startswith('._'):
            continue
        if pdf_file.name.startswith('.'):
            continue

        # El nombre del archivo contiene el código
        if codigo in pdf_file.stem:
            return str(pdf_file)

    # Si no encuentra exacta, intentar con el código como nombre
    for pdf_file in pdf_path.rglob(f"{codigo}.pdf"):
        if pdf_file.name.startswith('._'):
            continue
        return str(pdf_file)

    return None


def retry_failed():
    """Reintenta procesar PDFs fallidos."""
    output_dir = Path(OUTPUT_DIR)
    failed_files = []

    # Buscar archivos fallidos
    for json_file in output_dir.glob("*.json"):
        if json_file.name.startswith('._'):
            continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                if not data.get('success'):
                    failed_files.append(json_file)
        except:
            pass

    if not failed_files:
        print("✅ No hay PDFs fallidos para reintentar")
        return

    print(f"🔄 Reintentando {len(failed_files)} PDFs fallidos...")
    print("="*80)

    client = OllamaClient(model=MODEL, use_cache=True, timeout=600)

    for i, json_file in enumerate(failed_files, 1):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            codigo = data.get('codigo', json_file.stem)

            # Intentar obtener el path del JSON primero
            pdf_path = data.get('pdf_path', '')

            # Si no existe o no es válido, buscar por código
            if not pdf_path or not os.path.exists(pdf_path):
                print(f"🔍 [{i}/{len(failed_files)}] {codigo}: Buscando PDF...")
                pdf_path = find_pdf_by_codigo(codigo, PDF_FOLDER)

                if not pdf_path:
                    print(f"   ❌ PDF no encontrado para el código {codigo}")
                    continue

                print(f"   ✅ PDF encontrado: {pdf_path}")

            print(f"🔄 [{i}/{len(failed_files)}] {codigo}")

            # Extraer datos BC3 directamente desde el PDF
            bc3_data = extract_bc3_from_pdf(
                pdf_path=pdf_path,
                model=MODEL,
                target_language=TARGET_LANGUAGE,
                use_cache=True,
                timeout=600
            )

            # Actualizar JSON
            data.update({
                'success': True,
                'pdf_path': pdf_path,  # Guardar el path para futuros reintentos
                'descripcion_corta': bc3_data['descripcion_corta'],
                'descripcion_larga': bc3_data['descripcion_larga'],
                'tipologia': bc3_data['product_type_name'],  # Usar la clave correcta
                'ollama_model': MODEL,
                'reintentado': True,
                'reintentado_at': datetime.now().isoformat()
            })

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"   ✅ Éxito: {bc3_data['product_type_name']}")

            # Pequeña pausa para no sobrecalentar
            if i < len(failed_files):
                time.sleep(2)

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "="*80)
    print(f"✅ Reintento completado")
    print(f"   Procesados: {len(failed_files)}")


if __name__ == "__main__":
    retry_failed()
