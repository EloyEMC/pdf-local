#!/usr/bin/env python3
"""
Genera un archivo de texto con la lista de PDFs que han fallado.
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

OUTPUT_DIR = "outputs/processed_json"
ERRORS_FILE = "outputs/pdf_errors_list.txt"


def generate_error_list():
    """Genera un archivo con la lista de errores."""
    json_dir = Path(OUTPUT_DIR)

    if not json_dir.exists():
        print(f"❌ Directorio no encontrado: {OUTPUT_DIR}")
        return

    errors = []
    error_codes = []

    # Buscar todos los JSONs con errores
    for json_file in json_dir.glob("*.json"):
        # Filtrar archivos ocultos de macOS
        if json_file.name.startswith('._'):
            continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                if not data.get('success'):
                    error_msg = data.get('error', 'Error desconocido')
                    codigo = data.get('codigo', json_file.stem)
                    processed_at = data.get('processed_at', 'N/A')

                    errors.append({
                        'codigo': codigo,
                        'error': error_msg,
                        'fecha': processed_at
                    })
                    error_codes.append(codigo)
        except Exception as e:
            pass

    # Ordenar por fecha (más recientes primero)
    errors.sort(key=lambda x: x['fecha'], reverse=True)

    # Guardar en archivo
    with open(ERRORS_FILE, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write(f"LISTADO DE PDFs CON ERRORES\n")
        f.write(f"Total: {len(errors)} PDFs\n")
        f.write("="*80 + "\n\n")

        for err in errors:
            f.write(f"CÓDIGO: {err['codigo']}\n")
            f.write(f"ERROR: {err['error']}\n")
            f.write(f"FECHA: {err['fecha']}\n")
            f.write("-"*80 + "\n\n")

        # Lista simple de códigos para copiar/pegar
        f.write("="*80 + "\n")
        f.write("LISTA SIMPLE DE CÓDIGOS (para copiar/pegar)\n")
        f.write("="*80 + "\n\n")
        for codigo in error_codes:
            f.write(f"{codigo}\n")

    print(f"\n✅ Lista de errores guardada en: {ERRORS_FILE}")
    print(f"   Total de errores: {len(errors)}\n")


if __name__ == "__main__":
    generate_error_list()
