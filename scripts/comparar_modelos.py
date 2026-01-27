#!/usr/bin/env python3
"""
Compara el rendimiento de diferentes modelos de Ollama en el mismo PDF.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils import extract_bc3_from_pdf


def comparar_modelos(pdf_path: str, target_language: str = 'es'):
    """
    Compara múltiples modelos con el mismo PDF.

    Args:
        pdf_path: Ruta al archivo PDF
        target_language: Idioma (es, ca, eu, gl)
    """
    modelos = [
        "llama3.2:latest",
        "deepseek-r1:latest",
    ]

    for modelo in modelos:
        print(f"\n{'='*80}")
        print(f"MODELO: {modelo}")
        print(f"{'='*80}\n")

        print(f"📄 PDF: {pdf_path}")
        print(f"🌐 Idioma: {target_language}")
        print(f"\nProcesando...\n")

        try:
            # Extraer datos usando el extractor BC3
            result = extract_bc3_from_pdf(
                pdf_path=pdf_path,
                model=modelo,
                target_language=target_language,
                use_cache=False  # No usar caché para comparar
            )

            print(f"✓ Tipología: {result['product_type_name']}")
            print(f"\n{'─'*60}")
            print(f"DESCRIPCIÓN CORTA")
            print(f"{'─'*60}")
            print(result['descripcion_corta'])

            print(f"\n{'─'*60}")
            print(f"DESCRIPCIÓN LARGA")
            print(f"{'─'*60}")
            print(result['descripcion_larga'])

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python comparar_modelos.py <ruta_pdf> [idioma]")
        print("Ejemplo: python comparar_modelos.py /ruta/a/pdf.pdf es")
        sys.exit(1)

    pdf_file = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else 'es'

    comparar_modelos(pdf_file, lang)
