#!/usr/bin/env python3
"""
Ejemplo de uso del extractor BC3 con dos peticiones a Ollama.

Este script demuestra cómo usar el nuevo extractor basado en el prompt de Haaku.
"""

import sys
import os

# Asegurar que estamos en el directorio correcto (el script está en tests/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils import extract_bc3_from_pdf, BC3Extractor


def test_bc3_extractor(pdf_path: str, target_language: str = 'es'):
    """
    Prueba el extractor BC3 con un PDF.

    Args:
        pdf_path: Ruta al archivo PDF
        target_language: Idioma (es, ca, eu, gl)
    """
    print(f"\n{'='*60}")
    print(f"Extractor BC3 - Dos Peticiones")
    print(f"{'='*60}\n")

    print(f"📄 PDF: {pdf_path}")
    print(f"🌐 Idioma: {target_language}")
    print(f"\nProcesando...\n")

    try:
        # Extraer datos usando el extractor BC3
        result = extract_bc3_from_pdf(
            pdf_path=pdf_path,
            model="deepseek-r1:latest",
            target_language=target_language,
            use_cache=True
        )

        print(f"✓ Tipología detectada: {result['product_type_name']}")
        print(f"\n{'─'*60}")
        print(f"PARTE 1: DESCRIPCIÓN CORTA (Párrafo de Presupuesto)")
        print(f"{'─'*60}")
        print(result['descripcion_corta'])

        print(f"\n{'─'*60}")
        print(f"PARTE 2: DESCRIPCIÓN LARGA (Detalles Técnicos)")
        print(f"{'─'*60}")
        print(result['descripcion_larga'])

        print(f"\n{'='*60}\n")

        return result

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_with_text(pdf_text: str, target_language: str = 'es'):
    """
    Prueba el extractor BC3 directamente con texto.

    Args:
        pdf_text: Texto extraído del PDF
        target_language: Idioma (es, ca, eu, gl)
    """
    print(f"\n{'='*60}")
    print(f"Extractor BC3 - Desde Texto")
    print(f"{'='*60}\n")

    try:
        extractor = BC3Extractor(model="llama3.2:3b", use_cache=True)
        result = extractor.extract(pdf_text, target_language=target_language)

        print(f"✓ Tipología: {result['product_type_name']}")
        print(f"\n{'─'*60}")
        print(f"PARTE 1: DESCRIPCIÓN CORTA")
        print(f"{'─'*60}")
        print(result['descripcion_corta'])

        print(f"\n{'─'*60}")
        print(f"PARTE 2: DESCRIPCIÓN LARGA")
        print(f"{'─'*60}")
        print(result['descripcion_larga'])

        print(f"\n{'='*60}\n")

        return result

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Ejemplo 1: Probar con un PDF
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        lang = sys.argv[2] if len(sys.argv) > 2 else 'es'
        test_bc3_extractor(pdf_file, lang)
    else:
        # Ejemplo 2: Probar con texto de ejemplo
        ejemplo_texto = """
        Luminaria LED Saturno 320
        Código: 330730-07

        Características:
        - Flujo luminoso: 4500 lm
        - Potencia: 45W
        - Temperatura color: 4000K
        - Grado de protección: IP65
        - Vida útil: 50.000 h

        Dimensiones: 320mm diámetro x 85mm alto
        Material: Aluminio inyectado
        """

        print("Usando texto de ejemplo...\n")
        test_with_text(ejemplo_texto, 'es')
