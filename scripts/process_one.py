#!/usr/bin/env python3
"""
Procesa fichas técnicas de UNA EN UNA con modelo rápido.
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils import extract_pdf_text, extract_bc3_from_pdf

PDF_FOLDER = "/Volumes/WEBS/disano-scraper/data/output/fichas_tecnicas"
DB_PATH = os.path.join(project_root, "database", "tarifa_disano.db")
MODEL = "qwen3:4b"  # Modelo rápido (sin razonamiento)
TARGET_LANGUAGE = "es"


def get_next_pdf():
    """Obtiene el siguiente PDF sin procesar."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    pdfs = []
    for pdf_file in Path(PDF_FOLDER).rglob("*.pdf"):
        codigo = pdf_file.stem
        cursor.execute('SELECT ollama_processed FROM productos WHERE "CÓDIGO" = ? OR REFERENCIA = ?', (codigo, codigo))
        result = cursor.fetchone()

        if not result or not result[0]:
            pdfs.append((codigo, str(pdf_file)))

    conn.close()
    return pdfs


def process_pdf(codigo: str, ruta: str) -> bool:
    """Procesa un único PDF."""
    try:
        print(f"\n{'='*80}")
        print(f"🔄 [{codigo}]")
        print(f"{'='*80}")

        import time
        start = time.time()

        # Extraer texto
        texto_extraido = extract_pdf_text(ruta, remove_headers=True)
        print(f"✓ Texto: {len(texto_extraido)} chars")

        # Extraer BC3
        print(f"⏳ Ollama ({MODEL})...")
        bc3_data = extract_bc3_from_pdf(
            pdf_path=ruta,
            model=MODEL,
            target_language=TARGET_LANGUAGE,
            use_cache=True
        )

        elapsed = time.time() - start
        print(f"✓ {bc3_data['product_type_name']} ({elapsed:.1f}s)")

        # Guardar
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE productos
            SET texto_extraido = ?, descripcion_corta_ollama = ?,
                descripcion_larga = ?, bc3_product_type = ?,
                ollama_processed = 1, ollama_processed_at = ?
            WHERE "CÓDIGO" = ? OR REFERENCIA = ?
        """, (
            texto_extraido[:50000],
            bc3_data['descripcion_corta'],
            bc3_data['descripcion_larga'],
            bc3_data['product_type'],
            datetime.now().isoformat(),
            codigo, codigo
        ))
        conn.commit()
        conn.close()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        return False


if __name__ == "__main__":
    import time

    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1

    print(f"\n🚀 Procesando {cantidad} PDF(s) con {MODEL}\n")

    pdfs = get_next_pdf()
    print(f"📋 Pendientes: {len(pdfs)}\n")

    success = 0
    total_time = 0

    for i in range(min(cantidad, len(pdfs))):
        codigo, ruta = pdfs[i]
        start = time.time()

        if process_pdf(codigo, ruta):
            success += 1

        elapsed = time.time() - start
        total_time += elapsed

        print(f"✅ [{i+1}/{cantidad}] {elapsed:.1f}s (media: {total_time/(i+1):.1f}s)")

    # Stats
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM productos WHERE ollama_processed = 1')
    processed = cursor.fetchone()[0]
    conn.close()

    print(f"\n{'='*80}")
    print(f"✅ {success} procesados | 📊 Total en BD: {processed} | ⏱️ {total_time:.1f}s")
    print(f"{'='*80}")
