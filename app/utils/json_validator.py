import json
import re
from typing import Dict, Any, Optional, Union, List


class JSONValidator:
    """Valida y corrige respuestas JSON de Ollama."""

    # Schema esperado de los datos extraídos
    EXPECTED_SCHEMA = {
        "codigo_producto": str,
        "nombre": str,
        "descripcion": str,
        "dimensiones": dict,
        "caracteristicas_electricas": dict,
        "materiales": list,
        "colores": list,
        "normas": list,
        "garantia": (str, type(None)),
        "observaciones": (str, type(None))
    }

    @classmethod
    def extract_and_validate(cls, response: str) -> Dict[str, Any]:
        """
        Extrae JSON de la respuesta de Ollama y lo valida.

        Args:
            response: Respuesta cruda de Ollama

        Returns:
            Diccionario validado con todos los campos esperados

        Raises:
            ValueError: Si no se puede extraer JSON válido
        """
        # 1. Extraer JSON (limpiar markdown)
        cleaned = cls._extract_json_string(response)

        # 2. Intentar parsear
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            # 3. Intentar corregir errores comunes
            corrected = cls._fix_common_json_errors(cleaned)
            try:
                data = json.loads(corrected)
            except json.JSONDecodeError as e2:
                raise ValueError(f"JSON inválido después de correcciones: {e2}. Original: {e}")

        # 4. Validar schema
        validated = cls._validate_schema(data)

        return validated

    @classmethod
    def _extract_json_string(cls, response: str) -> str:
        """
        Extrae JSON de respuestas con markdown.

        Args:
            response: Respuesta cruda de Ollama

        Returns:
            String con JSON limpio
        """
        # Eliminar bloques de código markdown
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1).strip()

        # Si no hay markdown, buscar el primer objeto JSON completo
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)

        return response.strip()

    @classmethod
    def _fix_common_json_errors(cls, json_str: str) -> str:
        """
        Corrige errores comunes en JSON malformado.

        Args:
            json_str: String JSON potencialmente malformado

        Returns:
            String JSON corregido
        """
        fixed = json_str

        # 1. Comillas simples a dobles (cuidado con contracciones)
        # Reemplazar comillas simples en valores, pero no en claves
        fixed = re.sub(r"'([^']*)'", r'"\1"', fixed)

        # 2. Trailing commas antes de }
        fixed = re.sub(r',\s*}', r'}', fixed)

        # 3. Trailing commas antes de ]
        fixed = re.sub(r',\s*]', r']', fixed)

        # 4. Comentarios de JavaScript (// ...)
        fixed = re.sub(r'//.*?\n', '\n', fixed)

        # 5. Comentarios multi-línea (/* ... */)
        fixed = re.sub(r'/\*.*?\*/', '', fixed, flags=re.DOTALL)

        # 6. Valores sin comillas que no sean true, false, null
        # Buscar patrones como : valor (donde valor no está entre comillas)
        fixed = re.sub(
            r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])',
            r': "\1"\2',
            fixed
        )

        return fixed

    @classmethod
    def _validate_schema(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida y limpia datos según schema esperado.

        Args:
            data: Diccionario de datos a validar

        Returns:
            Diccionario validado con todos los campos
        """
        validated = {}

        for key, expected_type in cls.EXPECTED_SCHEMA.items():
            if key in data:
                value = data[key]

                # Validar tipo
                if isinstance(expected_type, tuple):
                    # Acepta múltiples tipos (ej: str o None)
                    if not isinstance(value, expected_type):
                        value = None
                elif not isinstance(value, expected_type):
                    # Intentar conversión
                    value = cls._convert_type(value, expected_type)

                validated[key] = value
            else:
                # Campo faltante - usar valor por defecto
                if isinstance(expected_type, tuple):
                    # Tuple significa que acepta None como valor
                    validated[key] = None
                else:
                    # Valor por defecto según tipo
                    validated[key] = expected_type()

        return validated

    @classmethod
    def _convert_type(cls, value: Any, target_type: type) -> Any:
        """
        Intenta convertir un valor al tipo objetivo.

        Args:
            value: Valor a convertir
            target_type: Tipo objetivo

        Returns:
            Valor convertido o valor por defecto del tipo
        """
        try:
            if target_type == dict:
                if isinstance(value, str):
                    return {}
                return dict(value) if hasattr(value, '__iter__') else {}
            elif target_type == list:
                if isinstance(value, str):
                    return []
                return list(value) if hasattr(value, '__iter__') else []
            elif target_type == str:
                return str(value)
            else:
                return target_type()
        except:
            # Si falla la conversión, retornar valor por defecto
            if target_type in (dict, list, str):
                return target_type()
            return None

    @classmethod
    def validate_partial(cls, data: Dict[str, Any], required_fields: List[str] = None) -> Dict[str, Any]:
        """
        Valida datos parciales (no todos los campos son requeridos).

        Args:
            data: Datos a validar
            required_fields: Lista de campos requeridos (opcional)

        Returns:
            Diccionario validado
        """
        validated = cls._validate_schema(data)

        # Verificar campos requeridos
        if required_fields:
            missing = [f for f in required_fields if not validated.get(f)]
            if missing:
                raise ValueError(f"Campos requeridos faltantes: {', '.join(missing)}")

        return validated
