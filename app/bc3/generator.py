from typing import Dict, Any, List
from datetime import datetime


class BC3Generator:
    """Generador de archivos BC3."""

    def __init__(self):
        self.records = []

    def generate(self, data: Dict[str, Any) -> str:
        """
        Genera el contenido de un archivo BC3 a partir de los datos extraídos.

        Args:
            data: Diccionario con los datos extraídos del PDF

        Returns:
            Contenido del archivo BC3
        """
        self.records = []

        # Versión del formato
        self.add_version()

        # Registro de concepto principal
        self.add_concept(data)

        # Registro de desglose
        self.add_desglose(data)

        # Registro de textos
        self.add_textos(data)

        # Unir todos los registros
        return "\r\n".join(self.records)

    def add_version(self):
        """Añade el registro de versión."""
        self.records.append("~V|BC3|1|")

    def add_concept(self, data: Dict[str, Any]):
        """Añade el registro de concepto."""
        codigo = data.get("codigo_producto", "001")
        nombre = data.get("nombre", "Producto genérico")
        unidad = data.get("unidad", "U")

        # Formato: ~C|{CODIGO}|\{UNIDAD}\{NOMBRE}|
        self.records.append(f"~C|{codigo}|\\{unidad}\\{nombre}|")

    def add_desglose(self, data: Dict[str, Any]):
        """Añade el registro de desglose."""
        codigo = data.get("codigo_producto", "001")
        precio = data.get("precio", "0.00")

        # Formato: ~D|{CODIGO}|\{PORCENTAJE}%\{SUBCODIGO}|
        self.records.append(f"~D|{codigo}|\\100%\\{codigo}|")

        # Si hay precio, añadir registro de precio
        if precio != "0.00":
            self.add_precio(codigo, precio)

    def add_precio(self, codigo: str, precio: str):
        """Añade el registro de precio."""
        # Formato: ~P|{CODIGO}|\{PRECIO}|
        self.records.append(f"~P|{codigo}|\\{precio}|")

    def add_textos(self, data: Dict[str, Any]):
        """Añade el registro de textos/observaciones."""
        codigo = data.get("codigo_producto", "001")

        # Construir texto con toda la información
        texto_parts = []

        if data.get("descripcion"):
            texto_parts.append(f"DESCRIPCIÓN: {data['descripcion']}")

        if data.get("dimensiones"):
            dims = data["dimensiones"]
            dim_text = ", ".join(f"{k}: {v}" for k, v in dims.items() if v)
            if dim_text:
                texto_parts.append(f"DIMENSIONES: {dim_text}")

        if data.get("caracteristicas_electricas"):
            elec = data["caracteristicas_electricas"]
            elec_text = ", ".join(f"{k}: {v}" for k, v in elec.items() if v)
            if elec_text:
                texto_parts.append(f"CARACTERÍSTICAS ELÉCTRICAS: {elec_text}")

        if data.get("materiales"):
            texto_parts.append(f"MATERIALES: {', '.join(data['materiales'])}")

        if data.get("normas"):
            texto_parts.append(f"NORMAS: {', '.join(data['normas'])}")

        if data.get("observaciones"):
            texto_parts.append(f"OBSERVACIONES: {data['observaciones']}")

        if texto_parts:
            texto_completo = " | ".join(texto_parts)
            # Formato: ~T|{CODIGO}|\{TEXTO}|
            self.records.append(f"~T|{codigo}|\\{texto_completo}|")


def generate_bc3_from_dict(data: Dict[str, Any], output_path: str = None) -> str:
    """
    Genera un archivo BC3 a partir de un diccionario de datos.

    Args:
        data: Diccionario con los datos extraídos del PDF
        output_path: Ruta donde guardar el archivo (opcional)

    Returns:
        Contenido del archivo BC3
    """
    generator = BC3Generator()
    content = generator.generate(data)

    if output_path:
        with open(output_path, 'w', encoding='latin-1') as f:
            f.write(content)

    return content


def generate_bc3_with_ollama(data: Dict[str, Any], ollama_client=None) -> str:
    """
    Genera un BC3 usando Ollama para crear el formato correcto.

    Args:
        data: Diccionario con los datos extraídos
        ollama_client: Cliente de Ollama (opcional)

    Returns:
        Contenido del archivo BC3
    """
    from .ollama_client import OllamaClient

    client = ollama_client or OllamaClient()
    return client.generate_bc3_structure(data)
