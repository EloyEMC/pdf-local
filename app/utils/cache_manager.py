import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class CacheManager:
    """Gestiona el caché de resultados de procesamiento de PDFs."""

    def __init__(self, cache_dir: str = None, ttl_hours: int = 24):
        """
        Inicializa el gestor de caché.

        Args:
            cache_dir: Directorio para guardar archivos de caché
            ttl_hours: Tiempo de vida en horas
        """
        if cache_dir is None:
            # Por defecto, usar directorio cache/ en la raíz del proyecto
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cache_dir = os.path.join(base_dir, 'cache')

        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_pdf_hash(self, pdf_path: str) -> str:
        """
        Genera hash único del PDF basado en contenido.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Hash MD5 hexadecimal
        """
        with open(pdf_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def get(self, pdf_path: str, model: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene resultado cacheado si existe y es válido.

        Args:
            pdf_path: Ruta al archivo PDF
            model: Modelo de Ollama usado

        Returns:
            Diccionario con datos cacheados o None si no existe/expiró
        """
        cache_key = self._get_cache_key(pdf_path, model)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if not os.path.exists(cache_file):
            return None

        # Verificar TTL
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age > self.ttl:
            try:
                os.remove(cache_file)
            except:
                pass
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            # Archivo corrupto, eliminar y retornar None
            try:
                os.remove(cache_file)
            except:
                pass
            return None

    def set(self, pdf_path: str, model: str, data: Dict[str, Any]):
        """
        Guarda resultado en caché.

        Args:
            pdf_path: Ruta al archivo PDF
            model: Modelo de Ollama usado
            data: Datos a guardar
        """
        cache_key = self._get_cache_key(pdf_path, model)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_cache_key(self, pdf_path: str, model: str) -> str:
        """
        Genera clave de caché única.

        Args:
            pdf_path: Ruta al archivo PDF
            model: Modelo de Ollama usado

        Returns:
            Clave única para el caché
        """
        pdf_hash = self._get_pdf_hash(pdf_path)
        # Reemplazar dos puntos en el nombre del modelo (no válidos en nombres de archivo)
        model_safe = model.replace(':', '_')
        return f"{pdf_hash}_{model_safe}"

    def invalidate(self, pdf_path: str = None):
        """
        Invalida caché (un PDF específico o todo).

        Args:
            pdf_path: Ruta al PDF específico. Si es None, limpia todo el caché.
        """
        if pdf_path:
            # Buscar y eliminar archivos de caché relacionados
            try:
                pdf_hash = self._get_pdf_hash(pdf_path)
                for filename in os.listdir(self.cache_dir):
                    if filename.startswith(pdf_hash):
                        os.remove(os.path.join(self.cache_dir, filename))
            except:
                pass
        else:
            # Limpiar todo el caché
            try:
                for filename in os.listdir(self.cache_dir):
                    os.remove(os.path.join(self.cache_dir, filename))
            except:
                pass

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el caché.

        Returns:
            Diccionario con estadísticas del caché
        """
        try:
            files = os.listdir(self.cache_dir)
            total_size = sum(
                os.path.getsize(os.path.join(self.cache_dir, f))
                for f in files
            )

            return {
                'cache_dir': self.cache_dir,
                'cached_files': len(files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'ttl_hours': self.ttl.total_seconds() / 3600
            }
        except:
            return {
                'cache_dir': self.cache_dir,
                'cached_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'ttl_hours': self.ttl.total_seconds() / 3600
            }
