#!/usr/bin/env python3
"""
Exporta la base de datos SQLite a Excel.
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configuración
DB_PATH = os.path.join(project_root, "database", "tarifa_disano.db")
OUTPUT_DIR = os.path.expanduser("~/Documents")


def export_to_excel():
    """Exporta la base de datos a Excel."""

    print(f"\n{'='*80}")
    print(f"EXPORTACIÓN DE BASE DE DATOS A EXCEL")
    print(f"{'='*80}\n")

    print(f"📁 Base de datos: {DB_PATH}")
    print(f"📊 Salida: {OUTPUT_DIR}\n")

    # Conectar a la base de datos
    conn = sqlite3.connect(DB_PATH)

    # Leer datos
    query = "SELECT * FROM productos"
    df = pd.read_sql_query(query, conn)

    # Renombrar columnas para mejor legibilidad
    column_rename = {
        'MARCA': 'Marca',
        'CÓDIGO': 'Código',
        'CÓDIGO WEB': 'Código Web',
        'REFERENCIA': 'Referencia',
        'EAN 13': 'EAN 13',
        'DESCRIPCION': 'Descripción',
        'U.P.LOG': 'U.P.LOG',
        'U.CAJA': 'U.CAJA',
        'DTO.': 'DTO.',
        'CLASE ETIM': 'Clase ETIM',
        'RAEE_A': 'RAEE_A',
        'RAEE_L': 'RAEE_L',
        'RAEE_T': 'RAEE_T',
        'Peso bruto KG': 'Peso bruto KG',
        'Peso bruto GR': 'Peso bruto GR',
        'Peso neto KG': 'Peso neto KG',
        'Peso neto GR': 'Peso neto GR',
        'Longitud M': 'Longitud M',
        'Longitud MM': 'Longitud MM',
        'Ancho M': 'Ancho M',
        'Ancho MM': 'Ancho MM',
        'Alto M': 'Alto M',
        'Altura MM': 'Altura MM',
        'Volumen DM3': 'Volumen DM3',
        'Serie_familia_1': 'Serie familia 1',
        'Familia_WEB': 'Familia WEB',
        'Familia_Catalogo': 'Familia Catálogo',
        'Familia_Catalogo_PTL': 'Familia Catálogo PTL',
        'Url_ficha_tec': 'URL Ficha Técnica',
        'descontinuado': 'Descontinuado',
        'descripcion_corta': 'Descripción Corta',
        'img_url': 'URL Imagen',
        'PVP_26_01_26': 'PVP 26/01/26',
        'bc3_descripcion_corta': 'BC3 Descripción Corta',
        'bc3_descripcion_larga': 'BC3 Descripción Larga',
        'bc3_product_type': 'BC3 Tipo Producto',
        'bc3_processed_at': 'BC3 Procesado'
    }

    df = df.rename(columns=column_rename)

    total_registros = len(df)
    total_columnas = len(df.columns)

    print(f"📊 Registros: {total_registros:,}")
    print(f"📊 Columnas: {total_columnas}")
    print(f"📊 Tamaño en memoria: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB\n")

    # Generar nombre de archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tarifa_disano_{timestamp}.xlsx"
    output_path = os.path.join(OUTPUT_DIR, filename)

    print(f"💾 Guardando en: {filename}")
    print("⏳ Procesando...\n")

    # Exportar a Excel
    from openpyxl.utils import get_column_letter

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Productos', index=False)

        # Ajustar ancho de columnas automáticamente
        worksheet = writer.sheets['Productos']
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].fillna('').astype(str).str.len().max(),
                len(str(col))
            )
            # Limitar ancho máximo
            adjusted_width = min(max_length + 2, 50)
            col_letter = get_column_letter(idx)
            worksheet.column_dimensions[col_letter].width = adjusted_width

    file_size_mb = os.path.getsize(output_path) / 1024 / 1024

    print(f"{'='*80}")
    print(f"RESUMEN DE EXPORTACIÓN")
    print(f"{'='*80}")
    print(f"✅ Archivo creado: {filename}")
    print(f"📊 Registros: {total_registros:,}")
    print(f"📊 Columnas: {total_columnas}")
    print(f"💾 Tamaño: {file_size_mb:.1f} MB")
    print(f"📁 Ruta completa: {output_path}")
    print(f"{'='*80}\n")

    # Mostrar algunas estadísticas
    print("📈 Estadísticas de campos BC3:")
    print(f"   - BC3 Descripción Corta: {df['BC3 Descripción Corta'].notna().sum():,} registros")
    print(f"   - BC3 Descripción Larga: {df['BC3 Descripción Larga'].notna().sum():,} registros")
    print(f"   - BC3 Tipo Producto: {df['BC3 Tipo Producto'].notna().sum():,} registros")
    print(f"   - URL Imagen: {df['URL Imagen'].notna().sum():,} registros\n")

    conn.close()


if __name__ == "__main__":
    try:
        export_to_excel()
    except KeyboardInterrupt:
        print("\n\n⚠️  Exportación interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
