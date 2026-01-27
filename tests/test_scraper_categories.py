#!/usr/bin/env python3
"""
Script de prueba para scrapear categorías de Disano.
"""

import sys
sys.path.insert(0, '/Volumes/WEBS/Pdf-local')

from app.utils.disano_scraper import DisanoScraper

print("="*60)
print("TEST - Scraper Disano (Categorías)")
print("="*60)

scraper = DisanoScraper()

# Obtener página principal
print("\n1. Obteniendo página principal...")
soup = scraper.get_page(scraper.START_URL)

if not soup:
    print("   ✗ Error de conexión")
    sys.exit(1)

# Obtener categorías
print("\n2. Obteniendo categorías...")
categories = scraper.get_category_links(soup)
print(f"   ✓ {len(categories)} categorías encontradas")

# Scraear las primeras 3 categorías
all_pdfs = []
for i, cat_url in enumerate(categories[:3], 1):
    print(f"\n3.{i} Scrapeando categoría {i}: {cat_url.split('/')[-1]}")

    cat_soup = scraper.get_page(cat_url)
    if cat_soup:
        pdfs = scraper.extract_pdf_links(cat_soup)

        if pdfs:
            print(f"      ✓ {len(pdfs)} PDFs encontrados")
            all_pdfs.extend(pdfs)

            # Mostrar primeros 3
            for pdf in pdfs[:3]:
                print(f"         - {pdf['name']}")
                print(f"           Código: {pdf['product_code']}")
        else:
            print(f"      - No se encontraron PDFs")

    # Pequeña pausa
    import time
    time.sleep(1)

print(f"\n{'='*60}")
print(f"RESULTADO: {len(all_pdfs)} PDFs encontrados en total")
print(f"{'='*60}")

if all_pdfs:
    print("\nPrimeros 10 PDFs:")
    for pdf in all_pdfs[:10]:
        print(f"  • {pdf['name']}")
        print(f"    URL: {pdf['url']}")
