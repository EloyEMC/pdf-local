from .ollama_client import OllamaClient, extract_pdf_data, generate_bc3
from .pdf_extractor import (
    extract_pdf_text,
    extract_pdf_to_dict,
    extract_pdf_text_chunked,
    extract_pdf_to_dict_chunked,
    validate_pdf,
    get_pdf_info,
    extract_bc3_from_pdf
)
from .cache_manager import CacheManager
from .json_validator import JSONValidator
from .bc3_extractor import BC3Extractor, extract_bc3_data

__all__ = [
    # Ollama client
    'OllamaClient',
    'extract_pdf_data',
    'generate_bc3',

    # PDF extractor
    'extract_pdf_text',
    'extract_pdf_to_dict',
    'extract_pdf_text_chunked',
    'extract_pdf_to_dict_chunked',
    'validate_pdf',
    'get_pdf_info',
    'extract_bc3_from_pdf',

    # Cache
    'CacheManager',

    # JSON validator
    'JSONValidator',

    # BC3 extractor (dos peticiones)
    'BC3Extractor',
    'extract_bc3_data',
]
