#!/usr/bin/env python3
"""
Procesa todas las fichas técnicas y guarda resultados en JSON.
Luego usar otro script para actualizar la BD.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils import extract_pdf_text, extract_bc3_from_pdf

PDF_FOLDER = "/Volumes/WEBS/disano-scraper/data/output/fichas_tecnicas"
MODEL = "deepseek-r1:latest"  # Modelo más potente para evitar alucinaciones
TARGET_LANGUAGE = "es"
OUTPUT_DIR = os.path.expanduser("~/Documents/processed_json")


def get_all_pdfs(folder_path: str):
    """Obtiene todos los PDFs no procesados."""
    output_dir = Path(OUTPUT_DIR)
    pdfs = []

    for pdf_file in Path(folder_path).rglob("*.pdf"):
        # Filtrar archivos ocultos de macOS (._*)
        if pdf_file.name.startswith('._'):
            continue

        # Filtrar archivos que comienzan con '.' (ocultos)
        if pdf_file.name.startswith('.'):
            continue

        codigo = pdf_file.stem

        # Saltar si ya está procesado
        json_file = output_dir / f"{codigo}.json"
        if json_file.exists():
            continue

        pdfs.append({
            'codigo': codigo,
            'ruta': str(pdf_file)
        })

    return pdfs


def process_pdf(codigo: str, ruta: str) -> dict:
    """Procesa un PDF y retorna los datos."""
    try:
        print(f"\n{'='*80}")
        print(f"🔄 [{codigo}]")
        print(f"{'='*80}")

        start = time.time()

        # Extraer texto
        texto_extraido = extract_pdf_text(ruta, remove_headers=True)
        print(f"✓ Texto: {len(texto_extraido)} chars")

        # Extraer BC3
        bc3_data = extract_bc3_from_pdf(
            pdf_path=ruta,
            model=MODEL,
            target_language=TARGET_LANGUAGE,
            use_cache=True
        )

        elapsed = time.time() - start
        print(f"✓ {bc3_data['product_type_name']} ({elapsed:.1f}s)")

        return {
            'codigo': codigo,
            'ruta': ruta,
            'texto_extraido': texto_extraido[:50000],
            'descripcion_corta': bc3_data['descripcion_corta'],
            'descripcion_larga': bc3_data['descripcion_larga'],
            'product_type': bc3_data['product_type'],
            'processed_at': datetime.now().isoformat(),
            'model': MODEL,
            'success': True,
            'elapsed_time': elapsed
        }

    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        return {
            'codigo': codigo,
            'ruta': ruta,
            'success': False,
            'error': str(e),
            'processed_at': datetime.now().isoformat()
        }


def main(cantidad: int = None):
    """Procesa PDFs y guarda en JSON."""
    print(f"\n{'='*80}")
    print(f"PROCESADOR DE PDFs A JSON")
    print(f"{'='*80}\n")

    print(f"📁 Carpeta: {PDF_FOLDER}")
    print(f"💾 Salida: {OUTPUT_DIR}")
    print(f"🤖 Modelo: {MODEL}\n")

    # Crear directorio de salida
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Obtener PDFs
    pdfs = get_all_pdfs(PDF_FOLDER)
    total = len(pdfs)

    print(f"📋 Pendientes: {total}")

    if cantidad:
        pdfs = pdfs[:cantidad]
        print(f"📊 Procesando: {cantidad} PDFs")

    if not pdfs:
        print("\n✅ No hay PDFs pendientes")
        return

    # Procesar
    success = 0
    errors = 0
    total_time = 0

    for i, pdf_info in enumerate(pdfs, 1):
        codigo = pdf_info['codigo']
        ruta = pdf_info['ruta']

        print(f"\n[{i}/{len(pdfs)}] ", end="")

        result = process_pdf(codigo, ruta)

        # Limpiar placeholders si existen
        if isinstance(result.get('descripcion_corta'), str):
            import re
            # Eliminar placeholders [NOMBRE], [CÓDIGO]
            dc = result['descripcion_corta']
            dc = dc.replace('[NOMBRE]', '').replace('[CÓDIGO]', '').replace('  (', ' (Código: ')
            dc = re.sub(r'\s+', ' ', dc)  # Eliminar espacios extras
            result['descripcion_corta'] = dc.strip()

        if isinstance(result.get('descripcion_larga'), str):
            import re
            # Eliminar secciones de garantía vacías o con 0 años
            dl = result['descripcion_larga']
            dl = re.sub(r'GARANTÍA\s*\n\s*(?:Garantía posventa\s*:\s*0\s*(?:años?|yr)\s*)?\n', '', dl, flags=re.IGNORECASE)
            # Eliminar líneas vacías múltiples
            dl = re.sub(r'\n{3,}', '\n\n', dl)
            result['descripcion_larga'] = dl.strip()

        # Guardar en JSON
        json_file = Path(OUTPUT_DIR) / f"{codigo}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"💾 Guardado: {json_file.name}")

        if result['success']:
            success += 1
            total_time += result.get('elapsed_time', 0)
        else:
            errors += 1

    # Resumen
    print(f"\n{'='*80}")
    print(f"RESUMEN")
    print(f"{'='*80}")
    print(f"✅ Exitosos: {success}")
    print(f"❌ Errores: {errors}")
    print(f"⏱️  Tiempo total: {total_time/60:.1f} min")
    if success > 0:
        print(f"⏱️  Media: {total_time/success:.1f} s/PDF")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None

    try:
        main(cantidad)
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        print(f"💾 Los JSON procesados hasta ahora están guardados en {OUTPUT_DIR}/")
