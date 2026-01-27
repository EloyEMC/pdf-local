# Scraper de Disano - Estado y Opciones

## Problema Detectado

La web de Disano (https://www.disano.it/es/cat/disano/) utiliza **JavaScript/React** para cargar contenido dinámicamente. El scraper actual con `requests` + `BeautifulSoup` **no puede ejecutar JavaScript**, por lo que no encuentra:
- Enlaces a productos individuales
- Enlaces a PDFs de descarga

## El código HTML que buscas

```html
<a href="/download/mediafiles/-5_150340-0041.pdf/ES_150340-0041.pdf" download="">
    <svg>...</svg>
    ES_150340-0041.pdf
</a>
```

## Soluciones Disponibles

### Opción 1: Usar Selenium o Playwright (Recomendado)

Estas herramientas **sí ejecutan JavaScript** y pueden ver el contenido renderizado.

**Instalar dependencias:**
```bash
pip install selenium webdriver-manager
# o
pip install playwright
playwright install
```

### Opción 2: Buscar API oculta

Muchas webs con React tienen una API JSON que usan los componentes. Podemos:
1. Abrir las DevTools del navegador (F12)
2. Ir a Network
3. Navegar por la web
4. Buscar peticiones XHR/fetch que devuelvan JSON con productos

### Opción 3: Usar el servicio de scraping de Ollama

Podemos crear un script que:
1. Descargue las páginas con Playwright
2. Pase el HTML a Ollama para que extraiga los enlaces a PDF
3. Guarde los resultados en la base de datos

## Código Actual Disponible

El scraper actual tiene:
- ✅ Conexión SSL funcionando
- ✅ Navegación básica por categorías
- ❌ Extracción de productos (requiere JavaScript)
- ❌ Extracción de PDFs (requiere JavaScript)

## Recomendación

**Usar Playwright** - Es más rápido y moderno que Selenium:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://www.disano.it/es/cat/disano/')

    # Esperar a que cargue el contenido
    page.wait_for_selector('a[href*="/download/mediafiles/"]')

    # Extraer enlaces
    pdf_links = page.eval_on_selector_all('a[href*="/download/mediafiles/"]', 'elements => elements.map(e => e.href)')

    browser.close()
```

¿Quieres que implemente el scraper con Playwright?
