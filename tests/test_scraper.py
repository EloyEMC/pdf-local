#!/usr/bin/env python3
"""
Script de prueba para el scraper de Disano.
"""

import sys
sys.path.insert(0, '/Volumes/WEBS/Pdf-local')

from app.utils.disano_scraper import DisanoScraper

print("="*60)
print("TEST - Scraper Disano")
print("="*60)

scraper = DisanoScraper()

# Probar conexión
print("\n1. Probando conexión con Disano...")
soup = scraper.get_page(scraper.START_URL)

if soup:
    print("   ✓ Conexión exitosa")
    print(f"   Título: {soup.title.string if soup.title else 'N/A'}")
else:
    print("   ✗ Error de conexión")
    sys.exit(1)

# Probar extracción de PDFs
print("\n2. Buscando PDFs en la página principal...")
pdfs = scraper.extract_pdf_links(soup)

if pdfs:
    print(f"   ✓ Encontrados {len(pdfs)} PDFs")
    print("\n   Primeros 5 PDFs:")
    for i, pdf in enumerate(pdfs[:5], 1):
        print(f"   {i}. {pdf['name']}")
        print(f"      Código: {pdf['product_code']}")
        print(f"      URL: {pdf['url'][:80]}...")
else:
    print("   ✗ No se encontraron PDFs")

# Probar extracción de categorías
print("\n3. Buscando categorías...")
categories = scraper.get_category_links(soup)

if categories:
    print(f"   ✓ Encontradas {len(categories)} categorías")
    print("\n   Primeras 5 categorías:")
    for i, cat in enumerate(categories[:5], 1):
        print(f"   {i}. {cat}")
else:
    print("   ✗ No se encontraron categorías")

print("\n" + "="*60)
print("TEST COMPLETADO")
print("="*60)
print(f"\nTotal PDFs encontrados: {len(pdfs)}")
print(f"Total categorías: {len(categories)}")
