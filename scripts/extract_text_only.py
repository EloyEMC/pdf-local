#!/usr/bin/env python3
"""
FASE 1: Extrae SOLO el texto de los PDFs sin usar IA.
Guarda el texto extraído en JSONs para procesamiento posterior.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils import extract_pdf_text

PDF_FOLDER = "/Volumes/WEBS/disano-scraper/data/output/fichas_tecnicas"
OUTPUT_DIR = os.path.expanduser("~/Documents/extracted_texts")


def get_all_pdfs(folder_path: str):
    """Obtiene todos los PDFs no procesados."""
    output_dir = Path(OUTPUT_DIR)
    pdfs = []

    for pdf_file in Path(folder_path).rglob("*.pdf"):
        # Filtrar archivos ocultos de macOS
        if pdf_file.name.startswith('._'):
            continue
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


def extract_text_from_pdf(codigo: str, ruta: str) -> dict:
    """Extrae solo el texto del PDF."""
    try:
        print(f"\n{'='*80}")
        print(f"📄 [{codigo}]")
        print(f"{'='*80}")

        start = time.time()

        # Extraer texto (sin IA)
        texto_extraido = extract_pdf_text(ruta, remove_headers=True)
        elapsed = time.time() - start

        print(f"✓ Texto extraído: {len(texto_extraido)} chars")
        print(f"⏱️  Tiempo: {elapsed:.2f}s")

        # Detectar tipología desde la ruta
        ruta_lower = ruta.lower()
        tipologia = "General"

        if "columna" in ruta_lower or "poste" in ruta_lower:
            tipologia = "Columna"
        elif "accesorio" in ruta_lower and ("mecanico" in ruta_lower or "iluminacion" in ruta_lower):
            tipologia = "Accesorio Mecánico"
        elif "accesorio electrico" in ruta_lower or "driver" in ruta_lower or "transformador" in ruta_lower:
            tipologia = "Equipo de Alimentación"
        elif "empotrable" in ruta_lower or "interior" in ruta_lower or "exterior" in ruta_lower:
            tipologia = "Luminaria"

        return {
            'codigo': codigo,
            'pdf_path': ruta,
            'texto_extraido': texto_extraido,
            'texto_length': len(texto_extraido),
            'tipologia_detectada': tipologia,
            'extracted_at': datetime.now().isoformat(),
            'success': True,
            'elapsed_time': elapsed
        }

    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        return {
            'codigo': codigo,
            'pdf_path': ruta,
            'success': False,
            'error': str(e),
            'extracted_at': datetime.now().isoformat()
        }


def main(cantidad: int = None):
    """Extrae texto de PDFs y guarda en JSON."""
    print(f"\n{'='*80}")
    print(f"FASE 1: EXTRACCIÓN DE TEXTO (SIN IA)")
    print(f"{'='*80}\n")

    print(f"📁 Carpeta: {PDF_FOLDER}")
    print(f"💾 Salida: {OUTPUT_DIR}\n")

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

        result = extract_text_from_pdf(codigo, ruta)

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
    print(f"RESUMEN DE EXTRACCIÓN")
    print(f"{'='*80}")
    print(f"✅ Exitosos: {success}")
    print(f"❌ Errores: {errors}")
    print(f"⏱️  Tiempo total: {total_time/60:.1f} min")
    if success > 0:
        print(f"⏱️  Media: {total_time/success:.2f} s/PDF")
    print(f"\n💾 Textos guardados en: {OUTPUT_DIR}/")
    print(f"📝 Lista para procesar con IA usando: process_extracted_texts.py")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None

    try:
        main(cantidad)
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        print(f"💾 Los textos extraídos hasta ahora están guardados en {OUTPUT_DIR}/")
