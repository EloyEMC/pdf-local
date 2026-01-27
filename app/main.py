from flask import Flask, render_template, request, redirect, send_file, flash, session, jsonify
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

# Importar modelos y base de datos
from app.models import db, Product, ExtractedData

app = Flask(__name__)
app.secret_key = 'cambia-esto-en-produccion'

# Configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
DATABASE_FOLDER = os.path.join(BASE_DIR, 'database')
ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'csv'}

# Crear directorios necesarios
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(DATABASE_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'cache'), exist_ok=True)  # Directorio de caché

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['DATABASE_FOLDER'] = DATABASE_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(DATABASE_FOLDER, "tarifas.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar base de datos
db.init_app(app)

with app.app_context():
    db.create_all()


def allowed_file(filename, file_types=None):
    """Verifica si el archivo tiene una extensión permitida."""
    if file_types is None:
        file_types = ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in file_types


def allowed_tariff_file(filename):
    """Verifica si el archivo es una tarifa válida (Excel/CSV)."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls', 'csv'}



@app.route('/test')
def test():
    """Página de prueba simple."""
    return '''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Test</title></head>
    <body style="background: white; color: black; padding: 50px; font-family: Arial;">
        <h1 style="color: green;">TEST - SI VES ESTO, EL SERVIDOR FUNCIONA</h1>
        <p>El servidor Flask está respondiendo correctamente.</p>
        <p>Abre la consola del navegador (F12) para ver si hay errores.</p>
        <button onclick="alert(\'JavaScript funciona\')" style="padding: 15px; font-size: 18px;">
            Probar JavaScript
        </button>
        <hr>
        <p>Si ves esto bien, el problema está en el template index.html</p>
    </body>
    </html>
    '''


@app.route('/favicon.ico')
def favicon():
    """Devuelve un favicon vacío para evitar 404."""
    return '', 204


@app.route('/debug')
def debug():
    """Página de debug para diagnosticar problemas."""
    return render_template('debug.html')


@app.route('/')
def index():
    """Página principal."""
    extracted_data = session.pop('extracted_data', None)
    bc3_filename = session.pop('bc3_filename', None)
    return render_template('index.html', extracted_data=extracted_data, bc3_filename=bc3_filename)


@app.route('/upload', methods=['POST'])
def upload():
    """Procesa el archivo PDF subido."""
    try:
        # Verificar que se haya enviado un archivo
        if 'pdf_file' not in request.files:
            flash('No se ha seleccionado ningún archivo', 'error')
            return redirect('/')

        file = request.files['pdf_file']

        if file.filename == '':
            flash('No se ha seleccionado ningún archivo', 'error')
            return redirect('/')

        if not file or not allowed_file(file.filename):
            flash('Tipo de archivo no permitido. Solo se aceptan archivos PDF.', 'error')
            return redirect('/')

        # Guardar el archivo
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # Obtener opciones del formulario
        use_ollama = request.form.get('use_ollama') == 'on'
        model = request.form.get('model', 'llama3.2:3b')

        # Extraer datos del PDF
        if use_ollama:
            from app.utils import extract_pdf_to_dict_chunked, get_pdf_info
            from app.bc3 import generate_bc3_from_dict

            # Verificar información del PDF
            pdf_info = get_pdf_info(file_path)
            if pdf_info.get('needs_chunking'):
                flash(f'PDF largo ({pdf_info["pages"]} páginas). Procesando en fragmentos...', 'info')
            else:
                flash('Procesando PDF con Ollama, esto puede tardar unos segundos...', 'info')

            try:
                # Extraer datos usando Ollama (con chunking automático si es necesario)
                extracted_data = extract_pdf_to_dict_chunked(file_path)

                # Generar archivo BC3
                bc3_filename = f"{uuid.uuid4().hex}.bc3"
                bc3_path = os.path.join(app.config['OUTPUT_FOLDER'], bc3_filename)
                generate_bc3_from_dict(extracted_data, bc3_path)

                # Guardar en sesión
                session['extracted_data'] = extracted_data
                session['bc3_filename'] = bc3_filename

                flash('PDF procesado correctamente con Ollama', 'success')
            except Exception as e:
                flash(f'Error procesando con Ollama: {str(e)}', 'error')
                return redirect('/')
        else:
            flash('La extracción sin Ollama no está implementada aún', 'error')
            return redirect('/')

        return redirect('/')

    except Exception as e:
        flash(f'Error procesando el archivo: {str(e)}', 'error')
        return redirect('/')


@app.route('/download/bc3')
def download_bc3():
    """Descarga el archivo BC3 generado."""
    bc3_filename = session.get('bc3_filename')

    if not bc3_filename:
        flash('No hay ningún archivo BC3 para descargar', 'error')
        return redirect('/')

    bc3_path = os.path.join(app.config['OUTPUT_FOLDER'], bc3_filename)

    if not os.path.exists(bc3_path):
        flash('El archivo BC3 no existe', 'error')
        return redirect('/')

    return send_file(
        bc3_path,
        as_attachment=True,
        download_name=f"presupuesto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bc3",
        mimetype='text/plain'
    )


@app.route('/health')
def health():
    """Endpoint de health check."""
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}


# ========== RUTAS DE TARIFAS ==========

@app.route('/tarifas')
def tarifas():
    """Página principal de gestión de tarifas."""
    products = Product.query.order_by(Product.created_at.desc()).all()
    stats = {
        'total': Product.query.count(),
        'processed': Product.query.filter_by(processed=True).count(),
        'pending': Product.query.filter_by(processed=False).count(),
    }
    return render_template('tarifas/index.html', products=products, stats=stats)


@app.route('/tarifas/upload', methods=['GET', 'POST'])
def upload_tariff():
    """Sube una tarifa (Excel/CSV)."""
    if request.method == 'GET':
        return render_template('tarifas/upload.html')

    try:
        if 'tariff_file' not in request.files:
            flash('No se ha seleccionado ningún archivo', 'error')
            return redirect(request.url)

        file = request.files['tariff_file']

        if file.filename == '':
            flash('No se ha seleccionado ningún archivo', 'error')
            return redirect(request.url)

        if not file or not allowed_tariff_file(file.filename):
            flash('Tipo de archivo no permitido. Solo Excel (.xlsx, .xls) y CSV.', 'error')
            return redirect(request.url)

        # Guardar el archivo
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # Procesar la tarifa
        from app.utils.tariff_processor import process_tariff_file
        results = process_tariff_file(file_path)

        flash(f'Tarifa procesada: {results["added"]} productos añadidos, {results["updated"]} actualizados', 'success')
        return redirect('/tarifas')

    except Exception as e:
        flash(f'Error procesando la tarifa: {str(e)}', 'error')
        return redirect(request.url)


@app.route('/tarifas/product/<int:product_id>')
def product_detail(product_id):
    """Ver detalles de un producto."""
    product = Product.query.get_or_404(product_id)
    return render_template('tarifas/product_detail.html', product=product)


@app.route('/tarifas/product/<int:product_id>/process', methods=['POST'])
def process_product_pdf(product_id):
    """Procesa el PDF de un producto con Ollama."""
    try:
        product = Product.query.get_or_404(product_id)

        if not product.pdf_url:
            return jsonify({'error': 'El producto no tiene PDF asociado'}), 400

        # Actualizar estado
        product.processing_status = 'processing'
        db.session.commit()

        from app.utils.ollama_client import OllamaClient
        from app.utils.pdf_extractor import extract_pdf_text_chunked, get_pdf_info
        import requests
        import time

        # Descargar PDF
        start_time = time.time()

        # Si es una URL, descargar el PDF
        if product.pdf_url.startswith('http'):
            pdf_response = requests.get(product.pdf_url)
            pdf_filename = f"{uuid.uuid4().hex}.pdf"
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)

            with open(pdf_path, 'wb') as f:
                f.write(pdf_response.content)
        else:
            pdf_path = product.pdf_url

        # Crear cliente Ollama con caché activado
        client = OllamaClient(
            model=request.form.get('model', 'llama3.2:3b'),
            use_cache=True
        )

        # Obtener información del PDF
        pdf_info = get_pdf_info(pdf_path)

        # Extraer datos con chunking si es necesario
        if pdf_info.get('needs_chunking'):
            print(f"Procesando PDF largo ({pdf_info['pages']} páginas) en chunks...")
            chunks = extract_pdf_text_chunked(pdf_path)
            extracted_data = client.extract_data_from_pdf_chunked(chunks)
        else:
            # PDF corto, procesar normalmente con caché
            pdf_text = extract_pdf_text(pdf_path)
            extracted_data = client.extract_data_from_pdf(pdf_text, pdf_path=pdf_path)

        # Guardar en base de datos
        processing_time = time.time() - start_time

        # Buscar si ya existe datos extraídos
        data = ExtractedData.query.filter_by(product_id=product.id).first()

        if not data:
            data = ExtractedData(product_id=product.id)

        # Mapear datos
        data.codigo_producto = extracted_data.get('codigo_producto')
        data.nombre = extracted_data.get('nombre')
        data.descripcion = extracted_data.get('descripcion')

        # Dimensiones
        dims = extracted_data.get('dimensiones', {})
        data.dimensiones_alto = dims.get('alto')
        data.dimensiones_ancho = dims.get('ancho')
        data.dimensiones_profundidad = dims.get('profundidad')
        data.dimensiones_peso = dims.get('peso')

        # Características eléctricas
        elec = extracted_data.get('caracteristicas_electricas', {})
        data.elec_tension = elec.get('tension')
        data.elec_potencia = elec.get('potencia')
        data.elec_frecuencia = elec.get('frecuencia')

        # Listas
        data.set_materiales(extracted_data.get('materiales', []))
        data.set_colores(extracted_data.get('colores', []))
        data.set_normas(extracted_data.get('normas', []))

        # Otros campos
        data.garantia = extracted_data.get('garantia')
        data.observaciones = extracted_data.get('observaciones')
        data.ollama_model = client.model
        data.processing_time = processing_time

        db.session.add(data)

        # Actualizar producto
        product.processed = True
        product.processing_status = 'completed'
        db.session.commit()

        return jsonify({'success': True, 'data': data.to_dict()})

    except Exception as e:
        product.processing_status = 'error'
        db.session.commit()
        return jsonify({'error': str(e)}), 500


@app.route('/tarifas/process-all', methods=['POST'])
def process_all_products():
    """Procesa todos los productos pendientes."""
    try:
        model = request.form.get('model', 'llama3.2:3b')
        pending_products = Product.query.filter_by(processed=False).all()

        results = {
            'total': len(pending_products),
            'processed': 0,
            'errors': 0,
        }

        for product in pending_products:
            if product.pdf_url:
                # Procesar cada producto
                # TODO: Implementar procesamiento en lote
                results['processed'] += 1

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/tarifas/export')
def export_tariff():
    """Exporta la tarifa a Excel."""
    try:
        import pandas as pd
        from io import BytesIO

        # Obtener todos los productos con sus datos extraídos
        products = Product.query.all()

        data = []
        for p in products:
            row = {
                'Código': p.code,
                'Nombre': p.name,
                'Descripción': p.description,
                'Precio': p.price,
                'Unidad': p.unit,
                'PDF URL': p.pdf_url,
                'Procesado': 'Sí' if p.processed else 'No',
            }

            # Añadir datos extraídos si existen
            if p.extracted_data:
                ed = p.extracted_data
                row.update({
                    'Código Producto': ed.codigo_producto,
                    'Nombre Extraído': ed.nombre,
                    'Alto': ed.dimensiones_alto,
                    'Ancho': ed.dimensiones_ancho,
                    'Profundidad': ed.dimensiones_profundidad,
                    'Peso': ed.dimensiones_peso,
                    'Tensión': ed.elec_tension,
                    'Potencia': ed.elec_potencia,
                    'Materiales': ', '.join(ed.get_materiales()),
                    'Normas': ', '.join(ed.get_normas()),
                })

            data.append(row)

        # Crear Excel
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, engine='openpyxl', index=False)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name=f"tarifa_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        flash(f'Error exportando: {str(e)}', 'error')
        return redirect('/tarifas')


# ========== RUTAS DE SCRAPING ==========

@app.route('/scraper/disano')
def scraper_disano():
    """Página para scrapea Disano."""
    return render_template('scraper/disano.html')


@app.route('/scraper/disano/run', methods=['POST'])
def run_scraper_disano():
    """Ejecuta el scraper de Disano con Playwright."""
    try:
        from app.utils.disano_scraper_playwright import DisanoScraperPlaywright

        # Obtener parámetros
        max_categories = int(request.form.get('max_categories', 3))
        max_products = int(request.form.get('max_products', 10))

        # Ejecutar scraper
        scraper = DisanoScraperPlaywright(headless=True)
        pdfs = scraper.scrape_all_simple(max_categories=max_categories, max_products_per_category=max_products)

        # Importar productos a la base de datos
        added = 0
        updated = 0

        for pdf_data in pdfs:
            code = pdf_data['product_code'] or pdf_data['name'].replace('.pdf', '')

            # Buscar si existe
            product = Product.query.filter_by(code=code).first()

            if product:
                # Actualizar
                if not product.pdf_url:
                    product.pdf_url = pdf_data['url']
                updated += 1
            else:
                # Crear nuevo
                product = Product(
                    code=code,
                    name=pdf_data['name'].replace('.pdf', ''),
                    pdf_url=pdf_data['url'],
                    unit='U',
                )
                db.session.add(product)
                added += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'pdfs_found': len(pdfs),
            'products_added': added,
            'products_updated': updated,
            'pdfs': pdfs[:10],  # Primeros 10 como preview
        })

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Maneja errores de archivo demasiado grande."""
    flash('El archivo es demasiado grande. Máximo 16 MB.', 'error')
    return redirect('/')


@app.errorhandler(500)
def internal_error(error):
    """Maneja errores internos del servidor."""
    flash('Ha ocurrido un error interno del servidor.', 'error')
    return redirect('/')


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 PDF to BC3 - Ollama Local")
    print("="*60)
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📁 Output folder: {app.config['OUTPUT_FOLDER']}")
    print(f"🌐 Accede a: http://localhost:5001")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5001)
