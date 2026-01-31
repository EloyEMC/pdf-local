#!/usr/bin/env python3
"""
Procesa textos extraídos en lotes para mayor control.
Ejemplo: python process_texts_batch.py 100  (procesa 100 textos)
"""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Importar la función de process_extracted_texts
from scripts.process_extracted_texts import main as process_main


if __name__ == "__main__":
    # Cantidad por lote (por defecto 50)
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 50

    print(f"\n{'='*80}")
    print(f"PROCESANDO LOTE DE {batch_size} TEXTOS")
    print(f"{'='*80}\n")

    try:
        process_main(cantidad=batch_size)
    except KeyboardInterrupt:
        print("\n\n⚠️  Lote interrumpido")
