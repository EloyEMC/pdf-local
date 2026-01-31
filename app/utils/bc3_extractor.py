"""
Extractor especializado para generar descripciones BC3 con dos peticiones a Ollama.

Basado en el prompt probado de Claude Haaku, adaptado para Ollama llama3.2:latest.
"""

import re
from typing import Dict, Any, Tuple, Optional
from .ollama_client import OllamaClient


# Tipologías de productos soportadas
PRODUCT_TYPES = {
    "luminaria": {
        "keywords": ["luminaria", "lámpara", "light", "luminaire", "led", "fluorescente", "arcón"],
        "name": "Luminaria",
        "descripcion_corta_template": "Suministro y montaje de luminaria igual o equivalente a",
        "secciones_parte_larga": [
            "INFORMACIÓN GENERAL",
            "DIMENSIONES Y PESO",
            "INSTALACIÓN",
            "CARACTERÍSTICAS ELÉCTRICAS Y CONTROLES",
            "DATOS FOTOMÉTRICOS",
            "CARACTERÍSTICAS MECÁNICAS",
            "MATERIALES Y COLORES",
            "NORMAS Y CUMPLIMIENTO",
            "GARANTÍA"
        ]
    },
    "equipo_alimentacion": {
        "keywords": ["alimentación", "power supply", "driver", "transformador", "balasto"],
        "name": "Equipo de Alimentación",
        "descripcion_corta_template": "Suministro y montaje de equipo de alimentación igual o equivalente a",
        "secciones_parte_larga": [
            "INFORMACIÓN GENERAL",
            "DIMENSIONES Y PESO",
            "CARACTERÍSTICAS ELÉCTRICAS",
            "PROTECCIONES",
            "INSTALACIÓN",
            "MATERIALES",
            "NORMAS Y CUMPLIMIENTO",
            "GARANTÍA"
        ]
    },
    "accesorio_mecanico": {
        "keywords": ["articulación", "abalorio", "proyector", "soporte", "bracket", "accesorio", "colgador", "suspensión", "fijación", "brazo", "cuelgo"],
        "name": "Accesorio Mecánico",
        "descripcion_corta_template": "Suministro y montaje de accesorio mecánico igual o equivalente a",
        "secciones_parte_larga": [
            "INFORMACIÓN GENERAL",
            "DIMENSIONES Y PESO",
            "MATERIALES Y ACABADOS",
            "CAPACIDAD DE CARGA",
            "INSTALACIÓN",
            "NORMAS Y CUMPLIMIENTO",
            "GARANTÍA"
        ]
    },
    "columna": {
        "keywords": ["columna luminosa", "báculo", "poste de iluminación", "columna alto", "mástil"],
        "name": "Columna",
        "descripcion_corta_template": "Suministro y montaje de columna igual o equivalente a",
        "secciones_parte_larga": [
            "INFORMACIÓN GENERAL",
            "DIMENSIONES Y PESO",
            "MATERIALES Y ACABADOS",
            "CAPACIDAD DE CARGA",
            "FUNDAMENTACIÓN",
            "INSTALACIÓN",
            "NORMAS Y CUMPLIMIENTO",
            "GARANTÍA"
        ]
    },
    "general": {
        "keywords": [],
        "name": "Producto General",
        "descripcion_corta_template": "Suministro y montaje de producto igual o equivalente a",
        "secciones_parte_larga": [
            "INFORMACIÓN GENERAL",
            "DIMENSIONES Y PESO",
            "CARACTERÍSTICAS TÉCNICAS",
            "INSTALACIÓN",
            "MATERIALES",
            "NORMAS Y CUMPLIMIENTO",
            "GARANTÍA"
        ]
    }
}


class BC3Extractor:
    """Extractor especializado para generar descripciones BC3."""

    def __init__(self, model: str = "deepseek-r1:latest", use_cache: bool = True, timeout: int = 600):
        """
        Inicializa el extractor BC3.

        Args:
            model: Modelo de Ollama a usar
            use_cache: Si True, usa caché
            timeout: Timeout en segundos para llamadas a Ollama (default: 600 = 10 minutos)
        """
        self.client = OllamaClient(model=model, use_cache=use_cache, timeout=timeout)
        self.system_prompt = "Eres un experto en procesamiento de fichas técnicas y un traductor experto. Tu única tarea es extraer y generar la descripción en el idioma solicitado."

    def extract(self, pdf_text: str, pdf_path: str = None, target_language: str = 'es') -> Dict[str, Any]:
        """
        Extrae datos del PDF usando dos peticiones separadas.

        Args:
            pdf_text: Texto extraído del PDF
            pdf_path: Ruta del PDF (para caché y detección de tipología)
            target_language: Idioma de destino (es, ca, eu, gl)

        Returns:
            Dict con descripcion_corta y descripcion_larga
        """
        # Detectar tipología de producto (prioridad: ruta del archivo > contenido)
        product_type = self._detect_product_type_from_path(pdf_path) or self._detect_product_type(pdf_text)
        print(f"✓ Tipología detectada: {product_type['name']}")

        # Petición 1: Descripción corta (párrafo de presupuesto)
        print("  → Generando descripción corta...")
        descripcion_corta = self._extract_descripcion_corta(
            pdf_text,
            product_type,
            target_language
        )

        # Petición 2: Descripción larga (detalles técnicos)
        print("  → Generando descripción larga...")
        descripcion_larga = self._extract_descripcion_larga(
            pdf_text,
            product_type,
            target_language
        )

        return {
            'descripcion_corta': descripcion_corta,
            'descripcion_larga': descripcion_larga,
            'product_type': product_type['keywords'][0] if product_type['keywords'] else 'general',  # Usar primera keyword como tipo
            'product_type_name': product_type['name']
        }

    def _detect_product_type(self, pdf_text: str) -> Dict[str, Any]:
        """
        Detecta la tipología de producto basándose en palabras clave.

        Args:
            pdf_text: Texto del PDF

        Returns:
            Dict con toda la info del tipo de producto
        """
        pdf_lower = pdf_text.lower()

        # Prioridad de detección (de mayor a menor especificidad)
        priority_order = [
            "columna",           # Más específico: columna, poste, báculo
            "accesorio_mecanico", # Accesorios: articulación, soporte, bracket
            "equipo_alimentacion", # Drivers, transformadores
            "luminaria",         # Más genérico: led, light, luminaire
        ]

        # Buscar palabras clave según prioridad
        for type_key in priority_order:
            if type_key not in PRODUCT_TYPES:
                continue

            type_info = PRODUCT_TYPES[type_key]

            for keyword in type_info["keywords"]:
                # Ignorar keywords que empiezan con _ (son negativas)
                if keyword.startswith("_"):
                    continue

                if keyword.lower() in pdf_lower:
                    print(f"  → Keyword detectada: '{keyword}' → {type_info['name']}")
                    return type_info

        # Si no se detecta ninguna, usar general
        return PRODUCT_TYPES["general"]

    def _detect_product_type_from_path(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """
        Detecta la tipología de producto basándose en la ruta del archivo.

        Args:
            pdf_path: Ruta del PDF

        Returns:
            Dict con la info del tipo de producto, o None si no se puede determinar
        """
        if not pdf_path:
            return None

        import os

        # Mapeo de carpetas a tipos de producto
        folder_mapping = {
            # Accesorios mecánicos
            "accesorio de columna": "accesorio_mecanico",
            "accesorio de iluminacion": "accesorio_mecanico",
            "accesorio del sistema de carril": "accesorio_mecanico",
            "accesorio mecanico": "accesorio_mecanico",

            # Equipos de alimentación
            "accesorio electrico": "equipo_alimentacion",
            "kit de emergencia": "equipo_alimentacion",

            # Columnas
            "columna": "columna",

            # Luminarias (todo lo demás)
            "alumbrado publico": "luminaria",
            "decoracion": "luminaria",
            "emergencia": "luminaria",
            "empotrables": "luminaria",
            "empotrables orientables": "luminaria",
            "interiores civil y comercial": "luminaria",
            "luminarias viales": "luminaria",
            "pantallas estancas": "luminaria",
            "pantallas estancas atex": "luminaria",
            "proyectores": "luminaria",
            "proyectores atex": "luminaria",
            "residenciales": "luminaria",
            "suspension civil e industrial": "luminaria",
            "suspension industrial - atex": "luminaria",
            "iluminacion uv para la desinfeccion": "luminaria",
        }

        # Obtener el directorio padre del archivo
        parent_dir = os.path.basename(os.path.dirname(pdf_path)).lower()

        # Buscar coincidencia en el mapeo
        for folder, type_key in folder_mapping.items():
            if folder in parent_dir:
                print(f"  → Tipología desde ruta: '{folder}' → {PRODUCT_TYPES[type_key]['name']}")
                return PRODUCT_TYPES[type_key]

        return None

    def _extract_descripcion_corta(
        self,
        pdf_text: str,
        product_type: Dict[str, str],
        target_language: str
    ) -> str:
        """
        Primera petición: Generar el párrafo de presupuesto (descripción corta).

        Args:
            pdf_text: Texto del PDF
            product_type: Tipología detectada
            target_language: Idioma de destino

        Returns:
            String con el párrafo de presupuesto
        """
        # Instrucción de idioma
        lang_map = {'ca': 'Catalán', 'eu': 'Euskera', 'es': 'Español', 'gl': 'Gallego'}
        lang_name = lang_map.get(target_language, 'Español')
        lang_instruction = ""
        if target_language != 'es':
            lang_instruction = f"- La respuesta DEBE ESTAR ESCRITA ÍNTEGRAMENTE en {lang_name}."

        # Template según tipología
        template = product_type["descripcion_corta_template"]

        # Construir prompt específico para descripción corta
        prompt = self._get_prompt_descripcion_corta(pdf_text, template, lang_instruction)

        # Llamar a Ollama
        response = self.client.chat(prompt, system_prompt=self.system_prompt)

        # Limpiar respuesta
        cleaned = self._clean_descripcion_corta(response)

        return cleaned

    def _extract_descripcion_larga(
        self,
        pdf_text: str,
        product_type: Dict[str, str],
        target_language: str
    ) -> str:
        """
        Segunda petición: Generar los detalles técnicos estructurados (descripción larga).

        Args:
            pdf_text: Texto del PDF
            product_type: Tipología detectada
            target_language: Idioma de destino

        Returns:
            String con los detalles técnicos
        """
        # Instrucción de idioma
        lang_map = {'ca': 'Catalán', 'eu': 'Euskera', 'es': 'Español', 'gl': 'Gallego'}
        lang_name = lang_map.get(target_language, 'Español')
        lang_instruction = ""
        if target_language != 'es':
            lang_instruction = f"- La respuesta DEBE ESTAR ESCRITA ÍNTEGRAMENTE EN {lang_name}."

        # Secciones según tipología
        secciones = product_type["secciones_parte_larga"]

        # Construir prompt específico para descripción larga
        prompt = self._get_prompt_descripcion_larga(pdf_text, secciones, lang_instruction, product_type)

        # Llamar a Ollama
        response = self.client.chat(prompt, system_prompt=self.system_prompt)

        # Limpiar respuesta
        cleaned = self._clean_descripcion_larga(response)

        return cleaned

    def _get_prompt_descripcion_corta(self, pdf_text: str, template: str, lang_instruction: str) -> str:
        """Genera el prompt para la primera petición (descripción corta)."""
        return f"""Genera un único párrafo de presupuesto para BC3.

**Instrucciones:**
- El párrafo debe empezar **obligatoriamente** con: "{template}"
- IMPORTANTE: Si NO encuentras un nombre específico del producto, usa SOLO el código. NO uses placeholders como "[Nombre del producto]" o "[NOMBRE]".
- Formato correcto: "{template} (Código: XXXXX)" si no hay nombre, o "{template} Nombre del Producto (Código: XXXXX)" si hay nombre.
- Incluir descripción general, aplicaciones y materiales principales.
- Incluir datos técnicos clave más importantes.
- Si tiene emergencia integrada, mencionarlo.
- Siempre añadir al final: "con certificaciones ISO 9001, ISO 14001, ISO 14002, y ISO 45001."
- Máximo 3-4 líneas de texto.

{lang_instruction}

**Ejemplos:**
- Si hay nombre: {template} Anillo de unión (Código: 426954-00) pieza metálica de aluminio...
- Si NO hay nombre: {template} (Código: 426954-00) pieza metálica de aluminio...
- JAMÁS usar: {template} [NOMBRE] (Código: XXXXX)...

**Ficha técnica:**
{pdf_text}

Genera el párrafo:"""

    def _get_prompt_descripcion_larga(
        self,
        pdf_text: str,
        secciones: list,
        lang_instruction: str,
        product_type: Dict[str, str]
    ) -> str:
        """Genera el prompt para la segunda petición (descripción larga)."""
        secciones_text = "\n".join(f"- {s}" for s in secciones)

        return f"""Extrae la información técnica detallada en formato TEXTO PLANO.

**REGLAS DE ORO ANTES DE EMPEZAR:**
- SOLO extraer información que EXPLÍCITAMENTE APAREZCA en el PDF
- PROHIBIDO inventar, alucinar o añadir información que no esté en el texto
- PROHIBITO incluir garantías si no se especifican años en el PDF
- PROHIBIDO traducir términos técnicos: mantener los nombres originales (ej: "Anillo de unión", no "Ring Coupling")
- Si un dato no aparece en el PDF, NO incluirlo

**IMPORTANTE: RESPUESTA EN TEXTO PLANO, NO JSON**
- La respuesta debe ser texto plano con secciones separadas por líneas en blanco
- PROHIBIDO usar JSON, llaves, comillas, o formato de objeto
- PROHIBIDO usar ```json o ``` al inicio o final

**Instrucciones CRÍTICAS de formato:**
- SOLO puedes usar estas secciones MAYÚSCULAS, ninguna otra:
{secciones_text}
- PROHIBIDO crear secciones que no estén en la lista anterior.
- NO uses negritas (**), ni Markdown.
- Formato: cada campo en una línea como "Clave: Valor"
- En DIMENSIONES Y PESO: Eliminar cualquier unidad entre paréntesis del nombre del campo y ponerla solo en el valor. Si el PDF dice "Longitud (mm): 352", debes escribir "Longitud: 352 mm". El formato debe ser siempre "Nombre: Valor unidad".
- NO mezcles múltiples valores en una línea.
- REGLA DE ORO: Si una sección no tiene al menos UN dato técnico específico y concreto, OMITE ESA SECCIÓN COMPLETAMENTE.
- Frases que NO son datos útiles y obligan a OMITIR la sección: "No se proporciona", "No disponible", "Ver documentación", "Consultar fabricante", "Datos no especificados", "Información no disponible", "0 yr", "N/A".
- La primera sección debe ser "INFORMACIÓN GENERAL" con: Artículo, Código.
- **IMPORTANTE**: Si el producto tiene múltiples potencias o temperaturas de color, buscar en las últimas páginas la tabla de combinaciones. Incluir esta información en una sección llamada "COMBINACIONES DISPONIBLES" con el formato: "Código: Potencia - Temperatura de color - Flujo luminoso".
- En "NORMAS Y CUMPLIMIENTO" incluir SIEMPRE Y SIN EXCEPCIÓN estas 9 líneas obligatorias, en este orden exacto:
  Certificado ISO 9001
  Certificado ISO 14001
  Certificado ISO 14002
  Certificado ISO 45001
  Certificado ISO 50001
  Certificado que acredite el cumplimiento de las directivas RoHS y RAEE
  Certificado que acredite la inscripción del fabricante en un Sistema Integrado de Gestión (SIG) de residuos
  Certificado de Productor de Producto
  Nota: Declaración Ambiental del Producto (DAP) se debe consultar siempre su disponibilidad para cada código
- INMEDIATAMENTE DESPUÉS de las 9 líneas anteriores, añadir en "NORMAS Y CUMPLIMIENTO" cualquier certificación, norma o referencia específica encontrada en la ficha técnica.

{lang_instruction}

**Ejemplo de formato CORRECTO (texto plano, NO JSON):**
INFORMACIÓN GENERAL
Artículo: Garda 4
Código: 330546-00

DIMENSIONES Y PESO
Altura: 620 mm
Diámetro: 400 mm
Longitud: 352 mm
Peso: 6 kg

MATERIALES Y ACABADOS
Material: Aluminio
Color: Negro

COMBINACIONES DISPONIBLES
112533-00: 70lm - 4000K - CRI80
112533-00: 110lm - 4000K - CRI80
112533-00: 150lm - 5700K - CRI80

NORMAS Y CUMPLIMIENTO
Certificado ISO 9001
Certificado ISO 14001
Certificado ISO 14002
Certificado ISO 45001
Certificado ISO 50001
Certificado que acredite el cumplimiento de las directivas RoHS y RAEE
Certificado que acredite la inscripción del fabricante en un Sistema Integrado de Gestión (SIG) de residuos
Certificado de Productor de Producto
Nota: Declaración Ambiental del Producto (DAP) se debe consultar siempre su disponibilidad para cada código

**Ficha técnica a procesar:**
{pdf_text}

Genera los detalles técnicos en TEXTO PLANO siguiendo ESTRICTAMENTE las instrucciones:"""

    def _clean_descripcion_corta(self, text: str) -> str:
        """Limpia la respuesta de la descripción corta."""
        # Eliminar frases introductorias
        cleaned = re.sub(
            r'^(?:Basándome en.*?:|Aquí (?:está|tienes).*?:|Claro,.*?:|El párrafo es:|Respuesta:)\s*',
            '',
            text,
            flags=re.IGNORECASE
        )

        # Eliminar markdown si existe
        cleaned = re.sub(r'```\w*\n?', '', cleaned)

        # Eliminar negritas (**texto**)
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)

        # Limpiar espacios extras
        cleaned = ' '.join(cleaned.split())

        return cleaned.strip()

    def _clean_descripcion_larga(self, text: str) -> str:
        """Limpia la respuesta de la descripción larga."""
        # Eliminar frases introductorias
        cleaned = re.sub(
            r'^(?:Basándome en.*?:|Aquí (?:está|tienes).*?:|Claro,.*?:|Los detalles son:)\s*',
            '',
            text,
            flags=re.IGNORECASE
        )

        # Eliminar markdown si existe
        cleaned = re.sub(r'```\w*\n?', '', cleaned)

        # Eliminar negritas (**texto**)
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)

        # Eliminar líneas con valores no útiles (garantía 0, N/A, etc.)
        # Patrón: elimina líneas completas que contienen estos valores
        useless_lines_patterns = [
            r'Garantía.*(?:0 yr|0 años|0años)\n',
            r'Garantía posventa.*(?:0 yr|0 años)\n',
            r'.*N/A\n',
            r'.*No disponible\n',
            r'.*No especificado\n',
            r'.*No hay información disponible\n',
        ]

        for pattern in useless_lines_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # Eliminar secciones completas que contienen información no útil
        # Patrón: NOMBRE SECCION\n\nContenido no útil\n\n
        non_useful_patterns = [
            r'[A-ZÁÉÍÓÚÑ\s]+\n\nNo proporcionada\n\n',
            r'[A-ZÁÉÓÚÑ\s]+\n\nNo especificada\n\n',
            r'[A-ZÁÉÍÓÚÑ\s]+\n\nN/A\n\n',
            r'[A-ZÁÉÍÓÚÑ\s]+\n\nNo se proporciona información[^\n]+\n\n',
            r'[A-ZÁÉÍÓÚÑ\s]+\n\nVer documentación[^\n]+\n\n',
            r'[A-ZÁÉÍÓÚÑ\s]+\n\nConsultar fabricante[^\n]+\n\n',
            r'COMBINACIONES DISPONIBLES\n\s*No hay información disponible\s*\n\n',
        ]

        for pattern in non_useful_patterns:
            cleaned = re.sub(pattern, '\n\n', cleaned, flags=re.IGNORECASE)

        # Eliminar secciones vacías (solo título sin contenido debajo)
        # Patrón: NOMBRE SECCION\n\n\n (no hay contenido antes de la siguiente sección)
        # Buscamos secciones que solo tienen el título y luego doble salto de línea
        lines = cleaned.split('\n')
        i = 0
        while i < len(lines) - 1:
            # Si línea actual es todo mayúsculas (posible título de sección)
            # Y la siguiente línea está vacía o es también mayúsculas (otra sección)
            if lines[i].strip() and lines[i].isupper() and len(lines[i]) > 3:
                if not lines[i+1].strip() or (lines[i+1].strip() and lines[i+1].isupper() and len(lines[i+1]) > 3):
                    # Eliminar esta línea (sección vacía)
                    lines.pop(i)
                    continue
            i += 1
        cleaned = '\n'.join(lines)

        # Eliminar líneas vacías excesivas (más de 2 seguidas)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        # Limpiar espacios al inicio y final
        cleaned = cleaned.strip()

        return cleaned


def extract_bc3_data(
    pdf_text: str,
    pdf_path: str = None,
    model: str = "deepseek-r1:latest",
    target_language: str = 'es',
    use_cache: bool = True,
    timeout: int = 600
) -> Dict[str, Any]:
    """
    Función auxiliar para extraer datos BC3 con dos peticiones.

    Args:
        pdf_text: Texto extraído del PDF
        pdf_path: Ruta del PDF (para caché)
        model: Modelo de Ollama a usar
        target_language: Idioma de destino
        use_cache: Si True, usa caché
        timeout: Timeout en segundos para llamadas a Ollama

    Returns:
        Dict con descripcion_corta, descripcion_larga y product_type
    """
    extractor = BC3Extractor(model=model, use_cache=use_cache, timeout=timeout)
    return extractor.extract(pdf_text, pdf_path, target_language)
