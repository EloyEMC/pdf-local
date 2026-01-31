#!/usr/bin/env python3
"""
Procesa todas las fichas técnicas de Disano con Ollama y actualiza la BD.
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Añadir el directorio del proyecto al path (el script está en scripts/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils import extract_pdf_text, extract_bc3_from_pdf
from app.utils.ollama_client import OllamaClient


def get_all_pdfs(folder_path: str) -> List[Dict[str, str]]:
    """Escanea recursivamente la carpeta en busca de PDFs."""
    pdfs = []
    folder = Path(folder_path)

    for pdf_file in folder.rglob("*.pdf"):
        # Filtrar archivos ocultos de macOS (._*)
        if pdf_file.name.startswith('._'):
            continue

        # Filtrar archivos que comienzan con '.' (ocultos)
        if pdf_file.name.startswith('.'):
            continue

        codigo = pdf_file.stem  # nombre sin extensión
        pdfs.append({
            'codigo': codigo,
            'ruta': str(pdf_file)
        })

    return pdfs


def update_database(codigo: str, texto_extraido: str, bc3_data: dict,
                   model: str, cursor) -> bool:
    """Actualiza un producto en la base de datos con los datos de Ollama.

    Args:
        codigo: Código del producto
        texto_extraido: Texto extraído del PDF
        bc3_data: Datos BC3 extraídos
        model: Modelo de Ollama usado
        cursor: Cursor de base de datos activo

    Returns:
        True si se actualizó correctamente
    """
    try:
        # Actualizar el producto con datos BC3
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
            texto_extraido[:50000],  # Limitar a 50KB
            bc3_data['descripcion_corta'],
            bc3_data['descripcion_larga'],
            bc3_data['product_type'],
            datetime.now().isoformat(),
            model,
            codigo,
            codigo
        ))

        return cursor.rowcount > 0

    except Exception as e:
        print(f"  ❌ Error actualizando BD: {e}")
        return False


def process_all_pdfs(
    pdf_folder: str,
    db_path: str,
    model: str = "deepseek-r1:latest",
    target_language: str = 'es',
    skip_processed: bool = True
):
    """Procesa todos los PDFs y actualiza la base de datos."""
    print(f"\n{'='*80}")
    print(f"PROCESANDO FICHAS TÉCNICAS CON BC3 (OLLAMA)")
    print(f"{'='*80}\n")

    print(f"📁 Carpeta: {pdf_folder}")
    print(f"💾 Base de datos: {db_path}")
    print(f"🤖 Modelo: {model}")
    print(f"🌐 Idioma: {target_language}")
    print()

    # Obtener todos los PDFs
    print("Escaneando PDFs...")
    pdfs = get_all_pdfs(pdf_folder)
    total = len(pdfs)

    print(f"✓ Encontrados {total} archivos PDF\n")

    if total == 0:
        print("No se encontraron PDFs para procesar.")
        return

    # Crear una única conexión a la base de datos para todo el proceso
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Verificar cuántos ya están procesados
        if skip_processed:
            cursor.execute('SELECT COUNT(*) FROM productos WHERE ollama_processed = 1')
            processed_count = cursor.fetchone()[0]
            print(f"ℹ️  Productos ya procesados en BD: {processed_count}")
            print()

        # Procesar cada PDF
        success_count = 0
        error_count = 0
        skipped_count = 0
        commit_interval = 50  # Commit cada 50 productos

        for i, pdf_info in enumerate(pdfs, 1):
            codigo = pdf_info['codigo']
            ruta = pdf_info['ruta']

            # Verificar si ya está procesado
            if skip_processed:
                cursor.execute('SELECT ollama_processed FROM productos WHERE "CÓDIGO" = ? OR REFERENCIA = ?', (codigo, codigo))
                result = cursor.fetchone()

                if result and result[0]:
                    print(f"[{i}/{total}] ⏭️  {codigo} - Ya procesado")
                    skipped_count += 1
                    continue

            print(f"[{i}/{total}] 🔄 {codigo}")

            try:
                # Extraer texto del PDF
                texto_extraido = extract_pdf_text(ruta, remove_headers=True)

                # Extraer datos BC3
                bc3_data = extract_bc3_from_pdf(
                    pdf_path=ruta,
                    model=model,
                    target_language=target_language,
                    use_cache=True
                )

                # Actualizar base de datos (usando el cursor existente)
                updated = update_database(
                    codigo=codigo,
                    texto_extraido=texto_extraido,
                    bc3_data=bc3_data,
                    model=model,
                    cursor=cursor
                )

                if updated:
                    print(f"     ✓ Guardado")
                    success_count += 1
                else:
                    print(f"     ⚠️  Producto no encontrado en BD")
                    error_count += 1

                # Commit periódico para no perder datos si falla
                if success_count % commit_interval == 0:
                    conn.commit()
                    print(f"     💾 Commit intermedio ({success_count} procesados)")

            except Exception as e:
                print(f"     ❌ Error: {str(e)[:100]}")
                error_count += 1

        # Commit final de todos los cambios
        conn.commit()

        # Resumen
        print(f"\n{'='*80}")
        print(f"RESUMEN")
        print(f"{'='*80}")
        print(f"Total PDFs: {total}")
        print(f"✓ Procesados correctamente: {success_count}")
        print(f"⏭️  Saltados (ya procesados): {skipped_count}")
        print(f"❌ Errores: {error_count}")
        print(f"{'='*80}\n")

    finally:
        # Asegurar que la conexión se cierre siempre
        conn.close()


if __name__ == "__main__":
    # Obtener el directorio raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    PDF_FOLDER = "/Volumes/WEBS/disano-scraper/data/output/fichas_tecnicas"
    DB_PATH = os.path.join(project_root, "database", "tarifa_disano.db")
    MODEL = "qwen3:4b"
    TARGET_LANGUAGE = "es"

    if not os.path.exists(PDF_FOLDER):
        print(f"❌ Error: No existe la carpeta {PDF_FOLDER}")
        sys.exit(1)

    if not os.path.exists(DB_PATH):
        print(f"❌ Error: No existe la base de datos {DB_PATH}")
        sys.exit(1)

    process_all_pdfs(
        pdf_folder=PDF_FOLDER,
        db_path=DB_PATH,
        model=MODEL,
        target_language=TARGET_LANGUAGE,
        skip_processed=True
    )
