import asyncio
import sys
import os
import io
from datetime import datetime
import re

# Forcer l'encodage UTF-8 pour la sortie console sous Windows
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.browser import BrowserManager
from scraper.pipeline import DataPipeline
from playwright.async_api import async_playwright


async def scrape_emploi_ma(pipeline, browser_manager, page):
    """Scraper pour Emploi.ma - Site principal"""
    try:
        print("🔍 Scraping Emploi.ma...")
        await page.goto("https://www.emploi.ma/recherche-jobs-maroc", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)  # Attendre le chargement JS
        
        # Try multiple selector strategies
        selectors = [
            '.job-description-wrapper',
            '.job-list li',
            'article.job',
            '.search-results .job',
            '[class*="job"][class*="card"]',
            '.liste-offres li',
            'div[class*="offre"]'
        ]
        
        job_cards = []
        for selector in selectors:
            job_cards = await page.query_selector_all(selector)
            if len(job_cards) > 0:
                print(f"   Trouvé {len(job_cards)} éléments avec le sélecteur: {selector}")
                break
        
        if len(job_cards) == 0:
            print(f"   ⚠️ Aucun élément trouvé sur Emploi.ma avec les sélecteurs standards")
            # Try to get all links as fallback
            all_links = await page.query_selector_all('a[href*="offre"], a[href*="job"]')
            print(f"   Trouvé {len(all_links)} liens d'offres en fallback")
            job_cards = all_links[:15]
        
        for card in job_cards[:15]:
            try:
                # Try multiple title selectors
                title = await card.query_selector('h5, h3, h2, .job-title, a[title], span[title]')
                if not title:
                    # If card is a link itself, try to get title from it
                    title_attr = await card.get_attribute('title')
                    if title_attr:
                        title_text = title_attr
                    else:
                        continue
                else:
                    title_text = await title.inner_text()
                
                company = await card.query_selector('.company-name, .company, span.text-muted, .entreprise')
                location = await card.query_selector('.job-location, .location, .ville')
                link = await card.query_selector('a[href*="job"], a[href*="offre"]')
                
                # If card itself is a link
                if not link:
                    tag_name = await card.evaluate('el => el.tagName')
                    if tag_name == 'A':
                        link = card
                
                if not link:
                    continue
                
                href = await link.get_attribute('href')
                if not href:
                    continue
                    
                full_url = href if href.startswith('http') else f"https://www.emploi.ma{href}"
                
                job_data = {
                    'title': title_text.strip(),
                    'company': (await company.inner_text()).strip() if company else 'Non spécifié',
                    'location': (await location.inner_text()).strip() if location else 'Maroc',
                    'url': full_url,
                    'description': f"Offre: {title_text.strip()}",
                    'source': 'emploi.ma',
                    'date_posted': datetime.utcnow()
                }
                pipeline.save_job(job_data)
                print(f"   ✅ Ajouté: {title_text.strip()}")
            except Exception as e:
                print(f"   ⚠️ Erreur extraction Emploi.ma: {e}")
                
    except Exception as e:
        print(f"❌ Erreur Emploi.ma: {e}")


async def scrape_rekrute(pipeline, browser_manager, page):
    """Scraper pour Rekrute.com - Alternative fiable"""
    try:
        print("🔍 Scraping Rekrute.com...")
        await page.goto("https://www.rekrute.com/offres.html", timeout=60000, wait_until="load")
        await asyncio.sleep(3)
        
        job_cards = await page.query_selector_all('.post-id, article, .job-item')
        print(f"   Trouvé {len(job_cards)} offres sur Rekrute")
        
        for card in job_cards[:15]:
            try:
                title = await card.query_selector('h2, h3, .titreJob, a.titreJob')
                company = await card.query_selector('.company, .entreprise, .recruiter, .recruteurName, span.text-muted, .company-name, .employerName')
                location = await card.query_selector('.location, .ville')
                link = await card.query_selector('a[href*="offre"]')
                
                if title and link:
                    title_text = await title.inner_text()
                    href = await link.get_attribute('href')
                    full_url = href if href.startswith('http') else f"https://www.rekrute.com{href}"
                    
                    # Extraire le nom de l'entreprise
                    company_name = 'Entreprise'
                    if company:
                        company_text = await company.inner_text()
                        company_name = company_text.strip()
                    else:
                        # Essayer d'extraire depuis le HTML de la carte
                        html_content = await card.inner_html()
                        # Chercher "recrutement-" suivi du nom d'entreprise
                        match = re.search(r'recrutement-([a-zA-Z0-9\s-]+?)-[a-z]+-\d+\.html', html_content, re.IGNORECASE)
                        if match:
                            # Nettoyer le nom (remplacer tirets par espaces, capitaliser)
                            company_name = match.group(1).replace('-', ' ').title().strip()
                    
                    job_data = {
                        'title': title_text.strip(),
                        'company': company_name,
                        'location': (await location.inner_text()).strip() if location else 'Maroc',
                        'url': full_url,
                        'description': f"Offre: {title_text.strip()}",
                        'source': 'rekrute.com',
                        'date_posted': datetime.utcnow()
                    }
                    pipeline.save_job(job_data)
                    print(f"   ✅ Ajouté: {title_text.strip()}")
            except Exception as e:
                print(f"   ⚠️ Erreur extraction Rekrute: {e}")
                
    except Exception as e:
        print(f"❌ Erreur Rekrute.com: {e}")


async def scrape_marocannonces(pipeline, browser_manager, page):
    """Scraper pour Marocannonces.com - Section emploi"""
    try:
        print("🔍 Scraping Marocannonces.com...")
        await page.goto("https://www.marocannonces.com/maroc/offres-emploi-b292.html", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Try multiple selector strategies
        selectors = [
            '.listing-card',
            '.ad-item',
            'article',
            '.annonce',
            'div[class*="listing"]',
            'li.item',
            '.items-list li'
        ]
        
        job_cards = []
        for selector in selectors:
            job_cards = await page.query_selector_all(selector)
            if len(job_cards) > 0:
                print(f"   Trouvé {len(job_cards)} annonces avec le sélecteur: {selector}")
                break
        
        if len(job_cards) == 0:
            print(f"   ⚠️ Aucune annonce trouvée sur Marocannonces avec les sélecteurs standards")
            # Try to get all links as fallback
            all_links = await page.query_selector_all('a[href*="emploi"], a[href*="offre"]')
            print(f"   Trouvé {len(all_links)} liens d'emploi en fallback")
            job_cards = all_links[:15]
        
        for card in job_cards[:15]:
            try:
                title = await card.query_selector('h2, h3, .title, a.title, .ad-title')
                if not title:
                    # If card is a link itself, try to get title from it
                    title_attr = await card.get_attribute('title')
                    if title_attr:
                        title_text = title_attr
                    else:
                        continue
                else:
                    title_text = await title.inner_text()
                
                location = await card.query_selector('.location, .city, .ville')
                link = await card.query_selector('a[href*="emploi"], a[href*="offre"]')
                
                # If card itself is a link
                if not link:
                    tag_name = await card.evaluate('el => el.tagName')
                    if tag_name == 'A':
                        link = card
                
                if not link:
                    continue
                
                href = await link.get_attribute('href')
                if not href:
                    continue
                    
                # Robust URL construction
                if href.startswith('http'):
                    full_url = href
                else:
                    # Clean leading slash to avoid double slash
                    clean_href = href.lstrip('/')
                    full_url = f"https://www.marocannonces.com/{clean_href}"
                
                job_data = {
                    'title': title_text.strip(),
                    'company': 'Particulier/Entreprise',
                    'location': (await location.inner_text()).strip() if location else 'Maroc',
                    'url': full_url,
                    'description': f"Annonce: {title_text.strip()}",
                    'source': 'marocannonces.com',
                    'date_posted': datetime.utcnow()
                }
                pipeline.save_job(job_data)
                print(f"   ✅ Ajouté: {title_text.strip()} ({full_url})")
            except Exception as e:
                print(f"   ⚠️ Erreur extraction Marocannonces: {e}")
                
    except Exception as e:
        print(f"❌ Erreur Marocannonces.com: {e}")


async def scrape_indeed_morocco(pipeline, browser_manager, page):
    """Scraper pour Indeed Maroc"""
    try:
        print("🔍 Scraping Indeed.com (Maroc)...")
        await page.goto("https://ma.indeed.com/jobs?q=&l=Maroc", timeout=60000, wait_until="load")
        await asyncio.sleep(4)
        
        # Indeed a une structure spécifique
        job_cards = await page.query_selector_all('.job_seen_beacon, .jobsearch-SerpJobCard, .slider_item')
        print(f"   Trouvé {len(job_cards)} offres sur Indeed")
        
        for card in job_cards[:15]:
            try:
                # Extract job key from data attribute (most reliable)
                job_key = await card.get_attribute('data-jk')
                
                # Method 2: id attribute (often contains job key)
                if not job_key:
                    card_id = await card.get_attribute('id')
                    if card_id and 'job_' in card_id:
                        # Extract from patterns like "job_abc123" or "jobsearch-SerpJobCard-abc123"
                        job_key = card_id.replace('job_', '').replace('jobsearch-SerpJobCard-', '')
                
                # Method 3: Parse from link href or data-jk
                if not job_key:
                    link = await card.query_selector('a.jcs-JobTitle, h2 a, a[href*="jk="], a[data-jk]')
                    if link:
                        # Try data-jk on link first
                        job_key = await link.get_attribute('data-jk')
                        
                        # Then try href
                        if not job_key:
                            href = await link.get_attribute('href')
                            if href and 'jk=' in href:
                                jk_match = re.search(r'jk=([a-f0-9]+)', href)
                                if jk_match:
                                    job_key = jk_match.group(1)
                
                if not job_key:
                    print(f"   ⚠️ Indeed: Pas de job key trouvé pour une carte")
                    continue
                
                # Build clean URL using job key
                full_url = f"https://ma.indeed.com/viewjob?jk={job_key}"
                
                # Extract job details
                title = await card.query_selector('h2 span[title], .jobTitle span[title], h2 span, .jobTitle')
                company = await card.query_selector('.companyName')
                location = await card.query_selector('.companyLocation')
                
                if not title:
                    print(f"   ⚠️ Indeed: Pas de titre trouvé pour job {job_key}")
                    continue
                
                # Extraire le texte du titre
                title_text = await title.get_attribute('title')
                if not title_text:
                    title_text = await title.inner_text()
                
                job_data = {
                    'title': title_text.strip(),
                    'company': (await company.inner_text()).strip() if company else 'Non spécifié',
                    'location': (await location.inner_text()).strip() if location else 'Maroc',
                    'url': full_url,
                    'description': f"Offre: {title_text.strip()}",
                    'source': 'indeed.com',
                    'date_posted': datetime.utcnow()
                }
                pipeline.save_job(job_data)
                print(f"   ✅ Ajouté: {title_text.strip()}")
            except Exception as e:
                print(f"   ⚠️ Erreur extraction Indeed: {e}")
                
    except Exception as e:
        print(f"❌ Erreur Indeed.com: {e}")


async def scrape_bayt(pipeline, browser_manager, page):
    """Scraper pour Bayt.com - Section Maroc"""
    try:
        print("🔍 Scraping Bayt.com...")
        await page.goto("https://www.bayt.com/fr/morocco/jobs/", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Selecteurs Bayt
        job_cards = await page.query_selector_all('li.has-pointer-d, .t-regular-job-card')
        print(f"   Trouvé {len(job_cards)} offres sur Bayt")
        
        for card in job_cards[:15]:
            try:
                title = await card.query_selector('h2.jb-title, h2.m0')
                company = await card.query_selector('.jb-company, .company-name')
                location = await card.query_selector('.jb-loc, .country-name')
                link = await card.query_selector('a[href*="/job/"], h2 a')
                
                if title and link:
                    title_text = await title.inner_text()
                    href = await link.get_attribute('href')
                    full_url = href if href.startswith('http') else f"https://www.bayt.com{href}"
                    
                    job_data = {
                        'title': title_text.strip(),
                        'company': (await company.inner_text()).strip() if company else 'Non spécifié',
                        'location': (await location.inner_text()).strip() if location else 'Maroc',
                        'url': full_url,
                        'description': f"Offre Bayt: {title_text.strip()}",
                        'source': 'bayt.com',
                        'date_posted': datetime.utcnow()
                    }
                    pipeline.save_job(job_data)
                    print(f"   ✅ Ajouté: {title_text.strip()}")
            except Exception as e:
                print(f"   ⚠️ Erreur extraction Bayt: {e}")
                
    except Exception as e:
        print(f"❌ Erreur Bayt.com: {e}")


async def scrape_tanqeeb(pipeline, browser_manager, page):
    """Scraper pour Tanqeeb - Section Maroc"""
    try:
        print("🔍 Scraping Tanqeeb.com...")
        await page.goto("https://morocco.tanqeeb.com/ar/jobs/search?country=50", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Selecteurs Tanqeeb vérifiés via inspection browser
        # Le lien est le conteneur principal
        job_cards = await page.query_selector_all('a.card-list-item')
        print(f"   Trouvé {len(job_cards)} offres sur Tanqeeb")
        
        for card in job_cards[:15]:
            try:
                # Le lien est l'élément carte lui-même
                href = await card.get_attribute('href')
                if not href:
                    continue
                    
                full_url = href if href.startswith('http') else f"https://morocco.tanqeeb.com{href}"
                
                # Titre dans h2
                title = await card.query_selector('h2')
                
                # Metadata (Compagnie, Location) sont dans des spans avec icones
                # On récupère tout le texte de la carte pour parsing simplifié si sélecteurs précis échouent
                all_text = await card.inner_text()
                
                # Tentative d'extraction précise
                company_el = await card.query_selector('i.fa-building')
                location_el = await card.query_selector('i.fa-map-marker-alt, i.fa-map-marker')
                
                if title:
                    title_text = await title.inner_text()
                    
                    # Extraction company via parent de l'icone
                    company_name = "Non spécifié"
                    if company_el:
                        # Remonter au parent (span) pour avoir le texte
                        company_span = await company_el.evaluate_handle('el => el.parentElement')
                        company_name = (await company_span.inner_text()).strip()
                    
                    # Extraction location via parent de l'icone
                    location_name = "Maroc"
                    if location_el:
                         # Remonter au parent (span) pour avoir le texte
                        loc_span = await location_el.evaluate_handle('el => el.parentElement')
                        location_name = (await loc_span.inner_text()).strip()
                    
                    job_data = {
                        'title': title_text.strip(),
                        'company': company_name,
                        'location': location_name,
                        'url': full_url,
                        'description': f"Offre Tanqeeb: {title_text.strip()}",
                        'source': 'tanqeeb.com',
                        'date_posted': datetime.utcnow()
                    }
                    pipeline.save_job(job_data)
                    print(f"   ✅ Ajouté: {title_text.strip()}")
            except Exception as e:
                print(f"   ⚠️ Erreur extraction Tanqeeb: {e}")
                
    except Exception as e:
        print(f"❌ Erreur Tanqeeb.com: {e}")


async def main():
    pipeline = DataPipeline()
    manager = BrowserManager(headless=True)
    
    print("=" * 60)
    print("🚀 DÉMARRAGE DU SCRAPING MULTI-SITES (Version Optimisée)")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser, context, page = await manager.get_context_and_page(p)
        
        try:
            # Scraper les sites les plus fiables en premier
            await scrape_emploi_ma(pipeline, manager, page)
            await scrape_rekrute(pipeline, manager, page)
            await scrape_marocannonces(pipeline, manager, page)
            await scrape_indeed_morocco(pipeline, manager, page)
            await scrape_bayt(pipeline, manager, page)
            await scrape_tanqeeb(pipeline, manager, page)
            
            pipeline.log_run('success')
            print("=" * 60)
            print(f"✅ SCRAPING TERMINÉ - {pipeline.new_jobs_count} nouveaux jobs ajoutés")
            print("=" * 60)
            
        except Exception as e:
            pipeline.log_run('failed', str(e))
            print(f"❌ Échec du scraping: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
