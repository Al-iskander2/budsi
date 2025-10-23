# -*- coding: utf-8 -*-
"""
Tester visual automático para Budsi - Solo prints en terminal
"""

import time
import argparse
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------------- Config ----------------
DEFAULT_BASE = "http://127.0.0.1:8000/"
MAX_PAGES_DEFAULT = 30
CRAWL_DEPTH_DEFAULT = 2

# Semillas para rutas conocidas
SEED_PATHS = [
    "/", "/onboard/", "/tax/report/", "/dashboard/", "/login/", 
    "/register/", "/pricing/", "/expenses/", "/track/"
]

# --------------- Selenium ---------------
def launch_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1440,900")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    return driver

# --------------- Detectores principales ---------------
def detect_margin_collapse(driver):
    """Detecta el hueco/línea sobre navbar por colapso de márgenes"""
    try:
        result = driver.execute_script("""
            const main = document.querySelector('main.main-wrapper');
            const header = document.querySelector('header');
            if (!main || !header) return {suspected: false, reason: 'Missing elements'};
            
            const mainRect = main.getBoundingClientRect();
            const headerRect = header.getBoundingClientRect();
            const gap = mainRect.top - headerRect.bottom;
            
            // Buscar el primer hijo visible con margin-top
            let firstChild = null;
            for (let child of main.children) {
                if (getComputedStyle(child).display !== 'none') {
                    firstChild = child;
                    break;
                }
            }
            
            if (!firstChild) return {suspected: false, reason: 'No visible children'};
            
            const childStyle = getComputedStyle(firstChild);
            const mainStyle = getComputedStyle(main);
            
            const childMarginTop = parseFloat(childStyle.marginTop);
            const mainPaddingTop = parseFloat(mainStyle.paddingTop);
            const mainBorderTop = parseFloat(mainStyle.borderTopWidth);
            
            const suspected = (childMarginTop > 0 && mainPaddingTop === 0 && mainBorderTop === 0 && gap > 0);
            
            return {
                suspected: suspected,
                gap_px: gap,
                child_margin_top: childMarginTop,
                main_padding_top: mainPaddingTop,
                main_border_top: mainBorderTop,
                child_tag: firstChild.tagName
            };
        """)
        return result
    except Exception as e:
        return {"suspected": False, "error": str(e)}

def detect_logo_issues(driver):
    """Detecta logos sobredimensionados"""
    try:
        logos = driver.execute_script("""
            const logos = [];
            const elements = document.querySelectorAll('img[alt*=\"logo\" i], .navbar-brand img, [class*=\"logo\" i] img');
            
            for (let img of elements) {
                const rect = img.getBoundingClientRect();
                const computedHeight = rect.height;
                const isOversized = computedHeight > 56;
                
                if (isOversized) {
                    logos.push({
                        src: img.src.split('/').pop(), // solo nombre archivo
                        alt: img.alt || 'sin alt',
                        classes: img.className,
                        computed_height: Math.round(computedHeight)
                    });
                }
            }
            return logos;
        """)
        return logos
    except Exception as e:
        return []

def detect_bootstrap(driver):
    """Detecta si Bootstrap está presente"""
    try:
        bootstrap_data = driver.execute_script("""
            const links = Array.from(document.querySelectorAll('link[rel=\"stylesheet\"]'));
            const bootstrapLinks = links.filter(link => 
                link.href && link.href.toLowerCase().includes('bootstrap')
            );
            
            const bootstrapClasses = document.querySelector('.container, .row, .navbar, .btn');
            
            return {
                detected: bootstrapLinks.length > 0 || !!bootstrapClasses
            };
        """)
        return bootstrap_data.get('detected', False)
    except Exception:
        return False

# --------------- Crawler ---------------
def crawl_links(base_url, max_pages=MAX_PAGES_DEFAULT, depth=CRAWL_DEPTH_DEFAULT):
    """Crawler que incluye semillas y encuentra más páginas"""
    seen = set()
    queue = [(urljoin(base_url, path), 0) for path in SEED_PATHS]
    pages = []

    while queue and len(pages) < max_pages:
        url, current_depth = queue.pop(0)
        
        if url in seen:
            continue
        seen.add(url)
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                pages.append(url)
                print(f"✅ Encontrada: {url}")

                if current_depth < depth:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(base_url, href)
                        
                        # Filtrar enlaces internos válidos
                        if (full_url.startswith(base_url) and
                            full_url not in seen and
                            not any(excl in full_url for excl in ['/logout', '/admin/', '/static/'])):
                            queue.append((full_url, current_depth + 1))
                            
        except Exception as e:
            print(f"❌ Error al acceder {url}: {e}")

    return pages

# --------------- Análisis por página ---------------
def analyze_page(url):
    """Analiza una página y detecta problemas"""
    print(f"\n🔍 Analizando: {url}")
    driver = launch_driver(headless=True)
    
    try:
        driver.get(url)
        time.sleep(2)

        # Ejecutar todos los detectores
        margin_issue = detect_margin_collapse(driver)
        logo_issue = detect_logo_issues(driver) 
        bootstrap_detected = detect_bootstrap(driver)

        has_issues = False

        # Mostrar resultados en consola
        if margin_issue.get('suspected'):
            has_issues = True
            print("🚨 PROBLEMA: Colapso de márgenes detectado")
            print(f"   • Gap: {margin_issue['gap_px']:.1f}px")
            print(f"   • Primer hijo: {margin_issue['child_tag']} con margin-top: {margin_issue['child_margin_top']}px")
            print(f"   • Main padding-top: {margin_issue['main_padding_top']}px")
            print("🎯 SOLUCIÓN: Añadir a tu CSS:")
            print("   .main-wrapper { padding-top: 1px; }")
            print("   o border-top: 1px solid transparent;")
            print("   o overflow: auto;")

        if logo_issue:
            has_issues = True
            print(f"🚨 PROBLEMA: {len(logo_issue)} logo(s) sobredimensionado(s)")
            for logo in logo_issue:
                print(f"   • Logo: '{logo['alt']}' - Altura: {logo['computed_height']}px")
                if logo.get('src'):
                    print(f"     Archivo: {logo['src']}")
            print("🎯 SOLUCIÓN: Añadir a tu CSS:")
            print("   .navbar-brand img { max-height: 40px; height: auto; }")

        if bootstrap_detected:
            print("ℹ️  Bootstrap detectado en esta página")

        if not has_issues:
            print("✅ No se detectaron problemas visuales")

        return {
            'margin_issue': margin_issue.get('suspected', False),
            'logo_issue': bool(logo_issue),
            'bootstrap': bootstrap_detected
        }

    finally:
        driver.quit()

# --------------- Main ---------------
def main():
    parser = argparse.ArgumentParser(description='Tester visual automático para Budsi')
    parser.add_argument('--base', default=DEFAULT_BASE, help='URL base del sitio')
    parser.add_argument('--max-pages', type=int, default=MAX_PAGES_DEFAULT, help='Máximo de páginas a analizar')
    parser.add_argument('--depth', type=int, default=CRAWL_DEPTH_DEFAULT, help='Profundidad del crawler')
    
    args = parser.parse_args()

    print("🚀 Iniciando tester visual automático...")
    print("📡 Buscando páginas...")
    
    pages = crawl_links(args.base, args.max_pages, args.depth)
    
    if not pages:
        print("❌ No se encontraron páginas. Verifica que el servidor esté corriendo.")
        return

    print(f"\n🎯 Analizando {len(pages)} páginas:")
    for page in pages:
        print(f"   • {page}")

    summary = {
        'total_pages': len(pages),
        'pages_with_margin_issues': 0,
        'pages_with_logo_issues': 0,
        'pages_with_bootstrap': 0
    }

    print(f"\n{'='*60}")
    print("INICIANDO ANÁLISIS DETALLADO")
    print(f"{'='*60}")

    for page_url in pages:
        page_result = analyze_page(page_url)
        
        # Actualizar summary
        if page_result['margin_issue']:
            summary['pages_with_margin_issues'] += 1
        if page_result['logo_issue']:
            summary['pages_with_logo_issues'] += 1
        if page_result['bootstrap']:
            summary['pages_with_bootstrap'] += 1

        print(f"{'='*60}")

    print(f"\n📊 RESUMEN FINAL:")
    print(f"   • Total páginas analizadas: {summary['total_pages']}")
    print(f"   • Páginas con colapso de márgenes: {summary['pages_with_margin_issues']}")
    print(f"   • Páginas con logos problemáticos: {summary['pages_with_logo_issues']}")
    print(f"   • Páginas con Bootstrap: {summary['pages_with_bootstrap']}")

    if summary['pages_with_margin_issues'] > 0:
        print(f"\n💡 RECOMENDACIÓN PRINCIPAL:")
        print("   Añade esta regla CSS para solucionar el colapso de márgenes:")
        print("   .main-wrapper { padding-top: 1px; }")

    if summary['pages_with_logo_issues'] > 0:
        print(f"\n💡 RECOMENDACIÓN PRINCIPAL:")  
        print("   Añade esta regla CSS para normalizar logos:")
        print("   .navbar-brand img { max-height: 40px; height: auto; }")

if __name__ == '__main__':
    main()