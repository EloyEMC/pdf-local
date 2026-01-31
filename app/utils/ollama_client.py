import ollama
import json
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import threading

# Importar nuevas utilidades
from .cache_manager import CacheManager
from .json_validator import JSONValidator

# Configuración del modelo
MODEL = "deepseek-r1:latest"  # Modelo por defecto para mejor calidad
# Alternativas: "llama3.2:latest", "llama3.2:3b", "mistral:7b"

# System prompt para extracción de datos
SYSTEM_PROMPT = """Eres un experto en extraer información técnica de fichas técnicas de productos de construcción.
Tu tarea es extraer información estructurada del texto proporcionado y devolverla en formato JSON."""


class OllamaClient:
    """Cliente para interactuar con Ollama localmente."""

    def __init__(self, model: str = MODEL, use_cache: bool = True, timeout: int = 600):
        """
        Inicializa el cliente de Ollama.

        Args:
            model: Modelo de Ollama a usar
            use_cache: Si True, usa caché para resultados
            timeout: Timeout en segundos para llamadas a Ollama (default: 600 = 10 minutos)
        """
        self.model = model
        self.use_cache = use_cache
        self.timeout = timeout
        self.cache = CacheManager() if use_cache else None

    def chat(self, prompt: str, system_prompt: str = None) -> str:
        """
        Envía un mensaje al modelo y devuelve la respuesta.

        Args:
            prompt: Mensaje del usuario
            system_prompt: Instrucciones del sistema (opcional)

        Returns:
            Respuesta del modelo

        Raises:
            Exception: Si hay error de comunicación o timeout
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            # Usar ThreadPoolExecutor para implementar timeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    lambda: ollama.chat(model=self.model, messages=messages)
                )
                try:
                    response = future.result(timeout=self.timeout)
                    return response["message"]["content"]
                except FutureTimeoutError:
                    # Cancelar el futuro si timeout
                    future.cancel()
                    raise Exception(f"Timeout después de {self.timeout} segundos esperando respuesta de Ollama")
        except Exception as e:
            if "Timeout" in str(e):
                raise
            raise Exception(f"Error comunicando con Ollama: {str(e)}")

    def extract_data_from_pdf(self, pdf_text: str, pdf_path: str = None) -> Dict[str, Any]:
        """
        Extrae datos estructurados del texto de un PDF usando Ollama.

        Args:
            pdf_text: Texto extraído del PDF
            pdf_path: Ruta del PDF (opcional, usado para caché)

        Returns:
            Diccionario con los datos extraídos
        """
        # Si hay caché y ruta del PDF, intentar obtener del caché
        if self.cache and pdf_path:
            cached = self.cache.get(pdf_path, self.model)
            if cached:
                print(f"✓ Usando resultado cacheado para {pdf_path}")
                return cached

        # Crear prompt
        prompt = self._create_extraction_prompt(pdf_text)

        # Obtener respuesta de Ollama
        response = self.chat(prompt, system_prompt=SYSTEM_PROMPT)

        # Validar y extraer JSON
        try:
            extracted_data = JSONValidator.extract_and_validate(response)
        except ValueError as e:
            raise Exception(f"Error validando respuesta de Ollama: {str(e)}")

        # Guardar en caché si se proporcionó ruta
        if self.cache and pdf_path:
            self.cache.set(pdf_path, self.model, extracted_data)
            print(f"✓ Resultado guardado en caché")

        return extracted_data

    def extract_data_from_pdf_chunked(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Procesa múltiples chunks de PDF y combina los resultados.

        Args:
            chunks: Lista de dicts con {text, pages, chunk_id, is_complete}

        Returns:
            Diccionario combinado con todos los datos extraídos
        """
        all_results = []

        for i, chunk in enumerate(chunks, 1):
            print(f"  Procesando chunk {i}/{len(chunks)} (páginas {chunk['pages']})...")

            # Prompt específico para chunk
            chunk_prompt = self._create_chunk_prompt(chunk, len(chunks))

            response = self.chat(chunk_prompt, system_prompt=SYSTEM_PROMPT)

            try:
                chunk_data = JSONValidator.extract_and_validate(response)
                all_results.append(chunk_data)
            except Exception as e:
                print(f"    Warning: Error procesando chunk {i}: {e}")
                # Continuar con el siguiente chunk
                continue

        if not all_results:
            raise Exception("No se pudo procesar ningún chunk correctamente")

        # Combinar resultados
        return self._merge_chunk_results(all_results)

    def _create_extraction_prompt(self, pdf_text: str) -> str:
        """
        Crea el prompt para extracción de datos.

        Args:
            pdf_text: Texto del PDF

        Returns:
            Prompt completo
        """
        return f"""Extrae la siguiente información del texto de la ficha técnica y devuélvela en formato JSON:

Texto de la ficha técnica:
{pdf_text}

{self._get_json_structure_instruction()}

Responde SOLO con el JSON, sin texto adicional."""

    def _create_chunk_prompt(self, chunk: Dict[str, Any], total_chunks: int) -> str:
        """
        Crea prompt específico para procesar un chunk.

        Args:
            chunk: Dict con información del chunk
            total_chunks: Total de chunks

        Returns:
            Prompt específico para el chunk
        """
        is_first = chunk['chunk_id'] == 0
        is_last = chunk['is_complete']
        is_middle = not is_first and not is_last

        instruction = "Extrae la información técnica de este fragmento de ficha técnica.\n"

        if is_first:
            instruction += "Este es el PRINCIPIO del documento. Extrae toda la información general del producto (nombre, código, descripción principal)."
        elif is_middle:
            instruction += "Este es un FRAGMENTO INTERMEDIO. Extrae solo información técnica adicional (dimensiones detalladas, especificaciones técnicas). NO repitas información general."
        elif is_last:
            instruction += "Este es el FINAL del documento. Extrae información de garantía, normas, y completa cualquier dato faltante."

        return f"""{instruction}

Fragmento (páginas {chunk['pages']}):
{chunk['text']}

{self._get_json_structure_instruction()}

Responde SOLO con el JSON, sin texto adicional."""

    def _get_json_structure_instruction(self) -> str:
        """
        Devuelve la instrucción sobre estructura JSON esperada.

        Returns:
            String con estructura JSON
        """
        return """Devuelve un JSON con la siguiente estructura (incluye solo los campos que encuentres):
{
    "codigo_producto": "código del producto",
    "nombre": "nombre del producto",
    "descripcion": "descripción general",
    "dimensiones": {
        "alto": "altura",
        "ancho": "anchura",
        "profundidad": "profundidad",
        "peso": "peso"
    },
    "caracteristicas_electricas": {
        "tension": "tensión",
        "potencia": "potencia",
        "frecuencia": "frecuencia"
    },
    "materiales": ["lista de materiales"],
    "colores": ["lista de colores"],
    "normas": ["lista de normativas"],
    "garantia": "período de garantía",
    "observaciones": "observaciones adicionales"
}"""

    def _merge_chunk_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combina múltiples resultados de chunks en uno solo.

        Args:
            results: Lista de diccionarios extraídos de cada chunk

        Returns:
            Diccionario combinado
        """
        if not results:
            return {}

        if len(results) == 1:
            return results[0]

        merged = {}

        # Campos que se sobrescriben (usar el último no vacío)
        overwrite_fields = ['codigo_producto', 'nombre', 'descripcion']

        for field in overwrite_fields:
            for result in reversed(results):
                if result.get(field):
                    merged[field] = result[field]
                    break

        # Campos que se combinan (listas - se unen sin duplicados)
        list_fields = ['materiales', 'colores', 'normas']

        for field in list_fields:
            combined = set()
            for result in results:
                if result.get(field):
                    combined.update(result[field])
            merged[field] = list(combined)

        # Campos que se fusionan (diccionarios - se actualizan)
        merge_fields = ['dimensiones', 'caracteristicas_electricas']

        for field in merge_fields:
            merged[field] = {}
            for result in results:
                if result.get(field):
                    merged[field].update(result[field])

        # Otros campos (usar primer valor no nulo)
        other_fields = ['garantia', 'observaciones']
        for field in other_fields:
            for result in results:
                if result.get(field):
                    merged[field] = result[field]
                    break

        return merged

    def generate_bc3_structure(self, extracted_data: Dict[str, Any]) -> str:
        """
        Genera la estructura BC3 a partir de los datos extraídos.

        Args:
            extracted_data: Diccionario con los datos extraídos del PDF

        Returns:
            Estructura BC3 en formato de texto
        """
        system_prompt = """Eres un experto en el formato BC3 usado en presupuestos de construcción.
El formato BC3 tiene una estructura específica con registros que comienzan con ~."""

        prompt = f"""Genera un archivo BC3 a partir de los siguientes datos extraídos de una ficha técnica:

Datos extraídos:
{json.dumps(extracted_data, indent=2, ensure_ascii=False)}

El formato BC3 debe incluir:
- ~V: Versión del formato
- ~C: Capítulos/Conceptos con código y descripción
- ~D: Desglose de precios
- ~T: Textos/Observaciones
- ~U: Unidades
- ~M: Maquinas de auxiliares (si aplica)

Genera el contenido completo del archivo BC3 en formato de texto.
Usa un código de capítulo técnico (ejemplo: 01, 02, etc.) y subcapítulos según corresponda.
Responde solo con el contenido del archivo BC3, sin explicaciones adicionales."""

        return self.chat(prompt, system_prompt)


# Funciones auxiliares para facilitar el uso
def extract_pdf_data(pdf_text: str, model: str = None, pdf_path: str = None, timeout: int = 600) -> Dict[str, Any]:
    """
    Función auxiliar para extraer datos de un PDF.

    Args:
        pdf_text: Texto del PDF
        model: Modelo a usar (opcional)
        pdf_path: Ruta del PDF para caché (opcional)
        timeout: Timeout en segundos (opcional)

    Returns:
        Diccionario con datos extraídos
    """
    client = OllamaClient(model=model or MODEL, use_cache=True, timeout=timeout)
    return client.extract_data_from_pdf(pdf_text, pdf_path=pdf_path)


def generate_bc3(extracted_data: Dict[str, Any], model: str = None, timeout: int = 600) -> str:
    """
    Función auxiliar para generar BC3.

    Args:
        extracted_data: Datos extraídos del PDF
        model: Modelo a usar (opcional)
        timeout: Timeout en segundos (opcional)

    Returns:
        String con formato BC3
    """
    client = OllamaClient(model=model or MODEL, timeout=timeout)
    return client.generate_bc3_structure(extracted_data)
