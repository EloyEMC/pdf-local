#!/usr/bin/env python3
"""
Verifica el estado del procesamiento de PDFs.
"""

import os
import sys
import sqlite3
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

PDF_FOLDER = "/Volumes/WEBS/disano-scraper/data/output/fichas_tecnicas"
JSON_DIR = "outputs/processed_json"
DB_PATH = os.path.join(project_root, "database", "tarifa_disano.db")


def count_pdfs():
    """Cuenta PDFs reales (sin archivos ocultos)."""
    count = 0
    for pdf_file in Path(PDF_FOLDER).rglob("*.pdf"):
        # Filtrar archivos ocultos
        if pdf_file.name.startswith('._'):
            continue
        if pdf_file.name.startswith('.'):
            continue
        count += 1
    return count


def count_jsons():
    """Cuenta JSONs procesados."""
    json_dir = Path(JSON_DIR)
    if not json_dir.exists():
        return 0, 0

    json_files = list(json_dir.glob("*.json"))

    # Contar exitosos y fallidos
    success = 0
    failed = 0

    for json_file in json_files:
        try:
            import json
            with open(json_file, 'r') as f:
                data = json.load(f)
                if data.get('success'):
                    success += 1
                else:
                    failed += 1
        except:
            failed += 1

    return success, failed


def count_db_processed():
    """Cuenta productos procesados en BD."""
    if not os.path.exists(DB_PATH):
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM productos WHERE ollama_processed = 1')
    count = cursor.fetchone()[0]
    conn.close()

    return count


def main():
    """Muestra estado del procesamiento."""
    print(f"\n{'='*80}")
    print(f"ESTADO DEL PROCESAMIENTO")
    print(f"{'='*80}\n")

    # Contar PDFs
    total_pdfs = count_pdfs()
    print(f"📁 Total PDFs: {total_pdfs}")

    # Contar JSONs
    json_success, json_failed = count_jsons()
    total_jsons = json_success + json_failed
    print(f"📊 JSONs generados: {total_jsons}")
    print(f"   ✅ Exitosos: {json_success}")
    print(f"   ❌ Fallidos: {json_failed}")

    # Contar BD
    db_processed = count_db_processed()
    print(f"💾 En base de datos: {db_processed}")

    # Calcular pendientes
    pending = total_pdfs - db_processed
    print(f"\n⏳ Pendientes de procesar: {pending}")

    # Progreso
    if total_pdfs > 0:
        progress = (db_processed / total_pdfs) * 100
        print(f"📈 Progreso: {progress:.1f}%")

    # Espacio en disco
    json_dir = Path(JSON_DIR)
    if json_dir.exists():
        size = sum(f.stat().st_size for f in json_dir.glob("*.json") if f.is_file())
        size_mb = size / (1024 * 1024)
        print(f"💾 Tamaño JSONs: {size_mb:.1f} MB")

    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
