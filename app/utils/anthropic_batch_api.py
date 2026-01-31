"""
Implementación de Batch API de Anthropic usando requests.
Proporciona 50% descuento sobre los precios normales.
"""

import os
import time
import json
import requests as http_requests
from typing import List, Dict, Any
from pathlib import Path


class AnthropicBatchAPI:
    """Cliente para la Batch API de Anthropic con 50% descuento."""

    def __init__(self, api_key: str = None):
        """Inicializa el cliente Batch API."""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise Exception("ANTHROPIC_API_KEY no está configurada")

        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        # Configurar certificados SSL
        self.cert_path = "/Volumes/WEBS/Pdf-local/venv/lib/python3.14/site-packages/certifi/cacert.pem"
        self.verify = self.cert_path

    def create_batch_request(self, custom_id: str, prompt: str, model: str = "claude-3-5-haiku-latest") -> Dict:
        """Crea una solicitud individual para el batch."""
        return {
            "custom_id": custom_id,
            "request": {
                "model": model,
                "max_tokens": 4096,
                "temperature": 0.0,
                "system": "Eres un experto en procesamiento de fichas técnicas.",
                "messages": [{"role": "user", "content": prompt}]
            }
        }

    def submit_batch(self, requests: List[Dict]) -> str:
        """
        Envía un batch de solicitudes a procesar.

        Args:
            requests: Lista de solicitudes batch

        Returns:
            batch_id: ID del batch creado
        """
        url = f"{self.base_url}/messages/batches"

        payload = {
            "requests": requests
        }

        response = http_requests.post(url, json=payload, headers=self.headers, verify=self.verify)
        response.raise_for_status()

        result = response.json()
        return result["id"]

    def get_batch_status(self, batch_id: str) -> Dict:
        """
        Obtiene el estado de un batch.

        Args:
            batch_id: ID del batch

        Returns:
            Dict con estado y resultados
        """
        url = f"{self.base_url}/messages/batches/{batch_id}"

        response = http_requests.get(url, headers=self.headers, verify=self.verify)
        response.raise_for_status()

        return response.json()

    def wait_for_completion(self, batch_id: str, check_interval: int = 30, timeout: int = 3600) -> Dict:
        """
        Espera a que un batch se complete.

        Args:
            batch_id: ID del batch
            check_interval: Segundos entre verificaciones (default: 30)
            timeout: Tiempo máximo de espera (default: 3600 = 1 hora)

        Returns:
            Dict con estado final y resultados
        """
        start_time = time.time()

        print(f"⏳ Esperando completación del batch {batch_id}...")

        while True:
            # Verificar timeout
            if time.time() - start_time > timeout:
                raise Exception(f"Timeout esperando batch {batch_id}")

            # Obtener estado
            status = self.get_batch_status(batch_id)

            processing = status.get("results", {}).get("processing", 0)
            succeeded = status.get("results", {}).get("succeeded", 0)
            failed = status.get("results", {}).get("failed", 0)
            total = processing + succeeded + failed

            print(f"   Progreso: {total}/{len(status.get('request_counts', {}).get('processed', 0))} "
                  f"(✅{succeeded} ❌{failed} ⏳{processing})")

            # Verificar si completó
            if status.get("processing_status") in ["succeeded", "failed", "canceled"]:
                print(f"✅ Batch completado: {status.get('processing_status')}")
                return status

            # Esperar antes de siguiente verificación
            time.sleep(check_interval)

    def retrieve_results(self, batch_id: str) -> List[Dict]:
        """
        Recupera todos los resultados de un batch completado.

        Args:
            batch_id: ID del batch

        Returns:
            Lista de resultados con custom_id y contenido
        """
        status = self.get_batch_status(batch_id)

        results = []
        for result in status.get("results", []):
            results.append({
                "custom_id": result.get("custom_id"),
                "result_type": result.get("result_type"),
                "message": result.get("message", {}),
                "error": result.get("error")
            })

        return results
