#!/usr/bin/env python3
"""
Script de prueba del scraper con Playwright.
"""

import sys
sys.path.insert(0, '/Volumes/WEBS/Pdf-local')

from app.utils.disano_scraper_playwright import DisanoScraperPlaywright

print("="*60)
print("TEST - Scraper Disano con Playwright")
print("="*60)
print("\nEste scraper SÍ ejecuta JavaScript, por lo que debería")
print("encontrar los PDFs que se cargan dinámicamente.\n")

# Crear scraper con headless=False para ver el navegador
scraper = DisanoScraperPlaywright(headless=False)

print("Iniciando navegador (verás la ventana de Chrome)...\n")

try:
    # Scrapear 1 categoría con 2 productos (solo 2 fichas)
    pdfs = scraper.scrape_all_simple(max_categories=1, max_products_per_category=2)

    print(f"\n{'='*60}")
    print(f"RESULTADO: {len(pdfs)} PDFs encontrados")
    print(f"{'='*60}\n")

    if pdfs:
        print("PDFs encontrados:")
        for i, pdf in enumerate(pdfs, 1):
            print(f"{i}. {pdf['name']}")
            print(f"   Código: {pdf['product_code']}")
            print(f"   URL: {pdf['url']}")
            print()

        # Guardar en CSV
        import pandas as pd
        df = pd.DataFrame(pdfs)
        filename = 'disano_pdfs_test.csv'
        df.to_csv(filename, index=False)
        print(f"✓ Guardados en {filename}")
    else:
        print("❌ No se encontraron PDFs")
        print("\nPosibles causas:")
        print("  - La web ha cambiado su estructura")
        print("  - Los PDFs se cargan de forma diferente")
        print("  - Necesitamos más tiempo de espera")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
