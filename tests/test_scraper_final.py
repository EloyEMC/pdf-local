#!/usr/bin/env python3
"""
Script de prueba final para el scraper de Disano.
"""

import sys
sys.path.insert(0, '/Volumes/WEBS/Pdf-local')

from app.utils.disano_scraper import DisanoScraper

print("="*60)
print("TEST FINAL - Scraper Disano")
print("="*60)

scraper = DisanoScraper()

# Scrapear 1 categoría con 5 productos como prueba
print("\nScrapeando 1 categoría, 5 productos...")
print("Esto puede tardar unos minutos...\n")

pdfs = scraper.scrape_all_simple(max_categories=1, max_products_per_category=5)

print(f"\n{'='*60}")
print(f"RESULTADO: {len(pdfs)} PDFs encontrados")
print(f"{'='*60}\n")

if pdfs:
    print("PDFs encontrados:")
    for i, pdf in enumerate(pdfs[:20], 1):  # Mostrar máximo 20
        print(f"{i}. {pdf['name']}")
        print(f"   Código: {pdf['product_code']}")
        print(f"   URL: {pdf['url']}")
        print()

    if len(pdfs) > 20:
        print(f"... y {len(pdfs) - 20} más")

    # Guardar en CSV
    import pandas as pd
    df = pd.DataFrame(pdfs)
    filename = 'disano_pdfs_test.csv'
    df.to_csv(filename, index=False)
    print(f"✓ Guardados en {filename}")
else:
    print("No se encontraron PDFs")

