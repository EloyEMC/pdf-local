#!/usr/bin/env python3
"""
Script para investigar la estructura de la web de Disano.
"""

import sys
sys.path.insert(0, '/Volumes/WEBS/Pdf-local')

from app.utils.disano_scraper import DisanoScraper
from urllib.parse import urljoin

scraper = DisanoScraper()

# Obtener una página de categoría
soup = scraper.get_page("https://www.disano.it/es/cat/disano/10502-recessed-modulars")

if not soup:
    print("Error obteniendo la página")
    sys.exit(1)

print("Analizando enlaces en la página de categoría...\n")

# Buscar todos los enlaces
all_links = []
for link in soup.find_all('a', href=True):
    href = link['href']
    text = link.get_text(strip=True)[:50]  # Primeros 50 caracteres

    all_links.append({
        'href': href,
        'text': text,
        'full_url': urljoin(scraper.BASE_URL, href)
    })

# Mostrar patrones encontrados
patterns = {}

for link in all_links:
    href = link['href']

    # Identificar patrones
    if '/download/mediafiles/' in href:
        pattern = 'PDF download'
    elif '/es/prod/' in href or '/prod/' in href:
        pattern = 'Producto'
    elif '/es/cat/' in href or '/cat/' in href:
        pattern = 'Categoría'
    elif href.startswith('http'):
        pattern = 'External'
    else:
        pattern = 'Other'

    if pattern not in patterns:
        patterns[pattern] = []

    patterns[pattern].append(link)

# Mostrar resultados
print("Patrones encontrados:")
print("="*60)

for pattern, links in sorted(patterns.items()):
    print(f"\n{pattern}: {len(links)} enlaces")

    if pattern in ['Producto', 'PDF download']:
        for link in links[:10]:  # Mostrar primeros 10
            print(f"  - {link['text']}")
            print(f"    {link['href']}")

# Mostrar algunos enlaces aleatorios para investigación
print("\n" + "="*60)
print("Muestra de todos los enlaces:")
print("="*60)

for i, link in enumerate(all_links[:30], 1):
    print(f"{i}. [{link['href'][:60]}]")
    if link['text']:
        print(f"   Texto: {link['text']}")
