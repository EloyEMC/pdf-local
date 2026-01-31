#!/usr/bin/env python3
"""
Analiza los JSONs con errores y genera un reporte.
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

OUTPUT_DIR = os.path.expanduser("~/Documents/processed_json")


def analyze_errors():
    """Analiza todos los JSONs con errores."""
    json_dir = Path(OUTPUT_DIR)

    if not json_dir.exists():
        print(f"❌ Directorio no encontrado: {OUTPUT_DIR}")
        return

    errors = defaultdict(list)

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

                    errors[error_msg].append({
                        'codigo': codigo,
                        'archivo': json_file.name,
                        'fecha': processed_at
                    })
        except Exception as e:
            print(f"⚠️  Error leyendo {json_file.name}: {e}")

    # Mostrar reporte
    print(f"\n{'='*80}")
    print(f"REPORTE DE ERRORES")
    print(f"{'='*80}\n")

    total_errors = sum(len(err_list) for err_list in errors.values())

    if total_errors == 0:
        print("✅ No hay errores\n")
        return

    print(f"❌ Total de PDFs con errores: {total_errors}\n")

    # Agrupar por tipo de error
    for i, (error_type, error_list) in enumerate(errors.items(), 1):
        print(f"{'='*80}")
        print(f"Error {i}: {error_type}")
        print(f"{'='*80}")
        print(f"Cantidad: {len(error_list)}\n")

        for err in error_list:
            print(f"  • {err['codigo']}")
            print(f"    Archivo: {err['archivo']}")
            print(f"    Fecha: {err['fecha']}")
            print()

    # Comando para reintentar todos los errores
    print(f"{'='*80}")
    print(f"⚠️  Para reintentar todos los PDFs fallidos, ejecuta:")
    print(f"{'='*80}")
    print("\n# Eliminar todos los JSONs fallidos:")
    for error_type, error_list in errors.items():
        for err in error_list:
            print(f"rm outputs/processed_json/{err['archivo']}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    analyze_errors()
