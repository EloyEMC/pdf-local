"""
Scraper para extraer fichas técnicas en PDF de Disano usando Playwright.

Playwright puede ejecutar JavaScript, lo que permite ver el contenido dinámico
que carga la web de Disano (React).
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
from typing import List, Dict
import re


class DisanoScraperPlaywright:
    """Scraper de Disano usando Playwright para ejecutar JavaScript."""

    BASE_URL = "https://www.disano.it"
    START_URL = "https://www.disano.it/es/cat/disano/"

    def __init__(self, headless: bool = True):
        """
        Inicializa el scraper.

        Args:
            headless: Si True, no muestra la ventana del navegador
        """
        self.headless = headless
        self.browser = None
        self.page = None

    def start(self):
        """Inicia el navegador Playwright."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()

        # Configurar User-Agent
        self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        print(f"Navegador iniciado (headless={self.headless})")

    def stop(self):
        """Cierra el navegador."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("Navegador cerrado")

    def get_pdf_links_page(self, url: str, wait_time: int = 3) -> List[Dict[str, str]]:
        """
        Obtiene los enlaces a PDF de una página.

        Args:
            url: URL de la página
            wait_time: Tiempo de espera para que cargue el JavaScript (ms)

        Returns:
            Lista de diccionarios con información de los PDFs
        """
        print(f"  Visitando: {url}")

        try:
            self.page.goto(url, wait_until='networkidle', timeout=30000)

            # Esperar a que cargue el contenido dinámico
            time.sleep(wait_time / 1000)

            # Buscar todos los enlaces que contengan /download/mediafiles/
            # Esperar a que aparezcan los enlaces
            try:
                self.page.wait_for_selector('a[href*="/download/mediafiles/"]', timeout=10000)
            except PlaywrightTimeoutError:
                print("    No se encontraron enlaces a PDF (timeout)")
                return []

            # Extraer todos los enlaces a PDF
            pdf_links = self.page.eval_on_selector_all(
                'a[href*="/download/mediafiles/"]',
                '''elements => elements.map(el => ({
                    href: el.href,
                    text: el.textContent.trim(),
                    download: el.getAttribute('download')
                }))'''
            )

            # Procesar los enlaces encontrados
            results = []
            for link in pdf_links:
                if link['href'] and '.pdf' in link['href']:
                    # Extraer código de producto del nombre del archivo
                    code = self._extract_product_code(link['href'])

                    results.append({
                        'name': link['text'],
                        'url': link['href'],
                        'product_code': code,
                    })

            return results

        except Exception as e:
            print(f"    Error: {e}")
            return []

    def _extract_product_code(self, href: str) -> str:
        """Extrae el código de producto del enlace."""
        # Patrón: /download/mediafiles/-5_150340-0041.pdf/ES_150340-0041.pdf
        patterns = [
            r'/download/mediafiles/.*_(\d{6}-\d{4})\.pdf',
            r'ES_(\d{6}-\d{4})\.pdf',
            r'(\d{6}-\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, href)
            if match:
                return match.group(1)

        # Si no se encuentra patrón, extraer del nombre de archivo
        parts = href.split('/')
        if parts:
            filename = parts[-1]  # Última parte
            # Quitar extensión
            code = filename.replace('.pdf', '').replace('ES_', '')
            return code

        return ""

    def get_category_links(self) -> List[str]:
        """Obtiene los enlaces a las categorías."""
        print("Obteniendo categorías...")

        # Retornar directamente las categorías principales conocidas
        # basado en lo que el usuario especificó
        main_categories = [
            "https://www.disano.it/es/cat/disano/",
            "https://www.disano.it/es/cat/fosnova/",
        ]

        # También buscar categorías adicionales en la página
        self.page.goto(self.START_URL, wait_until='networkidle', timeout=30000)
        time.sleep(3)

        try:
            # Buscar todos los enlaces que contengan /cat/
            all_links = self.page.eval_on_selector_all(
                'a[href*="/cat/"]',
                '''elements => elements.map(el => el.href)'''
            )

            print(f"  Total de enlaces /cat/ encontrados: {len(all_links)}")

            # Buscar categorías adicionales con patrón /es/cat/XXX/
            # donde XXX no sea disano o fosnova (que ya tenemos)
            seen = set(main_categories)
            for link in all_links:
                # Patrones como /es/cat/disano/ o /es/cat/fosnova/ o /es/cat/otra-cosa/
                # Deben terminar en / (categorías principales)
                if link.endswith('/') and '/es/cat/' in link:
                    # Evitar duplicados y la página principal
                    if link not in seen and link != self.START_URL:
                        # Solo categorías directas, no subcategorías
                        # /es/cat/disano/ tiene 5 barras
                        slash_count = link.count('/')
                        if slash_count == 5:
                            print(f"  Categoría adicional encontrada: {link}")
                            seen.add(link)

            return list(seen)

        except Exception as e:
            print(f"  Error buscando categorías adicionales: {e}")
            # Retornar al menos las categorías principales
            return main_categories

    def get_subcategories(self, category_url: str) -> List[str]:
        """
        Obtiene los enlaces a subcategorías desde una página de categoría principal.

        Args:
            category_url: URL de la categoría principal (ej: /es/cat/disano/)

        Returns:
            Lista de URLs de subcategorías
        """
        print(f"\n  Buscando subcategorías en: {category_url}")

        try:
            self.page.goto(category_url, wait_until='networkidle', timeout=30000)
            time.sleep(3)

            # Buscar enlaces que sean subcategorías
            # Las subcategorías tienen URLs como /es/cat/disano/apparecchi-da-incasso/
            subcategories = self.page.eval_on_selector_all(
                'a[href*="/cat/"]',
                '''elements => elements.map(el => el.href)'''
            )

            # Filtrar para obtener solo subcategorías de esta categoría
            seen = set()
            filtered_subcats = []

            base_path = category_url.replace('https://www.disano.it', '').rstrip('/')

            for subcat in subcategories:
                # Debe contener la base path y tener un nivel adicional
                subcat_path = subcat.replace('https://www.disano.it', '').rstrip('/')

                if subcat_path.startswith(base_path) and subcat_path != base_path:
                    # Es una subcategoría si tiene un segmento adicional
                    if subcat_path.count('/') > base_path.count('/'):
                        if subcat not in seen:
                            filtered_subcats.append(subcat)
                            seen.add(subcat)

            print(f"  ✓ {len(filtered_subcats)} subcategorías encontradas")
            return filtered_subcats

        except Exception as e:
            print(f"  ! Error obteniendo subcategorías: {e}")
            return []

    def scrape_category(self, category_url: str, max_products: int = 20) -> List[Dict]:
        """
        Scrapea una categoría completa.

        Visita subcategorías y busca PDFs directamente en las páginas.

        Args:
            category_url: URL de la categoría (ej: /es/cat/disano/)
            max_products: Máximo de productos a scrapear (0 = ilimitado)

        Returns:
            Lista de PDFs encontrados
        """
        print(f"\nScrapeando categoría: {category_url}")

        all_pdfs = []

        try:
            # Obtener subcategorías
            subcategories = self.get_subcategories(category_url)

            if not subcategories:
                print("  ! No se encontraron subcategorías")
                return []

            # Visitar cada subcategoría
            for i, subcat_url in enumerate(subcategories, 1):
                if max_products > 0 and len(all_pdfs) >= max_products:
                    print(f"\n  ✓ Límite de {max_products} PDFs alcanzado")
                    break

                print(f"\n  [{i}/{len(subcategories)}] Visitando subcategoría: {subcat_url}")

                try:
                    self.page.goto(subcat_url, wait_until='networkidle', timeout=30000)
                    time.sleep(5)

                    # Primero: buscar PDFs directamente en esta página
                    print(f"    Buscando PDFs directamente en la subcategoría...")

                    # Buscar todos los enlaces que contengan "download" o ".pdf"
                    try:
                        all_download_links = self.page.eval_on_selector_all(
                            'a[href*="download"], a[href*=".pdf"]',
                            '''elements => elements.map(el => ({
                                href: el.href,
                                text: el.textContent.trim(),
                                html: el.outerHTML.substring(0, 200)
                            }))'''
                        )

                        print(f"    ✓ {len(all_download_links)} enlaces de descarga encontrados")

                        if all_download_links:
                            # Procesar los enlaces de descarga
                            for link in all_download_links[:10]:  # Primeros 10 para debugging
                                print(f"      - {link['text'][:50]}")
                                print(f"        URL: {link['href'][:80]}")

                            # Extraer PDFs válidos
                            for link in all_download_links:
                                href = link['href']
                                if '.pdf' in href.lower() or 'download' in href.lower():
                                    code = self._extract_product_code(href)
                                    all_pdfs.append({
                                        'name': link['text'] or 'PDF Disano',
                                        'url': href,
                                        'product_code': code,
                                    })

                            if max_products > 0 and len(all_pdfs) >= max_products:
                                print(f"  ✓ Límite de {max_products} PDFs alcanzado")
                                return all_pdfs[:max_products]

                    except Exception as e:
                        print(f"    ! Error buscando enlaces de descarga: {e}")

                    # Si no encontramos PDFs, intentar hacer scroll y buscar más
                    if len(all_pdfs) == 0:
                        print(f"    Haciendo scroll para cargar más contenido...")
                        try:
                            self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                            time.sleep(3)

                            # Intentar buscar de nuevo
                            scroll_pdfs = self.get_pdf_links_page(subcat_url, wait_time=3000)
                            if scroll_pdfs:
                                print(f"    ✓ {len(scroll_pdfs)} PDFs encontrados después del scroll")
                                all_pdfs.extend(scroll_pdfs)
                        except Exception as e:
                            print(f"    ! Error haciendo scroll: {e}")

                except Exception as e:
                    print(f"    ! Error visitando subcategoría: {e}")

        except Exception as e:
            print(f"    Error: {e}")
            import traceback
            traceback.print_exc()

        return all_pdfs

    def scrape_all(self, max_categories: int = 5, max_products_per_category: int = 20) -> List[Dict]:
        """
        Scrapea todo el sitio de Disano.

        Args:
            max_categories: Máximo de categorías a scrapear
            max_products_per_category: Máximo de productos por categoría

        Returns:
            Lista de todos los PDFs encontrados
        """
        all_pdfs = []

        try:
            self.start()

            # Obtener categorías
            categories = self.get_category_links()
            print(f"\n✓ {len(categories)} categorías encontradas")

            # Limitar categorías
            categories = categories[:max_categories]

            # Scrapear cada categoría
            for i, cat_url in enumerate(categories, 1):
                print(f"\n[{i}/{len(categories)}] Procesando categoría {i}...")

                category_pdfs = self.scrape_category(cat_url, max_products_per_category)
                all_pdfs.extend(category_pdfs)

                print(f"  Total acumulado: {len(all_pdfs)} PDFs")

        finally:
            self.stop()

        return all_pdfs

    def scrape_all_simple(self, max_categories: int = 3, max_products_per_category: int = 10) -> List[Dict]:
        """Versión simplificada para pruebas rápidas."""
        return self.scrape_all(max_categories, max_products_per_category)


def download_pdf(pdf_url: str, output_path: str) -> bool:
    """Descarga un PDF."""
    try:
        import requests
        import os

        # Usar las mismas variables de entorno que el scraper
        os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'

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
    scraper = DisanoScraperPlaywright(headless=False)  # headless=False para ver el navegador

    print("="*60)
    print("Scraper Disano con Playwright")
    print("="*60)

    # Scraear 1 categoría como prueba
    pdfs = scraper.scrape_all_simple(max_categories=1, max_products_per_category=5)

    print(f"\n{'='*60}")
    print(f"RESULTADO: {len(pdfs)} PDFs encontrados")
    print(f"{'='*60}\n")

    if pdfs:
        print("Primeros 10 PDFs:")
        for i, pdf in enumerate(pdfs[:10], 1):
            print(f"{i}. {pdf['name']}")
            print(f"   Código: {pdf['product_code']}")
            print(f"   URL: {pdf['url']}")
            print()

        # Guardar en CSV
        import pandas as pd
        df = pd.DataFrame(pdfs)
        df.to_csv('disano_pdfs.csv', index=False)
        print(f"✓ Guardados en disano_pdfs.csv")
