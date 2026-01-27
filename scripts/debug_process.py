#!/usr/bin/env python3
import os
import sys
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

PDF_FOLDER = "/Volumes/WEBS/disano-scraper/data/output/fichas_tecnicas"
DB_PATH = os.path.join(project_root, "database", "tarifa_disano.db")

print("=== DEBUG ===")
print(f"PDF_FOLDER existe: {os.path.exists(PDF_FOLDER)}")
print(f"DB_PATH existe: {os.path.exists(DB_PATH)}")
print(f"DB_PATH: {DB_PATH}")

# Contar PDFs
pdf_count = len(list(Path(PDF_FOLDER).rglob("*.pdf")))
print(f"PDFs encontrados: {pdf_count}")

# Ver primer PDF
first_pdf = next(Path(PDF_FOLDER).rglob("*.pdf"))
print(f"Primer PDF: {first_pdf}")
print(f"Código: {first_pdf.stem}")

# Verificar BD
import sqlite3
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM productos')
total = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM productos WHERE ollama_processed = 1')
processed = cursor.fetchone()[0]
print(f"Total productos en BD: {total}")
print(f"Procesados: {processed}")
conn.close()
