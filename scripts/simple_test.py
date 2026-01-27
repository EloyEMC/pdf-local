#!/usr/bin/env python3
import os, sys, sqlite3
from pathlib import Path
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils import extract_pdf_text, extract_bc3_from_pdf

# Usar el primer PDF
pdf_path = "/Volumes/WEBS/disano-scraper/data/output/fichas_tecnicas/Accesorio de columna/42695400.pdf"
codigo = "42695400"
db_path = os.path.join(project_root, "database", "tarifa_disano.db")

print(f"🔄 Procesando: {codigo}")
print(f"📁 PDF: {pdf_path}")

try:
    # Extraer texto
    texto = extract_pdf_text(pdf_path, remove_headers=True)
    print(f"✓ Texto: {len(texto)} chars")

    # Extraer BC3
    bc3 = extract_bc3_from_pdf(
        pdf_path=pdf_path,
        model="qwen3:4b",
        target_language='es',
        use_cache=True
    )
    print(f"✓ BC3: {bc3['product_type_name']}")

    # Guardar en BD
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE productos
        SET texto_extraido = ?, descripcion_corta_ollama = ?,
            descripcion_larga = ?, bc3_product_type = ?,
            ollama_processed = 1, ollama_processed_at = ?
        WHERE "CÓDIGO" = ?
    """, (
        texto[:50000],
        bc3['descripcion_corta'],
        bc3['descripcion_larga'],
        bc3['product_type'],
        datetime.now().isoformat(),
        codigo
    ))
    conn.commit()

    if cursor.rowcount > 0:
        print(f"✅ Guardado correctamente")
    else:
        print(f"⚠️  Producto no encontrado en BD")

    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
