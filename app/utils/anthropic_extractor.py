"""
Extractor usando Anthropic Claude Haiku API.
Basado en el sistema de la app web pdf-to-bc3-server-main.
"""

import os
import re
import anthropic
from typing import Dict, Any, Optional


class AnthropicExtractor:
    """Extractor de datos BC3 usando Anthropic Claude Haiku API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-haiku-latest"):
        """
        Inicializa el extractor Anthropic.

        Args:
            api_key: API key de Anthropic (opcional, usa env var si no se provee)
            model: Modelo a usar (default: claude-3-5-haiku-latest)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise Exception("ANTHROPIC_API_KEY no está configurada en variables de entorno")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

    def _get_product_type(self, pdf_text: str) -> Dict[str, Any]:
        """
        Detecta la tipología de producto basándose en palabras clave.

        Returns:
            Dict con toda la info del tipo de producto
        """
        PRODUCT_TYPES = {
            "columna": {
                "name": "Columna",
                "keywords": ["columna", "poste", "báculo", "báculo exterior"]
            },
            "accesorio_mecanico": {
                "name": "Accesorio Mecánico",
                "keywords": ["articulación", "soporte", "bracket", "empotramiento", "fijación", "suspendido", "spike", "cuelgo de lámpara", "varilla", "tensión"]
            },
            "equipo_alimentacion": {
                "name": "Equipo de Alimentación",
                "keywords": ["driver", "transformador", "emergency", "emergencia", "control", "dalí", "push", "dimmer"]
            },
            "luminaria": {
                "name": "Luminaria",
                "keywords": ["led", "luz", "luminaire", "lámpara", "downlight", "proyector", "reflect", "spot", "empotrable", "suspendido", "exterior", "interior"]
            },
            "general": {
                "name": "General",
                "keywords": []
            }
        }

        pdf_lower = pdf_text.lower()

        # Prioridad de detección (de mayor a menor especificidad)
        priority_order = [
            "columna",
            "accesorio_mecanico",
            "equipo_alimentacion",
            "luminaria"
        ]

        # Buscar palabras clave según prioridad
        for type_key in priority_order:
            type_info = PRODUCT_TYPES[type_key]
            for keyword in type_info["keywords"]:
                if keyword.lower() in pdf_lower:
                    return type_info

        # Si no se detecta ninguna, usar general
        return PRODUCT_TYPES["general"]

    def _build_prompt(self, pdf_text: str, target_language: str = 'es') -> str:
        """Construye el prompt para Claude basado en la app web."""

        lang_map = {'ca': 'Catalán', 'eu': 'Euskera', 'es': 'Español', 'gl': 'Gallego'}
        lang_name = lang_map.get(target_language, 'Español')
        translation_instruction = ""
        if target_language != 'es':
            translation_instruction = f"- La respuesta final DEBE ESTAR ESCRITA ÍNTEGRAMENTE en {lang_name}."

        prompt = f"""
Tu tarea es procesar una ficha técnica de una luminaria y generar una descripción en dos partes, separadas por `---`.

**Parte 1: Párrafo de Presupuesto**
Genera un único párrafo que empiece **obligatoriamente** con "Suministro y montaje de luminaria igual o equivalente a".
Este párrafo debe incluir:
- Nombre del producto y código.
- Descripción general, aplicaciones y materiales.
- Datos técnicos clave: Flujo Luminoso (lm), Potencia (W), y CCT (K).
- Si tiene Emergencia integrada, inclúyelo al final del párrafo.
- Siempre añade al final del párrafo "con certificaciones ISO 9001, ISO 14001, ISO 14002, y ISO 45001."

**Parte 2: Detalles Técnicos Estructurados**
Extrae el resto de la información técnica en formato de secciones y campos `Clave: Valor`.
Incluye la sección `INFORMACIÓN GENERAL` con los campos `Artículo`, `Código` y `Descripción` con valores simples y directos.

INFORMACIÓN GENERAL
DIMENSIONES Y PESO
INSTALACIÓN
CARACTERÍSTICAS ELÉCTRICAS Y CONTROLES
DATOS FOTOMÉTRICOS
CARACTERÍSTICAS MECÁNICAS
MATERIALES Y COLORES
NORMAS Y CUMPLIMIENTO
GARANTÍA

- En CARACTERÍSTICAS ELÉCTRICAS Y CONTROLES debe incluir el campo de Emergencia si está presente en la ficha técnica.
- En NORMAS Y CUMPLIMIENTO incluye siempre las certificaciones:
Certificado ISO 9001
Certificado ISO 14001
Certificado ISO 14002
Certificado ISO 45001
Certificado ISO 50001
Certificado que acredite el cumplimiento de las directivas RoHS y RAEE (WEEE)
Certificado que acredite la inscripción del fabricante en un Sistema Integrado de Gestión (SIG) de residuos
Certificado de Productor de Producto
Declaración Ambiental del Producto (DAP) se debe consultar siempre su disponibilidad para cada código, antes de realizar la prescripción

**Instrucciones Finales:**
- No añadas ninguna introducción o frase de saludo en tu respuesta.
- La respuesta debe empezar directamente con el párrafo de la Parte 1.
{translation_instruction}

**Ficha técnica a procesar:**
{pdf_text}
"""
        return prompt

    def extract(self, pdf_text: str, pdf_path: str = None, target_language: str = 'es') -> Dict[str, Any]:
        """
        Extrae datos del PDF usando Anthropic Claude.

        Args:
            pdf_text: Texto extraído del PDF
            pdf_path: Ruta del PDF (opcional, para detección de tipología)
            target_language: Idioma de destino (es, ca, eu, gl)

        Returns:
            Dict con descripcion_corta, descripcion_larga, product_type, product_type_name
        """
        # Detectar tipología
        product_type = self._get_product_type(pdf_text)

        # Construir prompt
        prompt = self._build_prompt(pdf_text, target_language)

        try:
            # Llamada a la API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,
                system="Eres un experto en procesamiento de fichas técnicas y un traductor experto. Tu única tarea es extraer y generar la descripción en el idioma solicitado.",
                messages=[{"role": "user", "content": prompt}]
            )

            # Extraer texto
            extracted_text = response.content[0].text.strip()

            # Limpiar frases introductorias
            cleaned_text = re.sub(
                r'^(?:Basándome en.*?:|Aquí (?:está|tienes).*?:|Claro,.*?:)\s*',
                '',
                extracted_text,
                flags=re.IGNORECASE
            ).strip()

            # Separar en descripción corta y larga
            if '---' in cleaned_text:
                parts = cleaned_text.split('---', 1)
                descripcion_corta = parts[0].strip()
                descripcion_larga = parts[1].strip()
            else:
                # Si no hay separador, usar todo como descripción corta
                descripcion_corta = cleaned_text
                descripcion_larga = ""

            # Limpiar descripción larga
            descripcion_larga = self._clean_descripcion_larga(descripcion_larga)

            return {
                'descripcion_corta': descripcion_corta,
                'descripcion_larga': descripcion_larga,
                'product_type': product_type['keywords'][0] if product_type['keywords'] else 'general',
                'product_type_name': product_type['name'],
                'model': self.model
            }

        except Exception as e:
            raise Exception(f"Error al llamar a Anthropic Claude: {str(e)}")

    def _clean_descripcion_larga(self, text: str) -> str:
        """Limpia la descripción larga."""
        if not text:
            return text

        # Eliminar garantías con 0 años
        lines = text.split('\n')
        cleaned_lines = []

        skip_next = False
        for i, line in enumerate(lines):
            # Eliminar secciones de garantía vacías o con 0 años
            if 'GARANTÍA' in line and i + 1 < len(lines):
                if '0 yr' in lines[i + 1] or '0 años' in lines[i + 1] or '0años' in lines[i + 1]:
                    continue

            # Eliminar líneas vacías múltiples
            if line.strip() or (cleaned_lines and cleaned_lines[-1].strip()):
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()
