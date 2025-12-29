import asyncio
import sys
import os
import io
import re
from datetime import datetime, timedelta
import locale

# Forcer l'encodage UTF-8 pour la sortie console sous Windows
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.browser import BrowserManager
from scraper.pipeline import DataPipeline
from playwright.async_api import async_playwright

# Configuration Locale pour les dates (fr_FR)
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR')
    except:
        pass # Fallback to default if fr_FR not available

def parse_relative_date(date_str, fallback_date=None):
    """
    Parse les dates relatives ou absolues
    Ex: "Il y a 2 jours", "12/05/2024", "Hier", "Aujourd'hui", "25 Déc. 2024"
    """
    if not date_str:
        return fallback_date
    
    date_str = date_str.lower().strip()
    now = datetime.utcnow()
    
    try:
        # Nettoyage préalable spécifique
        date_str = re.sub(r'publiée sur rekrute le|publié le|date :|du', '', date_str, flags=re.IGNORECASE).strip()
        # Enlever les indicateurs de temps (ex: "Aujourd'hui 14:30")
        date_str = re.split(r'\s+\d{1,2}:\d{2}', date_str)[0].strip()

        # Handle ISO format
        if 't' in date_str and len(date_str) > 10:
            try:
                iso_date = date_str.split('t')[0]
                return datetime.strptime(iso_date, '%Y-%m-%d')
            except:
                pass

        # MAPPING MOIS FRANCAIS (Avec abréviations et accents)
        french_months = {
            'janvier': '01', 'janv.': '01', 'janv': '01', 'jan': '01',
            'février': '02', 'fevrier': '02', 'fév.': '02', 'fev.': '02', 'fév': '02', 'fev': '02', 'feb': '02',
            'mars': '03', 'mar.': '03', 'mar': '03',
            'avril': '04', 'avr.': '04', 'avr': '04', 'apr': '04',
            'mai': '05', 'may': '05',
            'juin': '06', 'jun': '06',
            'juillet': '07', 'juil.': '07', 'juil': '07', 'jul': '07',
            'août': '08', 'aout': '08', 'aug': '08',
            'septembre': '09', 'sept.': '09', 'sept': '09', 'sep': '09',
            'octobre': '10', 'oct.': '10', 'oct': '10',
            'novembre': '11', 'nov.': '11', 'nov': '11',
            'décembre': '12', 'decembre': '12', 'déc.': '12', 'dec.': '12', 'déc': '12', 'dec': '12'
        }
        
        # Cas relatifs - Priorité à "Hier/Avant-hier" pour ne pas matcher avec "heures" si mal placé
        if any(x in date_str for x in ['avant-hier', 'before yesterday']):
             return now - timedelta(days=2)

        if any(x in date_str for x in ['hier', 'yesterday']):
            return now - timedelta(days=1)

        # "Aujourd'hui", "Maintenant", ou temps très court (minutes, heures)
        # Attention: 'h' seul peut matcher 'hier', donc on utilise regex pour les heures/minutes
        if any(x in date_str for x in ['aujourd', 'today', 'maintenant', 'now']):
            return now
            
        # Regex pour "Il y a X heures" ou "5h" ou "12:30" (implique aujourd'hui)
        if re.search(r'\d+\s*(h|heure|hour|minute|min|sec)', date_str) or re.search(r'\d{1,2}:\d{2}', date_str):
             return now

            
        # "Il y a X jours" / "X days ago"
        match_days = re.search(r'il y a (\d+) jour', date_str) or re.search(r'(\d+) jour', date_str) or re.search(r'(\d+) day', date_str)
        if match_days:
            return now - timedelta(days=int(match_days.group(1)))
            
        match_months = re.search(r'il y a (\d+) mois', date_str) or re.search(r'(\d+) mois', date_str)
        if match_months:
            return now - timedelta(days=int(match_months.group(1)) * 30)

        # Essai de remplacement des mois APRES les tests relatifs
        lower_str = date_str
        for fr, digit in french_months.items():
            if fr in lower_str:
                # Ex: "12 déc. 2024" -> "12 12 2024"
                lower_str = lower_str.replace(fr, digit)
                
                # Nettoyage pour standardiser
                # Garder chiffres et espaces
                clean = re.sub(r'[^\d\s]', ' ', lower_str)
                clean = re.sub(r'\s+', ' ', clean).strip()
                
                try:
                    return datetime.strptime(clean, '%d %m %Y')
                except:
                    pass
                try:
                    # Cas sans année explicite ? (Rare pour historique, on assume année courante si absent?)
                    # Pour l'instant on demande l'année
                    pass
                except:
                    pass
                # On continue si échec, peut-être un autre mois matchera mieux (peu probable) ou format regex plus bas
                break 

        # Formats courants
        formats = [
            '%d/%m/%Y', '%d.%m.%Y', '%d-%m-%Y', 
            '%Y-%m-%d', '%d %B %Y', '%d %b %Y',
            '%d %m %Y', '%d-%m-%y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        # Regex générique pour trouver dates (dd/mm/yyyy)
        match_date = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})', date_str)
        if match_date:
            day, month, year = match_date.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except:
                pass

        # Si toujours rien, log mais ne pas fail hard si fallback existe pas
        if fallback_date:
            # print(f"⚠️ [DATE_FAIL] Date fallback: '{date_str}' -> {fallback_date.strftime('%d/%m/%Y')}")
            return fallback_date
        else:
            # print(f"⚠️ [DATE_FAIL] Date non reconnue: '{date_str}'")
            return None
        
    except Exception as e:
        if fallback_date:
            return fallback_date
        return None


# Liste des principales villes et régions du Maroc
MOROCCAN_CITIES = {
    # Grandes villes
    'casablanca', 'rabat', 'fes', 'fès', 'marrakech', 'tanger', 'agadir', 'meknes', 'meknès',
    'oujda', 'kenitra', 'kénitra', 'tetouan', 'tétouan', 'safi', 'temara', 'mohammedia',
    'khouribga', 'beni mellal', 'béni mellal', 'el jadida', 'nador', 'taza', 'settat',
    
    # Villes moyennes
    'laayoune', 'laâyoune', 'khemisset', 'khmisset', 'berkane', 'taourirt', 'ksar el kebir',
    'larache', 'guelmim', 'berrechid', 'errachidia', 'ouarzazate', 'tiznit', 'tan-tan',
    'essaouira', 'dakhla', 'sidi kacem', 'sidi slimane', 'youssoufia', 'sefrou',
    
    # Quartiers/Zones de Casablanca
    'ain chock', 'ain sebaa', 'anfa', 'hay hassani', 'hay mohammadi', 'sidi maarouf',
    'sidi moumen', 'maarif', 'gauthier', 'bourgogne', 'californie', 'oulfa',
    'derb sultan', 'roches noires', 'ain diab', 'bouskoura', 'nouaceur',
    
    # Quartiers/Zones de Rabat
    'agdal', 'hay riad', 'souissi', 'hassan', 'ocean', 'aviation', 'akkari',
    
    # Régions (pour fallback)
    'grand casablanca', 'casablanca settat', 'rabat sale kenitra', 'rabat salé kénitra',
    'fes meknes', 'fès meknès', 'marrakech safi', 'tanger tetouan', 'tanger tétouan',
    'oriental', 'souss massa', 'draa tafilalet', 'beni mellal khenifra',
    
    # Variations orthographiques
    'el kelaa', 'el kelaa des sraghna', 'sidi bennour', 'azrou', 'ifrane', 'midelt',
    'sale', 'salé', 'jadida', 'mohammadia', 'benslimane', 'mediouna', 'nouasseur'
}

def clean_location(loc_str):
    """Nettoie et extrait intelligemment le nom de la ville"""
    if not loc_str: 
        return "Maroc"
    
    original = loc_str
    loc_str = loc_str.lower().strip()
    
    # Enlever les préfixes communs
    loc_str = re.sub(r'région\s+de\s*:?\s*', '', loc_str, flags=re.IGNORECASE)
    loc_str = re.sub(r'ville\s+de\s*:?\s*', '', loc_str, flags=re.IGNORECASE)
    loc_str = re.sub(r'province\s+de\s*:?\s*', '', loc_str, flags=re.IGNORECASE)
    
    # Enlever " (Maroc)" à la fin
    loc_str = re.sub(r'\s*\(maroc\)\s*$', '', loc_str, flags=re.IGNORECASE)
    
    # Enlever "tout le maroc", variations génériques
    if any(x in loc_str for x in ['tout le maroc', 'tout maroc', 'المغرب', 'morocco', 'maroc maroc']):
        return "Maroc"
    
    # Nettoyer les caractères spéciaux
    loc_str = loc_str.replace('-', ' ').replace(':', '').replace('/', ' ').strip()
    
    # Si vide après nettoyage
    if not loc_str or len(loc_str) < 2:
        return "Maroc"
    
    # Normaliser les variations orthographiques courantes
    replacements = {
        'mohammédia': 'mohammedia',
        'tétouan': 'tetouan',
        'kénitra': 'kenitra',
        'témara': 'temara',
        'béni mellal': 'beni mellal',
        'el kelaa': 'el kelaa des sraghna',
        'laâyoune': 'laayoune',
    }
    
    for old, new in replacements.items():
        if old in loc_str:
            loc_str = loc_str.replace(old, new)
    
    # Chercher une ville connue dans la chaîne
    loc_lower = loc_str.lower()
    
    # Essayer de matcher une ville exacte d'abord
    for city in MOROCCAN_CITIES:
        if city == loc_lower:
            return city.title()
    
    # Essayer de trouver une ville dans la chaîne (pour "Casablanca / Sidi Maarouf" -> "Casablanca")
    for city in sorted(MOROCCAN_CITIES, key=len, reverse=True):  # Plus longues d'abord
        if city in loc_lower:
            # Vérifier que c'est bien un mot complet (pas juste une sous-chaîne)
            pattern = r'\b' + re.escape(city) + r'\b'
            if re.search(pattern, loc_lower):
                return city.title()
    
    # Si aucune ville trouvée mais la chaîne semble être une ville (pas trop longue)
    # On capitalise et retourne
    if len(loc_str) < 30 and not any(word in loc_lower for word in ['maroc', 'morocco', 'tout', 'national']):
        # Capitaliser proprement
        return ' '.join(word.capitalize() for word in loc_str.split())
    
    # Fallback final
    return "Maroc"



def estimate_date_from_page(page_number, days_per_page=1.5):
    """
    Estime la date d'une offre basée sur le numéro de page
    Hypothèse : les offres plus récentes sont sur les premières pages
    
    Args:
        page_number: Numéro de la page actuelle
        days_per_page: Nombre de jours estimés par page (défaut: 1.5)
    
    Returns:
        datetime estimé
    """
    days_offset = (page_number - 1) * days_per_page
    return datetime.utcnow() - timedelta(days=days_offset)


async def scrape_emploi_ma_history(pipeline, browser_manager, page, start_date):
    """Scraper Historique pour Emploi.ma avec pagination profonde"""
    # --- EMPLOI.MA ---
    print(f" Début scraping historique Emploi.ma (Cible: {start_date.strftime('%d/%m/%Y')})")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        stop_scraping = False
        
        for page_num in range(1, 501): # Augmenté à 500 pages pour historique profond
            if stop_scraping:
                break
                
            print(f"   📄 Traitement page {page_num}...")
            url = f"https://www.emploi.ma/recherche-jobs-maroc?page={page_num}"
            try:
                await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                await asyncio.sleep(2) # Slightly faster
                
                job_cards = await page.query_selector_all('.card-job-detail')
                
                if not job_cards:
                    print("   ⚠️ Plus d'offres trouvées (sélecteur .card-job-detail), arrêt.")
                    break

            except Exception as e:
                print(f"   ⚠️ Erreur page {page_num}: {e}")
                continue
                
            page_oldest_date = datetime.utcnow()
            
            for card in job_cards:
                try:
                    # DATE
                    date_el = await card.query_selector('time')
                    if date_el:
                        date_text = await date_el.get_attribute('datetime') or await date_el.inner_text()
                    else:
                        date_text = ""
                    
                    job_date = parse_relative_date(date_text)
                    if not job_date:
                        job_date = estimate_date_from_page(page_num, days_per_page=1.5)
                    
                    page_oldest_date = min(page_oldest_date, job_date)
                    
                    # Stop si trop vieux
                    if job_date < start_date:
                        print(f"   🛑 Offre trop ancienne ({job_date.strftime('%d/%m/%Y')}), arrêt du scraping historique.")
                        stop_scraping = True
                        break
                    
                    # TITLE
                    title_el = await card.query_selector('h3 a')
                    title_text = await title_el.inner_text() if title_el else "Sans titre"
                    
                    # COMPANY
                    company_el = await card.query_selector('.card-job-company, .company-name')
                    company = await company_el.inner_text() if company_el else "Non spécifié"
                    
                    # URL
                    link_el = await card.query_selector('h3 a')
                    href = await link_el.get_attribute('href') if link_el else ""
                    full_url = href if href.startswith('http') else f"https://www.emploi.ma{href}"

                    # LOCATION (Verified Live)
                    location = "Maroc"
                    # Lis method
                    lis = await card.query_selector_all('ul li')
                    for li in lis:
                        text = await li.inner_text()
                        if "Région" in text:
                            # Structure verified: <li>Région de : <strong>City</strong></li>
                            strong = await li.query_selector('strong')
                            if strong:
                                location = await strong.inner_text()
                            else:
                                location = text.replace("Région de :", "").strip()
                            break
                    
                    location = clean_location(location)

                    # DESCRIPTION (Snippet)
                    desc_el = await card.query_selector('.card-job-description')
                    desc_text = await desc_el.inner_text() if desc_el else title_text

                    job_data = {
                        'title': title_text.strip(),
                        'company': company.strip(),
                        'location': location,
                        'url': full_url,
                        'description': desc_text.strip(), # Description réelle pour extraction mots-clés
                        'source': 'emploi.ma',
                        'date_posted': job_date
                    }
                    
                    pipeline.save_job(job_data)
                    
                except Exception as e:
                    continue
            
            print(f"   📅 Plus ancienne date sur cette page: {page_oldest_date.strftime('%d/%m/%Y')}")

async def scrape_rekrute_history(pipeline, browser_manager, page, start_date):
    """Scraper Historique pour Rekrute.com"""
    print(f"\n📚 Début scraping historique Rekrute (Cible: {start_date.strftime('%d/%m/%Y')})")
    
    current_page = 1
    max_pages = 300  # Augmenté pour scraping historique profond
    stop_scraping = False
    
    while current_page <= max_pages and not stop_scraping:
        url = f"https://www.rekrute.com/offres.html?p={current_page}&s=1&o=1" # o=1 pour trier par date
        print(f"   📄 Traitement page {current_page}...")
        
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            job_cards = await page.query_selector_all('li.post-id')
            
            if not job_cards:
                print("   ⚠️ Plus d'offres trouvées, arrêt.")
                break
                
            page_oldest_date = datetime.utcnow()
            
            for card in job_cards:
                try:
                    # DATE - Attempt multiple extraction methods
                    job_date = None
                    date_text = ""
                    
                    # Method 1: Specific span inside em.date
                    date_spans = await card.query_selector_all('em.date span')
                    if date_spans and len(date_spans) > 0:
                         # Premier span = date publication typically
                         date_text = await date_spans[0].inner_text()
                         job_date = parse_relative_date(date_text)
                    
                    # Method 2: Fallback to em.date text content
                    if not job_date:
                        sh_el = await card.query_selector('em.date')
                        if sh_el:
                            sh_text = await sh_el.inner_text()
                            sh_text = sh_text.replace("Date de publication", "").strip()
                            job_date = parse_relative_date(sh_text)

                    # Method 3: Fallback regex on full card text (risky but better than skip)
                    if not job_date:
                        card_text = await card.inner_text()
                        # Clean up common noise
                        card_text = re.sub(r'[\n\r]+', ' ', card_text)
                        # Look for date-like strings
                        match = re.search(r'\d{2}/\d{2}/\d{4}', card_text)
                        if match:
                             job_date = parse_relative_date(match.group(0))
                        else:
                             # Try parsing the whole text as a last resort relative date
                             job_date = parse_relative_date(card_text)
                    
                    # Method 4: Estimate from page number (Last Resort)
                    if not job_date:
                        # print(f"   ⚠️ Date non trouvée pour une offre page {current_page}, estimation.")
                        job_date = estimate_date_from_page(current_page, days_per_page=2)

                    page_oldest_date = min(page_oldest_date, job_date)
                    
                    if job_date < start_date:
                        # Only stop if we are SURE it's old (not estimated) OR if it's way past start date
                        # Tolerance of 30 days for estimated dates to avoid premature stop due to mix
                        if (start_date - job_date).days > 30:
                            print(f"   🛑 Offre trop ancienne ({job_date.strftime('%d/%m/%Y')}), arrêt.")
                            stop_scraping = True
                            break

                    # TITLE
                    title_el = await card.query_selector('a.titreJob')
                    title_text = await title_el.inner_text() if title_el else "Sans titre"
                    
                    # COMPANY
                    # Souvent img alt ou lien spécifique
                    company = "Rekrute Client" # Default
                    img_el = await card.query_selector('.photo img')
                    if img_el:
                        company = await img_el.get_attribute('alt')
                    
                    # URL
                    if title_el:
                         href = await title_el.get_attribute('href')
                         full_url = href if href.startswith('http') else f"https://www.rekrute.com{href}"
                    else:
                         full_url = ""

                    # LOCATION - Source: Title split (confirmed by verify)
                    location = "Maroc"
                    if "|" in title_text:
                        parts = title_text.rsplit('|', 1)
                        if len(parts) > 1:
                            location_candidate = parts[1].strip()
                            if len(location_candidate) < 30: 
                                location = location_candidate
                    
                    # Method 2: Check info li
                    # Souvent <div class="info"><ul><li>...</li></ul></div>
                    if location == "Maroc":
                         info_el = await card.query_selector('.info ul')
                         if info_el:
                             info_text = await info_el.inner_text()
                             # Look for city-like words in info lines? 
                             # Simpler: check if we have a specific tag
                             pass

                    location = clean_location(location)

                    # DESCRIPTION (Snippet pour extraction mots clés)
                    info_el = await card.query_selector('.info')
                    if info_el:
                         desc_text = await info_el.inner_text()
                    else:
                         desc_text = await card.inner_text() # Fallback

                    job_data = {
                        'title': title_text.strip(),
                        'company': company.strip() if company else "Non spécifié",
                        'location': location,
                        'url': full_url,
                        'description': desc_text.strip(), # Essential for tech extraction
                        'source': 'rekrute.com',
                        'date_posted': job_date
                    }
                    
                    pipeline.save_job(job_data)
                    
                except Exception as e:
                    continue
            
            print(f"   📅 Plus ancienne date sur cette page: {page_oldest_date.strftime('%d/%m/%Y')}")

        except Exception as e:
             print(f"   ⚠️ Erreur page {current_page}: {e}")
             continue
        
        current_page += 1

        current_page += 1

async def scrape_marocannonces_history(pipeline, browser_manager, page, start_date):
    """Scraper Historique pour Marocannonces.com"""
    print(f"\n📚 Début scraping historique Marocannonces (Cible: {start_date.strftime('%d/%m/%Y')})")
    
    current_page = 1
    max_pages = 300  # Augmenté pour historique profond
    stop_scraping = False
    
    while current_page <= max_pages and not stop_scraping:
        # Marocannonces utilise pge=X
        url = f"https://www.marocannonces.com/maroc/offres-emploi-b292.html?pge={current_page}"
        print(f"   📄 Traitement page {current_page}...")
        
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Selectors - Verified Live: ul.cars-list li (standard items)
            # Mixed content: some Lis are not jobs. Filter by those having 'h3'.
            all_lis = await page.query_selector_all('ul.cars-list li, ul.content_list li, .listing-card')
            
            if not all_lis:
                print("   ⚠️ Plus d'annonces trouvées (sélecteur ul li), arrêt.")
                break
            
            page_oldest_date = datetime.utcnow()
            
            for card in all_lis:
                try:
                    # CHECK IF REAL JOB
                    title_el = await card.query_selector('h3')
                    if not title_el:
                         continue # Not a job card
                    
                    # TITLE - Verified: <h3>Title</h3>
                    title_text = await title_el.inner_text()
                    title_text = title_text.strip()
                    if not title_text:
                        continue
                        
                    # DATE - Robust Extraction
                    job_date = None
                    
                    # Method 1: Standard em.date
                    date_el = await card.query_selector('em.date')
                    if date_el:
                         date_text = await date_el.inner_text()
                         job_date = parse_relative_date(date_text)
                    
                    # Method 2: Look for date text in the card content
                    if not job_date:
                        date_match = await card.evaluate('''(el) => {
                            const text = el.innerText;
                            // Regex for DD Month YYYY or DD/MM/YYYY
                            const match = text.match(/(\d{1,2}\s+[a-zA-Zéû]{3,9}\.?\s+\d{4})|(\d{1,2}\/\d{1,2}\/\d{4})/);
                            return match ? match[0] : null;
                        }''')
                        if date_match:
                            job_date = parse_relative_date(date_match)

                    # Method 3: Estimate
                    if not job_date:
                        job_date = estimate_date_from_page(current_page, days_per_page=2)
                    
                    page_oldest_date = min(page_oldest_date, job_date)
                    
                    if job_date < start_date:
                         # Tolerance for estimates
                        if (start_date - job_date).days > 30:
                            print(f"   🛑 Annonce trop ancienne ({job_date.strftime('%d/%m/%Y')}), arrêt.")
                            stop_scraping = True
                            break

                    # LOCATION - Verified: <span class="location">City</span>
                    location = "Maroc"
                    loc_el = await card.query_selector('.location')
                    if loc_el:
                        location = await loc_el.inner_text()
                    
                    # URL - Verified: Link is usually surrounding or inside h3
                    full_url = ""
                    link_el = await card.query_selector('h3 a') 
                    if not link_el:
                         link_el = await card.query_selector('a')
                    
                    if link_el:
                         href = await link_el.get_attribute('href')
                         if href:
                             if href.startswith('http'):
                                 full_url = href
                             else:
                                 # Marocannonces relative links
                                 clean_href = href.lstrip('/')
                                 full_url = f"https://www.marocannonces.com/{clean_href}"
                    
                    if not full_url:
                        continue

                    job_data = {
                        'title': title_text,
                        'company': "Particulier/Entreprise", # Souvent masqué
                        'location': clean_location(location),
                        'url': full_url,
                        'description': f"Annonce: {title_text}", 
                        'source': 'marocannonces.com',
                        'date_posted': job_date
                    }
                    
                    pipeline.save_job(job_data)
                
                except Exception as e:
                    continue

            print(f"   📅 Plus ancienne date sur cette page: {page_oldest_date.strftime('%d/%m/%Y')}")

        except Exception as e:
            print(f"   ⚠️ Erreur page {current_page}: {e}")
            continue
            
        current_page += 1

        current_page += 1

async def scrape_bayt_history(pipeline, browser_manager, page, start_date):
    """Scraper Historique pour Bayt.com"""
    print(f"\n📚 Début scraping historique Bayt (Cible: {start_date.strftime('%d/%m/%Y')})")
    
    current_page = 1
    max_pages = 300  # Augmenté pour historique profond
    stop_scraping = False
    
    while current_page <= max_pages and not stop_scraping:
        url = f"https://www.bayt.com/fr/morocco/jobs/?page={current_page}"
        print(f"   📄 Traitement page {current_page}...")
        
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            job_cards = await page.query_selector_all('li.has-pointer-d, .t-regular-job-card')
            
            if not job_cards:
                print("   ⚠️ Plus d'offres trouvées, arrêt.")
                break
            
            page_oldest_date = datetime.utcnow()
            
            for card in job_cards:
                try:
                    # DATE - Robust Extraction
                    job_date = None
                    
                    # Method 1: Specific data attribute
                    date_el = await card.query_selector('.jb-date span[data-automation-id="job-active-date"]')
                    if date_el:
                         date_text = await date_el.inner_text()
                         job_date = parse_relative_date(date_text)
                    
                    # Method 2: Generic date container
                    if not job_date:
                         date_el = await card.query_selector('.jb-date')
                         if date_el:
                             date_text = await date_el.inner_text()
                             job_date = parse_relative_date(date_text)

                    # Method 3: Fallback regex on card text
                    if not job_date:
                        card_text = await card.inner_text()
                        job_date = parse_relative_date(card_text)
                    
                    # Method 4: Estimate
                    if not job_date:
                        job_date = estimate_date_from_page(current_page, days_per_page=2)
                        
                    page_oldest_date = min(page_oldest_date, job_date)
                    
                    if job_date < start_date:
                        if (start_date - job_date).days > 30:
                            print(f"   🛑 Offre trop ancienne ({job_date.strftime('%d/%m/%Y')}), arrêt.")
                            stop_scraping = True
                            break

                    # TITLE
                    title_el = await card.query_selector('h2.jb-title, h2.m0, a[data-js-aid="job-title"]')
                    title_text = await title_el.inner_text() if title_el else "Sans titre"
                    
                    # COMPANY
                    # Verified: inside .job-company-location-wrapper -> a.t-bold
                    company = "Non spécifié"
                    company_el = await card.query_selector('.job-company-location-wrapper a.t-bold')
                    if not company_el:
                         company_el = await card.query_selector('.jb-company, .company-name')
                    
                    if company_el:
                        company = await company_el.inner_text()
                    
                    # URL
                    link_el = await card.query_selector('a[href*="/job/"], h2 a')
                    full_url = ""
                    if link_el:
                         href = await link_el.get_attribute('href')
                         if href:
                             full_url = href if href.startswith('http') else f"https://www.bayt.com{href}"
                    
                    if not full_url:
                        continue

                    # LOCATION
                    # Verified: .job-company-location-wrapper .t-mute span
                    location = "Maroc"
                    loc_wrapper = await card.query_selector('.job-company-location-wrapper')
                    if loc_wrapper:
                        # Often "City - Morocco"
                        loc_text = await loc_wrapper.inner_text()
                        # Clean up company name from it if needed, easier to search for span
                        spans = await loc_wrapper.query_selector_all('span')
                        if spans:
                             # First span usually city
                             location = await spans[0].inner_text()
                    else:
                        # Fallback
                        location_el = await card.query_selector('.jb-loc, .country-name')
                        if location_el:
                             location = await location_el.inner_text()
                    
                    # DESCRIPTION Snippet
                    desc_el = await card.query_selector('.jb-descr, p.t-small')
                    desc_text = await desc_el.inner_text() if desc_el else title_text

                    job_data = {
                        'title': title_text.strip(),
                        'company': company.strip(),
                        'location': clean_location(location),
                        'url': full_url,
                        'description': desc_text.strip(), 
                        'source': 'bayt.com',
                        'date_posted': job_date
                    }
                    
                    pipeline.save_job(job_data)
                
                except Exception as e:
                    continue

            print(f"   📅 Plus ancienne date sur cette page: {page_oldest_date.strftime('%d/%m/%Y')}")

        except Exception as e:
            print(f"   ⚠️ Erreur page {current_page}: {e}")
            continue
            
        current_page += 1

        current_page += 1

async def scrape_tanqeeb_history(pipeline, browser_manager, page, start_date):
    """Scraper Historique pour Tanqeeb"""
    print(f"\n📚 Début scraping historique Tanqeeb (Cible: {start_date.strftime('%d/%m/%Y')})")
    
    current_page = 1
    max_pages = 300  # Augmenté pour historique profond
    stop_scraping = False
    
    while current_page <= max_pages and not stop_scraping:
        url = f"https://morocco.tanqeeb.com/ar/jobs/search?country=50&page={current_page}"
        print(f"   📄 Traitement page {current_page}...")
        
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            job_cards = await page.query_selector_all('a.card-list-item')
            
            if not job_cards:
                print("   ⚠️ Plus d'offres trouvées, arrêt.")
                break
            
            page_oldest_date = datetime.utcnow()
            
            for card in job_cards:
                try:
                    # DATE
                    # Souvent "il y a X jours" (arabe ou français)
                    card_text = await card.inner_text()
                    # Clean up newlines for regex
                    card_text_clean = " ".join(card_text.split())
                    
                    job_date = parse_relative_date(card_text_clean)
                    
                    if not job_date:
                         # Try finding specific time tags if any
                         time_el = await card.query_selector('time')
                         if time_el:
                             dt = await time_el.get_attribute('datetime')
                             if dt:
                                 job_date = parse_relative_date(dt)

                    if not job_date:
                        job_date = estimate_date_from_page(current_page, days_per_page=2)
                    
                    page_oldest_date = min(page_oldest_date, job_date)
                    
                    if job_date < start_date:
                        # Tanqeeb mélange parfois sponsorisé récent et organique vieux. On continue un peu.
                        if job_date < start_date - timedelta(days=60): # Marge augmentée à 60 jours
                             print(f"   🛑 Offre trop ancienne ({job_date.strftime('%d/%m/%Y')}), arrêt.")
                             stop_scraping = True
                             break

                    # TITRE
                    title_el = await card.query_selector('h2')
                    title_text = await title_el.inner_text() if title_el else "Sans titre"
                    
                    # LINK (Card `is` link)
                    href = await card.get_attribute('href')
                    full_url = href if href.startswith('http') else f"https://morocco.tanqeeb.com{href}"
                    
                    # COMPANY & LOCATION
                    # Basé sur icones
                    company = "Tanqeeb Recruteur"
                    c_el = await card.query_selector('i.fa-building')
                    if c_el:
                         # Parent
                         c_span = await c_el.evaluate_handle('el => el.parentElement')
                         company = (await c_span.inner_text()).strip()
                         
                    location = "Maroc"
                    l_el = await card.query_selector('i.fa-map-marker-alt, i.fa-map-marker')
                    if l_el:
                         l_span = await l_el.evaluate_handle('el => el.parentElement')
                         location = (await l_span.inner_text()).strip()

                    job_data = {
                        'title': title_text.strip(),
                        'company': company.strip(),
                        'location': clean_location(location),
                        'url': full_url,
                        'description': f"Offre Tanqeeb: {title_text.strip()}",
                        'source': 'tanqeeb.com',
                        'date_posted': job_date
                    }
                    pipeline.save_job(job_data)
                    
                except Exception as e:
                    continue
                    
            print(f"   📅 Plus ancienne date sur cette page: {page_oldest_date.strftime('%d/%m/%Y')}")

        except Exception as e:
            print(f"   ⚠️ Erreur page {current_page}: {e}")
            continue
        
        current_page += 1

async def scrape_indeed_history(pipeline, browser_manager, page, start_date):
    """Scraper Historique pour Indeed (Attention aux blocages)"""
    print(f"\n📚 Début scraping historique Indeed (Cible: {start_date.strftime('%d/%m/%Y')})")
    
    # Pagination Indeed: start=0, 10, 20...
    current_start = 0
    max_start = 3000  # ~300 pages (10 résultats par page) - Augmenté pour historique profond
    stop_scraping = False
    
    while current_start <= max_start and not stop_scraping:
        url = f"https://ma.indeed.com/jobs?q=&l=Maroc&start={current_start}"
        print(f"   📄 Traitement résultats à partir de {current_start}...")
        
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(4) # Délai plus long pour Indeed
            
            job_cards = await page.query_selector_all('.job_seen_beacon, .jobsearch-SerpJobCard')
            
            if not job_cards:
                print("   ⚠️ Plus d'offres trouvées ou CAPTCHA, arrêt.")
                break
            
            page_oldest_date = datetime.utcnow()
            
            for card in job_cards:
                try:
                    # DATE - element .date
                    date_el = await card.query_selector('.date')
                    if date_el:
                        # "Posted 2 days ago" ou "Publié il y a 30+ jours"
                        date_text = await date_el.inner_text()
                        # Nettoyer "Posted" "Publié"
                        date_text = date_text.replace("Posted", "").replace("Publié", "").strip()
                    else:
                        date_text = ""
                        
                    job_date = parse_relative_date(date_text)
                    if not job_date:
                        # Estimation basée sur l'offset Indeed (10 résultats par page)
                        page_num = (current_start // 10) + 1
                        job_date = estimate_date_from_page(page_num, days_per_page=3)
                    
                    page_oldest_date = min(page_oldest_date, job_date)
                    
                    if job_date < start_date:
                        # Indeed met souvent "30+ days ago", ce qui est vague. On continue quand même un peu.
                        if "30+" not in date_text:
                             print(f"   🛑 Offre trop ancienne ({job_date.strftime('%d/%m/%Y')}), arrêt.")
                             stop_scraping = True
                             break
                    
                    # DETAILS
                    # Get job key
                    job_key = await card.get_attribute('data-jk') or ""
                    
                    title_el = await card.query_selector('.jobTitle span')
                    title_text = await title_el.inner_text() if title_el else "Sans titre"
                    
                    company_el = await card.query_selector('.companyName')
                    company = await company_el.inner_text() if company_el else "Non spécifié"
                    
                    location_el = await card.query_selector('.companyLocation')
                    location = await location_el.inner_text() if location_el else "Maroc"
                    
                    full_url = f"https://ma.indeed.com/viewjob?jk={job_key}" if job_key else ""
                    
                    job_data = {
                        'title': title_text.strip(),
                        'company': company.strip(),
                        'location': clean_location(location),
                        'url': full_url,
                        'description': f"Offre Indeed: {title_text.strip()}",
                        'source': 'indeed.com',
                        'date_posted': job_date
                    }
                    
                    if full_url: # Only save if valid
                        pipeline.save_job(job_data)
                        
                except Exception as e:
                     continue
            
            print(f"   📅 Plus ancienne date estimee sur cette page: {page_oldest_date.strftime('%d/%m/%Y')}")
            
        except Exception as e:
            print(f"   ⚠️ Erreur Indeed: {e}")
            break
            
        current_start += 10 # Page suivante

async def main():
    pipeline = DataPipeline()
    manager = BrowserManager(headless=True)
    
    # Date cible: 1er Janvier 2024
    target_date = datetime(2024, 1, 1)
    
    print("=" * 60)
    print("🕰️ DÉMARRAGE SCRAPING HISTORIQUE (Deep Crawl)")
    print(f"📅 Cible: Remonter jusqu'au {target_date.strftime('%d/%m/%Y')}")
    print("⏱️  Timeout par site: 20 minutes")
    print("📄 Pages max par site: 300-500")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser, context, page = await manager.get_context_and_page(p)
        
        try:
            import time
            
            # Timeout de 20 minutes (1200 secondes) par site
            SITE_TIMEOUT = 1200
            
            # Emploi.ma
            print(f"\n🔵 [1/6] Démarrage Emploi.ma...")
            start_time = time.time()
            try:
                await asyncio.wait_for(
                    scrape_emploi_ma_history(pipeline, manager, page, target_date),
                    timeout=SITE_TIMEOUT
                )
                elapsed = time.time() - start_time
                print(f"✅ Emploi.ma terminé en {elapsed/60:.1f} minutes")
            except asyncio.TimeoutError:
                print(f"⏱️  Emploi.ma: Timeout après 20 minutes (normal pour scraping profond)")
            except Exception as e:
                print(f"⚠️  Emploi.ma: Erreur - {e}")
            
            # Rekrute
            print(f"\n🔵 [2/6] Démarrage Rekrute...")
            start_time = time.time()
            try:
                await asyncio.wait_for(
                    scrape_rekrute_history(pipeline, manager, page, target_date),
                    timeout=SITE_TIMEOUT
                )
                elapsed = time.time() - start_time
                print(f"✅ Rekrute terminé en {elapsed/60:.1f} minutes")
            except asyncio.TimeoutError:
                print(f"⏱️  Rekrute: Timeout après 20 minutes (normal pour scraping profond)")
            except Exception as e:
                print(f"⚠️  Rekrute: Erreur - {e}")
            
            # Marocannonces
            print(f"\n🔵 [3/6] Démarrage Marocannonces...")
            start_time = time.time()
            try:
                await asyncio.wait_for(
                    scrape_marocannonces_history(pipeline, manager, page, target_date),
                    timeout=SITE_TIMEOUT
                )
                elapsed = time.time() - start_time
                print(f"✅ Marocannonces terminé en {elapsed/60:.1f} minutes")
            except asyncio.TimeoutError:
                print(f"⏱️  Marocannonces: Timeout après 20 minutes (normal pour scraping profond)")
            except Exception as e:
                print(f"⚠️  Marocannonces: Erreur - {e}")
            
            # Bayt
            print(f"\n🔵 [4/6] Démarrage Bayt...")
            start_time = time.time()
            try:
                await asyncio.wait_for(
                    scrape_bayt_history(pipeline, manager, page, target_date),
                    timeout=SITE_TIMEOUT
                )
                elapsed = time.time() - start_time
                print(f"✅ Bayt terminé en {elapsed/60:.1f} minutes")
            except asyncio.TimeoutError:
                print(f"⏱️  Bayt: Timeout après 20 minutes (normal pour scraping profond)")
            except Exception as e:
                print(f"⚠️  Bayt: Erreur - {e}")
            
            # Tanqeeb
            print(f"\n🔵 [5/6] Démarrage Tanqeeb...")
            start_time = time.time()
            try:
                await asyncio.wait_for(
                    scrape_tanqeeb_history(pipeline, manager, page, target_date),
                    timeout=SITE_TIMEOUT
                )
                elapsed = time.time() - start_time
                print(f"✅ Tanqeeb terminé en {elapsed/60:.1f} minutes")
            except asyncio.TimeoutError:
                print(f"⏱️  Tanqeeb: Timeout après 20 minutes (normal pour scraping profond)")
            except Exception as e:
                print(f"⚠️  Tanqeeb: Erreur - {e}")
            
            # Indeed (risque de blocage)
            print(f"\n🔵 [6/6] Démarrage Indeed (risque de blocage)...")
            start_time = time.time()
            try:
                await asyncio.wait_for(
                    scrape_indeed_history(pipeline, manager, page, target_date),
                    timeout=SITE_TIMEOUT
                )
                elapsed = time.time() - start_time
                print(f"✅ Indeed terminé en {elapsed/60:.1f} minutes")
            except asyncio.TimeoutError:
                print(f"⏱️  Indeed: Timeout après 20 minutes (normal pour scraping profond)")
            except Exception as e:
                print(f"⚠️  Indeed: Erreur - {e}")
            
            pipeline.log_run('success_history')
            print("=" * 60)
            print(f"✅ SCRAPING HISTORIQUE TERMINÉ")
            print(f"📊 Total: {pipeline.new_jobs_count} jobs ajoutés/traités")
            print("=" * 60)
            
        except Exception as e:
            pipeline.log_run('failed_history', str(e))
            print(f"❌ Échec du scraping historique: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
