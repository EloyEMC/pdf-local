"""
Scraper para extraer fichas técnicas en PDF de Disano.

Estructura de URLs de Disano:
- Base: https://www.disano.it/es/cat/disano/
- Los PDFs están en enlaces con href="/download/mediafiles/..."
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
from typing import List, Dict
import urllib3
import os

# Configurar certificados SSL para macOS - ANTES de importar requests
os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'
os.environ['CURL_CA_BUNDLE'] = '/etc/ssl/cert.pem'
os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'

# Configurar certificados SSL para macOS
SSL_CERTIFICATES = [
    '/etc/ssl/cert.pem',
    '/usr/local/etc/openssl@1.1/cert.pem',
    '/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/certifi/cacert.pem',
]

# Desactivar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DisanoScraper:
    """Scraper de Disano para extraer fichas técnicas."""

    BASE_URL = "https://www.disano.it"
    START_URL = "https://www.disano.it/es/cat/disano/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # Buscar certificados SSL válidos
        cert_found = False
        for cert_path in SSL_CERTIFICATES:
            if os.path.exists(cert_path):
                self.session.verify = cert_path
                cert_found = True
                print(f"Usando certificados: {cert_path}")
                break

        if not cert_found:
            print("No se encontraron certificados SSL, desactivando verificación")
            self.session.verify = False

    def get_page(self, url: str) -> BeautifulSoup:
        """Descarga y parsea una página."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error accediendo a {url}: {e}")
            return None

    def extract_pdf_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extrae todos los enlaces a PDF de una página.

        Busca enlaces que contengan:
        - href con "/download/mediafiles/"
        - Extension .pdf
        - Texto o alt que contenga "PDF"
        """
        pdf_links = []

        # Buscar todos los enlaces
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Verificar si es un enlace a PDF
            if '/download/mediafiles/' in href and '.pdf' in href:
                # Extraer el nombre del archivo
                pdf_name = self._extract_pdf_name(link)

                # Construir URL completa
                pdf_url = urljoin(self.BASE_URL, href)

                pdf_links.append({
                    'name': pdf_name,
                    'url': pdf_url,
                    'product_code': self._extract_product_code(href),
                })

        return pdf_links

    def _extract_pdf_name(self, link) -> str:
        """Extrae el nombre del PDF del enlace."""
        # Buscar texto dentro del enlace
        text = link.get_text(strip=True)
        if text and '.pdf' in text.lower():
            return text

        # Buscar en atributos title o alt
        for attr in ['title', 'alt', 'data-name']:
            value = link.get(attr)
            if value:
                return value

        # Extraer del href
        href = link.get('href', '')
        parts = href.split('/')
        if parts:
            return parts[-1]

        return "Unknown"

    def _extract_product_code(self, href: str) -> str:
        """Extrae el código de producto del PDF."""
        # Patrones comunes en los nombres de archivo
        # Ejemplo: ES_150340-0041.pdf -> 150340-0041
        patterns = [
            r'ES_(\d{6}-\d{4})',
            r'(\d{6}-\d{4})',
            r'ES_([^/]+\.pdf)',
        ]

        for pattern in patterns:
            match = re.search(pattern, href)
            if match:
                return match.group(1)

        return ""

    def get_category_links(self, soup: BeautifulSoup) -> List[str]:
        """Extrae los enlaces a las categorías de productos."""
        category_links = []

        # Buscar enlaces de categorías
        # Esto depende de la estructura específica de la web
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Buscar enlaces que parezcan categorías
            if '/es/cat/' in href or '/cat/' in href:
                full_url = urljoin(self.BASE_URL, href)
                if full_url not in category_links and full_url != self.START_URL:
                    category_links.append(full_url)

        return category_links

    def get_product_links(self, soup: BeautifulSoup) -> List[str]:
        """Extrae los enlaces a productos de una página."""
        product_links = []

        # Los productos suelen tener enlaces que contienen "/es/prod/" o "/prod/"
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Buscar enlaces que parezcan productos
            if '/es/prod/' in href or '/prod/' in href:
                full_url = urljoin(self.BASE_URL, href)
                if full_url not in product_links:
                    product_links.append(full_url)

        return product_links

    def scrape_products_in_category(self, category_url: str, max_products: int = 10) -> List[Dict]:
        """
        Scrapea los productos de una categoría.

        Args:
            category_url: URL de la categoría
            max_products: Máximo de productos a scrapear (para limitar el tiempo)
        """
        print(f"  Scrapeando productos en: {category_url}")
        soup = self.get_page(category_url)

        if not soup:
            return []

        # Obtener enlaces a productos
        product_links = self.get_product_links(soup)
        print(f"    Encontrados {len(product_links)} productos")

        # Limitar número de productos
        product_links = product_links[:max_products]

        all_pdfs = []
        for i, product_url in enumerate(product_links, 1):
            print(f"    [{i}/{len(product_links)}] Visitando producto...")
            product_soup = self.get_page(product_url)

            if product_soup:
                pdfs = self.extract_pdf_links(product_soup)
                if pdfs:
                    print(f"      ✓ {len(pdfs)} PDFs encontrados")
                    all_pdfs.extend(pdfs)
                else:
                    print(f"      - No PDFs found")

            # Pausa pequeña
            time.sleep(0.5)

        return all_pdfs

    def scrape_category(self, category_url: str) -> List[Dict]:
        """Scrapea una categoría de productos."""
        print(f"Scrapeando categoría: {category_url}")
        soup = self.get_page(category_url)

        if not soup:
            return []

        # Extraer PDFs de esta página
        pdfs = self.extract_pdf_links(soup)

        # Buscar paginación
        # (implementar según la estructura de la web)

        return pdfs

    def scrape_all(self) -> List[Dict]:
        """Scrapea todo el sitio web de Disano."""
        all_pdfs = []

        print("Iniciando scrapeo de Disano...")

        # Empezar con la página principal
        soup = self.get_page(self.START_URL)

        if not soup:
            print("Error: No se pudo acceder a la página principal")
            return []

        # Obtener categorías
        category_links = self.get_category_links(soup)
        print(f"Encontradas {len(category_links)} categorías")

        # Scrapear cada categoría
        for i, category_url in enumerate(category_links, 1):
            print(f"\n[{i}/{len(category_links)}] Procesando categoría...")
            pdfs = self.scrape_category(category_url)
            all_pdfs.extend(pdfs)

            # Pausa para no sobrecargar el servidor
            time.sleep(2)

        # También buscar PDFs en la página principal
        main_pdfs = self.extract_pdf_links(soup)
        all_pdfs.extend(main_pdfs)

        return all_pdfs

    def scrape_all_simple(self, max_categories: int = 3, max_products_per_category: int = 10) -> List[Dict]:
        """
        Versión simplificada que busca todos los PDFs
        navegando por categorías y productos.

        Args:
            max_categories: Máximo de categorías a scrapear
            max_products_per_category: Máximo de productos por categoría
        """
        all_pdfs = []

        print("Iniciando scrapeo simplificado...")

        # Obtener página principal
        soup = self.get_page(self.START_URL)
        if not soup:
            return []

        # Obtener categorías
        category_links = self.get_category_links(soup)
        print(f"Encontradas {len(category_links)} categorías")

        # Limitar categorías
        category_links = category_links[:max_categories]

        # Scrapear cada categoría
        for i, category_url in enumerate(category_links, 1):
            print(f"\n[{i}/{len(category_links)}] Procesando categoría...")
            pdfs = self.scrape_products_in_category(category_url, max_products_per_category)
            all_pdfs.extend(pdfs)

            # Pausa para no sobrecargar el servidor
            time.sleep(1)

        return all_pdfs


def download_pdf(pdf_url: str, output_path: str) -> bool:
    """Descarga un PDF."""
    try:
        response = requests.get(pdf_url, timeout=30, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True
    except Exception as e:
        print(f"Error descargando {pdf_url}: {e}")
        return False


if __name__ == "__main__":
    scraper = DisanoScraper()

    # Scrapear y obtener lista de PDFs
    pdfs = scraper.scrape_all_simple()

    print(f"\n{'='*60}")
    print(f"Total de PDFs encontrados: {len(pdfs)}")
    print(f"{'='*60}\n")

    # Mostrar resultados
    for pdf in pdfs[:10]:  # Mostrar los primeros 10
        print(f"Código: {pdf['product_code']}")
        print(f"Nombre: {pdf['name']}")
        print(f"URL: {pdf['url']}")
        print("-" * 40)

    # Guardar en archivo CSV
    if pdfs:
        import pandas as pd

        df = pd.DataFrame(pdfs)
        output_file = 'disano_pdfs.csv'
        df.to_csv(output_file, index=False)
        print(f"\nGuardados {len(pdfs)} PDFs en {output_file}")
