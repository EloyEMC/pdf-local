#!/usr/bin/env python3
"""
Importa JSONs procesados con IA a la base de datos SQLite.
Actualiza los campos bc3_descripcion_corta, bc3_descripcion_larga, etc.
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configuración
DB_PATH = os.path.join(project_root, "database", "tarifa_disano.db")
JSON_DIR = os.path.expanduser("~/Documents/processed_json")


def import_jsons_to_db():
    """Importa JSONs procesados a la base de datos."""

    print(f"\n{'='*80}")
    print(f"IMPORTACIÓN DE JSONS PROCESADOS A BASE DE DATOS")
    print(f"{'='*80}\n")

    print(f"📁 JSONs: {JSON_DIR}")
    print(f"💾 Base de datos: {DB_PATH}\n")

    # Conectar a la base de datos
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener todos los JSONs
    json_dir = Path(JSON_DIR)
    json_files = list(json_dir.glob("*.json"))

    # Filtrar solo los que tienen descripcion_corta (procesados con IA)
    processed_files = []
    for json_file in json_files:
        if json_file.name.startswith('._'):
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('descripcion_corta'):
                    processed_files.append((json_file, data))
        except Exception as e:
            print(f"⚠️  Error leyendo {json_file.name}: {e}")
            continue

    total = len(processed_files)
    print(f"📊 JSONs a importar: {total}\n")

    if total == 0:
        print("❌ No hay JSONs procesados para importar")
        return

    # Estadísticas
    updated = 0
    not_found = 0
    errors = 0

    for i, (json_file, data) in enumerate(processed_files, 1):
        codigo = data.get('codigo')

        if not codigo:
            print(f"⚠️  [{i}/{total}] {json_file.name}: Sin código")
            errors += 1
            continue

        # Verificar si el producto existe en la base de datos
        cursor.execute(
            "SELECT CÓDIGO FROM productos WHERE CÓDIGO = ?",
            (codigo,)
        )
        result = cursor.fetchone()

        if not result:
            print(f"⚠️  [{i}/{total}] {codigo}: No encontrado en BD")
            not_found += 1
            continue

        # Actualizar el registro
        try:
            cursor.execute("""
                UPDATE productos
                SET bc3_descripcion_corta = ?,
                    bc3_descripcion_larga = ?,
                    bc3_product_type = ?,
                    bc3_processed_at = ?,
                    bc3_model = ?
                WHERE CÓDIGO = ?
            """, (
                data.get('descripcion_corta'),
                data.get('descripcion_larga'),
                data.get('product_type'),
                data.get('ai_processed_at'),
                data.get('ai_model'),
                codigo
            ))

            if cursor.rowcount > 0:
                updated += 1
                if updated % 100 == 0:
                    print(f"✅ [{i}/{total}] {codigo}: Actualizado ({updated} totales)")
            else:
                print(f"⚠️  [{i}/{total}] {codigo}: No se actualizó")

        except Exception as e:
            print(f"❌ [{i}/{total}] {codigo}: Error - {str(e)[:50]}")
            errors += 1

        # Commit cada 500 registros
        if i % 500 == 0:
            conn.commit()
            print(f"💾 Commit intermedio: {i} registros procesados\n")

    # Commit final
    conn.commit()

    # Resumen
    print(f"\n{'='*80}")
    print(f"RESUMEN DE IMPORTACIÓN")
    print(f"{'='*80}")
    print(f"✅ Actualizados: {updated}")
    print(f"⚠️  No encontrados: {not_found}")
    print(f"❌ Errores: {errors}")
    print(f"📊 Total procesados: {total}")
    print(f"\n💾 Base de datos actualizada: {DB_PATH}")
    print(f"{'='*80}\n")

    # Verificación
    cursor.execute(
        "SELECT COUNT(*) FROM productos WHERE bc3_descripcion_corta IS NOT NULL"
    )
    count = cursor.fetchone()[0]
    print(f"📈 Productos con bc3_descripcion_corta: {count}")

    cursor.execute(
        "SELECT COUNT(*) FROM productos WHERE bc3_product_type = 'columna'"
    )
    columnas = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM productos WHERE bc3_product_type = 'articulacion'"
    )
    articulaciones = cursor.fetchone()[0]

    print(f"📊 Columnas: {columnas}")
    print(f"📊 Articulaciones: {articulaciones}\n")

    conn.close()


if __name__ == "__main__":
    try:
        import_jsons_to_db()
    except KeyboardInterrupt:
        print("\n\n⚠️  Importación interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
