"""Configuración de la aplicación."""

# Configuración de Ollama
OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434
OLLAMA_MODEL = "deepseek-r1:latest"

# Modelos disponibles
AVAILABLE_MODELS = {
    "deepseek-r1:latest": "DeepSeek R1 - Mejor calidad",
    "llama3.2:latest": "Llama 3.2 - Modelo completo",
    "llama3.2:3b": "Llama 3.2 3B - Rápido y eficiente",
    "mistral:7b": "Mistral 7B - Buen rendimiento",
    "gemma3:4b": "Gemma 3 4B - Modelo de Google",
}

# Configuración de la aplicación
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB
ALLOWED_EXTENSIONS = {'pdf'}

# Paths
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
CACHE_DIR = os.path.join(BASE_DIR, 'cache')

# Configuración de chunking
MAX_CHARS_PER_CHUNK = 8000
OVERLAP_CHARS = 500
MAX_PAGES_PER_CHUNK = 5

# Configuración de caché
CACHE_ENABLED = True
CACHE_TTL_HOURS = 24

# Configuración de validación JSON
JSON_VALIDATION_ENABLED = True
