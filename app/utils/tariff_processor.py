import pandas as pd
from app.models import db, Product


def process_tariff_file(file_path):
    """
    Procesa un archivo de tarifa (Excel/CSV) y lo importa a la base de datos.

    Expected columns in the file:
    - code: Código del producto (required)
    - name: Nombre del producto (required)
    - description: Descripción (optional)
    - pdf_url: URL del PDF (optional)
    - price: Precio (optional)
    - unit: Unidad (optional)

    Returns:
        dict with 'added' and 'updated' counts
    """
    # Determinar el tipo de archivo
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path, engine='openpyxl')

    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # Mapeo de columnas esperadas
    column_mapping = {
        'código': 'code',
        'codigo': 'code',
        'code': 'code',
        'nombre': 'name',
        'name': 'name',
        'descripción': 'description',
        'descripcion': 'description',
        'description': 'description',
        'pdf': 'pdf_url',
        'pdf_url': 'pdf_url',
        'url': 'pdf_url',
        'ficha': 'pdf_url',
        'precio': 'price',
        'price': 'price',
        'unidad': 'unit',
        'unit': 'unit',
        'u': 'unit',
    }

    # Renombrar columnas
    df.rename(columns=column_mapping, inplace=True)

    # Verificar columnas requeridas
    required_columns = ['code', 'name']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(missing_columns)}")

    # Contadores
    added = 0
    updated = 0

    # Procesar cada fila
    for _, row in df.iterrows():
        code = str(row['code']).strip()
        name = str(row['name']).strip()

        # Buscar si existe el producto
        product = Product.query.filter_by(code=code).first()

        if product:
            # Actualizar producto existente
            product.name = name
            product.description = str(row.get('description', '')).strip() if pd.notna(row.get('description')) else product.description
            product.pdf_url = str(row.get('pdf_url', '')).strip() if pd.notna(row.get('pdf_url')) else product.pdf_url

            if pd.notna(row.get('price')):
                product.price = float(row['price'])

            product.unit = str(row.get('unit', 'U')).strip() if pd.notna(row.get('unit')) else product.unit
            updated += 1
        else:
            # Crear nuevo producto
            product = Product(
                code=code,
                name=name,
                description=str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
                pdf_url=str(row.get('pdf_url', '')).strip() if pd.notna(row.get('pdf_url')) else None,
                price=float(row['price']) if pd.notna(row.get('price')) else None,
                unit=str(row.get('unit', 'U')).strip() if pd.notna(row.get('unit')) else 'U',
            )
            db.session.add(product)
            added += 1

    # Guardar cambios
    db.session.commit()

    return {
        'added': added,
        'updated': updated,
        'total': added + updated,
    }
