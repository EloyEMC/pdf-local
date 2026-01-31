#!/usr/bin/env python3
"""
Actualiza la base de datos desde los archivos JSON generados.
"""

import os
import sys
import sqlite3
import json
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

JSON_DIR = "outputs/processed_json"
DB_PATH = os.path.join(project_root, "database", "tarifa_disano.db")


def get_processed_jsons():
    """Obtiene todos los JSON procesados."""
    json_dir = Path(JSON_DIR)
    if not json_dir.exists():
        return []

    json_files = list(json_dir.glob("*.json"))
    return json_files


def update_db_from_json(json_file: Path, cursor) -> bool:
    """Actualiza la BD desde un archivo JSON.

    Args:
        json_file: Ruta al archivo JSON
        cursor: Cursor de base de datos activo

    Returns:
        True si se actualizó correctamente
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data.get('success'):
            return False

        codigo = data['codigo']

        cursor.execute("""
            UPDATE productos
            SET texto_extraido = ?,
                descripcion_corta_ollama = ?,
                descripcion_larga = ?,
                bc3_product_type = ?,
                ollama_processed = 1,
                ollama_processed_at = ?,
                ollama_model = ?
            WHERE "CÓDIGO" = ? OR REFERENCIA = ?
        """, (
            data['texto_extraido'],
            data['descripcion_corta'],
            data['descripcion_larga'],
            data['product_type'],
            data['processed_at'],
            data['model'],
            codigo,
            codigo
        ))

        return cursor.rowcount > 0

    except Exception as e:
        print(f"❌ Error con {json_file.name}: {e}")
        return False


def main():
    """Actualiza la BD desde todos los JSON."""
    print(f"\n{'='*80}")
    print(f"ACTUALIZANDO BD DESDE JSON")
    print(f"{'='*80}\n")

    print(f"📁 Directorio JSON: {JSON_DIR}")
    print(f"💾 Base de datos: {DB_PATH}\n")

    json_files = get_processed_jsons()
    total = len(json_files)

    if total == 0:
        print("❌ No hay archivos JSON para procesar")
        return

    print(f"📊 Archivos JSON: {total}\n")

    # Crear una única conexión a la base de datos
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        success = 0
        errors = 0
        commit_interval = 100  # Commit cada 100 JSONs

        for i, json_file in enumerate(json_files, 1):
            print(f"[{i}/{total}] {json_file.stem}... ", end="")

            if update_db_from_json(json_file, cursor):
                print("✅")
                success += 1
            else:
                print("❌")
                errors += 1

            # Commit periódico
            if success % commit_interval == 0:
                conn.commit()
                print(f"     💾 Commit intermedio ({success} importados)")

        # Commit final
        conn.commit()

        # Resumen
        print(f"\n{'='*80}")
        print(f"✅ Actualizados: {success}")
        print(f"❌ Errores: {errors}")
        print(f"{'='*80}\n")

        # Verificar BD
        cursor.execute('SELECT COUNT(*) FROM productos WHERE ollama_processed = 1')
        processed = cursor.fetchone()[0]

        print(f"📊 Total procesados en BD: {processed}\n")

    finally:
        # Asegurar que la conexión se cierre siempre
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido")
