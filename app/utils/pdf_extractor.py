import pdfplumber
from typing import Optional, List, Dict, Any


# Constantes de configuración para chunking
MAX_CHARS_PER_CHUNK = 8000  # Dejar margen para el prompt
OVERLAP_CHARS = 500  # Superposición para mantener contexto
MAX_PAGES_PER_CHUNK = 5  # Máximo de páginas por chunk


def extract_pdf_text(pdf_path: str, remove_headers: bool = True) -> str:
    """
    Extrae el texto de un PDF.

    Args:
        pdf_path: Ruta al archivo PDF
        remove_headers: Si es True, elimina cabeceras y pies de página comunes

    Returns:
        Texto extraído del PDF
    """
    if not pdf_path:
        raise ValueError("Se requiere una ruta válida al archivo PDF")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                raise ValueError("El PDF no tiene páginas")

            if remove_headers and len(pdf.pages) > 1:
                return _extract_with_header_removal(pdf)
            else:
                return _extract_simple(pdf)

    except Exception as e:
        raise Exception(f"Error extrayendo texto del PDF: {str(e)}")


def extract_pdf_text_chunked(pdf_path: str, remove_headers: bool = True) -> List[Dict[str, Any]]:
    """
    Extrae texto del PDF en chunks si es muy largo.

    Args:
        pdf_path: Ruta al archivo PDF
        remove_headers: Si es True, elimina cabeceras y pies de página comunes

    Returns:
        Lista de dicts: [{"text": "...", "pages": [1, 2], "chunk_id": 0, "is_complete": bool}, ...]
    """
    if not pdf_path:
        raise ValueError("Se requiere una ruta válida al archivo PDF")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                raise ValueError("El PDF no tiene páginas")

            total_pages = len(pdf.pages)

            # Si es corto, extraer normalmente (un solo chunk)
            if total_pages <= MAX_PAGES_PER_CHUNK:
                full_text = _extract_with_header_removal(pdf) if remove_headers else _extract_simple(pdf)
                return [{
                    "text": full_text,
                    "pages": list(range(1, total_pages + 1)),
                    "chunk_id": 0,
                    "is_complete": True
                }]

            # Si es largo, hacer chunking
            print(f"PDF con {total_pages} páginas. Dividiendo en chunks...")
            return _create_chunks(pdf, remove_headers)

    except Exception as e:
        raise Exception(f"Error extrayendo texto del PDF: {str(e)}")


def _extract_simple(pdf) -> str:
    """Extracción simple sin eliminar cabeceras."""
    text = ""
    for page in pdf.pages:
        page_text = page.extract_text() or ""
        text += page_text + "\n\n"
    return text.strip()


def _extract_with_header_removal(pdf) -> str:
    """Elimina cabeceras y pies de página comunes entre páginas."""
    pages_lines = []

    # Extraer líneas de cada página
    for page in pdf.pages:
        page_text = page.extract_text() or ""
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        pages_lines.append(lines)

    if not pages_lines:
        return ""

    # Encontrar líneas comunes (cabeceras/pies de página)
    common_lines = set(pages_lines[0])
    for lines in pages_lines[1:]:
        common_lines &= set(lines)

    # Filtrar líneas comunes cortas (típicamente cabeceras/pies)
    common_lines = {line for line in common_lines if len(line) < 80}

    # Reconstruir texto sin cabeceras/pies
    filtered_text = ""
    for lines in pages_lines:
        filtered = [line for line in lines if line not in common_lines]
        filtered_text += "\n".join(filtered) + "\n\n"

    return filtered_text.strip()


def _create_chunks(pdf, remove_headers: bool) -> List[Dict[str, Any]]:
    """
    Crea chunks del PDF manteniendo contexto.

    Args:
        pdf: Objeto PDF abierto con pdfplumber
        remove_headers: Si se deben eliminar cabeceras

    Returns:
        Lista de dicts con información de cada chunk
    """
    chunks = []
    current_chunk = ""
    current_pages = []
    chunk_id = 0

    for i, page in enumerate(pdf.pages, 1):
        page_text = page.extract_text() or ""

        # Si añadir esta página excede el límite
        if len(current_chunk) + len(page_text) > MAX_CHARS_PER_CHUNK and current_chunk:
            # Guardar chunk actual
            chunks.append({
                "text": current_chunk.strip(),
                "pages": current_pages.copy(),
                "chunk_id": chunk_id,
                "is_complete": False
            })
            chunk_id += 1

            # Empezar nuevo chunk con superposición
            current_chunk = _get_overlap_text(current_chunk) + "\n\n" + page_text
            # Mantener últimas 1-2 páginas en el contexto
            current_pages = current_pages[-2:] + [i] if len(current_pages) > 2 else [i]
        else:
            # Añadir al chunk actual
            current_chunk += page_text + "\n\n"
            current_pages.append(i)

    # Añadir último chunk
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "pages": current_pages,
            "chunk_id": chunk_id,
            "is_complete": True
        })

    print(f"  Dividido en {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"    Chunk {i}: páginas {chunk['pages']}, ~{len(chunk['text'])} caracteres")

    return chunks


def _get_overlap_text(text: str) -> str:
    """
    Extrae las últimas OVERLAP_CHARS para mantener contexto entre chunks.

    Args:
        text: Texto del chunk actual

    Returns:
        Texto de superposición
    """
    lines = text.split('\n')
    overlap_lines = []
    total_chars = 0

    for line in reversed(lines):
        if total_chars + len(line) > OVERLAP_CHARS:
            break
        overlap_lines.insert(0, line)
        total_chars += len(line) + 1  # +1 por el newline

    return '\n'.join(overlap_lines)


def extract_pdf_to_dict(pdf_path: str, ollama_client=None) -> dict:
    """
    Extrae datos estructurados del PDF usando Ollama.

    Args:
        pdf_path: Ruta al archivo PDF
        ollama_client: Cliente de Ollama (opcional)

    Returns:
        Diccionario con los datos extraídos
    """
    from .ollama_client import OllamaClient

    # Extraer texto del PDF
    pdf_text = extract_pdf_text(pdf_path)

    # Usar Ollama para estructurar los datos
    client = ollama_client or OllamaClient(use_cache=True)
    structured_data = client.extract_data_from_pdf(pdf_text, pdf_path=pdf_path)

    return structured_data


def extract_pdf_to_dict_chunked(pdf_path: str, ollama_client=None) -> dict:
    """
    Extrae datos estructurados del PDF usando Ollama con chunking si es necesario.

    Args:
        pdf_path: Ruta al archivo PDF
        ollama_client: Cliente de Ollama (opcional)

    Returns:
        Diccionario con los datos extraídos
    """
    from .ollama_client import OllamaClient

    # Extraer texto en chunks
    chunks = extract_pdf_text_chunked(pdf_path)

    # Usar Ollama para estructurar los datos
    client = ollama_client or OllamaClient(use_cache=True)

    if len(chunks) > 1:
        # Procesar con chunking
        print(f"Procesando {len(chunks)} chunks con Ollama...")
        structured_data = client.extract_data_from_pdf_chunked(chunks)
    else:
        # Procesar normalmente (un solo chunk)
        structured_data = client.extract_data_from_pdf(chunks[0]['text'], pdf_path=pdf_path)

    return structured_data


def validate_pdf(pdf_path: str) -> bool:
    """
    Valida que el archivo sea un PDF válido.

    Args:
        pdf_path: Ruta al archivo PDF

    Returns:
        True si es un PDF válido
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return len(pdf.pages) > 0
    except:
        return False


def get_pdf_info(pdf_path: str) -> Dict[str, Any]:
    """
    Obtiene información básica sobre un PDF.

    Args:
        pdf_path: Ruta al archivo PDF

    Returns:
        Diccionario con información del PDF
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return {
                'valid': True,
                'pages': len(pdf.pages),
                'size_bytes': len(open(pdf_path, 'rb').read()),
                'needs_chunking': len(pdf.pages) > MAX_PAGES_PER_CHUNK
            }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e)
        }


def extract_bc3_from_pdf(
    pdf_path: str,
    model: str = "deepseek-r1:latest",
    target_language: str = 'es',
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Extrae datos BC3 usando el sistema de dos peticiones.

    Args:
        pdf_path: Ruta al archivo PDF
        model: Modelo de Ollama a usar
        target_language: Idioma de destino (es, ca, eu, gl)
        use_cache: Si True, usa caché

    Returns:
        Dict con descripcion_corta, descripcion_larga y product_type
    """
    from .bc3_extractor import extract_bc3_data

    # Extraer texto del PDF
    chunks = extract_pdf_text_chunked(pdf_path)

    # Si hay múltiples chunks, combinar el texto
    if len(chunks) > 1:
        pdf_text = "\n\n".join(chunk['text'] for chunk in chunks)
    else:
        pdf_text = chunks[0]['text']

    # Extraer datos BC3
    return extract_bc3_data(
        pdf_text,
        pdf_path=pdf_path,
        model=model,
        target_language=target_language,
        use_cache=use_cache
    )
