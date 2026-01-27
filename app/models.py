from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Product(db.Model):
    """Modelo de producto de la tarifa."""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    pdf_url = db.Column(db.String(1000))  # URL de la ficha técnica
    price = db.Column(db.Float)
    unit = db.Column(db.String(50))

    # Estado del procesamiento
    processed = db.Column(db.Boolean, default=False)
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, error

    # Fecha de creación y actualización
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con los datos extraídos
    extracted_data = db.relationship('ExtractedData', backref='product', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        """Convierte el producto a diccionario."""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'pdf_url': self.pdf_url,
            'price': self.price,
            'unit': self.unit,
            'processed': self.processed,
            'processing_status': self.processing_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ExtractedData(db.Model):
    """Datos extraídos del PDF por Ollama."""
    __tablename__ = 'extracted_data'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    # Datos estructurados extraídos
    codigo_producto = db.Column(db.String(100))
    nombre = db.Column(db.String(500))
    descripcion = db.Column(db.Text)

    # Dimensiones
    dimensiones_alto = db.Column(db.String(100))
    dimensiones_ancho = db.Column(db.String(100))
    dimensiones_profundidad = db.Column(db.String(100))
    dimensiones_peso = db.Column(db.String(100))

    # Características eléctricas
    elec_tension = db.Column(db.String(100))
    elec_potencia = db.Column(db.String(100))
    elec_frecuencia = db.Column(db.String(100))

    # Materiales y colores (JSON)
    materiales = db.Column(db.Text)  # JSON array
    colores = db.Column(db.Text)  # JSON array

    # Normas y certificados
    normas = db.Column(db.Text)  # JSON array
    garantia = db.Column(db.String(200))
    observaciones = db.Column(db.Text)

    # Metadatos del procesamiento
    ollama_model = db.Column(db.String(100))
    processing_time = db.Column(db.Float)  # segundos
    raw_response = db.Column(db.Text)  # Respuesta cruda de Ollama

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_materiales(self):
        """Devuelve la lista de materiales."""
        return json.loads(self.materiales) if self.materiales else []

    def get_colores(self):
        """Devuelve la lista de colores."""
        return json.loads(self.colores) if self.colores else []

    def get_normas(self):
        """Devuelve la lista de normas."""
        return json.loads(self.normas) if self.normas else []

    def set_materiales(self, lista):
        """Guarda la lista de materiales."""
        self.materiales = json.dumps(lista) if lista else None

    def set_colores(self, lista):
        """Guarda la lista de colores."""
        self.colores = json.dumps(lista) if lista else None

    def set_normas(self, lista):
        """Guarda la lista de normas."""
        self.normas = json.dumps(lista) if lista else None

    def to_dict(self):
        """Convierte los datos extraídos a diccionario."""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'codigo_producto': self.codigo_producto,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'dimensiones': {
                'alto': self.dimensiones_alto,
                'ancho': self.dimensiones_ancho,
                'profundidad': self.dimensiones_profundidad,
                'peso': self.dimensiones_peso,
            },
            'caracteristicas_electricas': {
                'tension': self.elec_tension,
                'potencia': self.elec_potencia,
                'frecuencia': self.elec_frecuencia,
            },
            'materiales': self.get_materiales(),
            'colores': self.get_colores(),
            'normas': self.get_normas(),
            'garantia': self.garantia,
            'observaciones': self.observaciones,
            'ollama_model': self.ollama_model,
            'processing_time': self.processing_time,
        }
