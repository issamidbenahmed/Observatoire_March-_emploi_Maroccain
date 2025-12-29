"""
Firecrawl Scraper - Extraction Ultra-Rapide via Cloud
Remplace l'IA locale (Ollama) par l'API Firecrawl pour une vitesse maximale.

NÉCESSITE UNE CLÉ API FIRECRAWL (https://firecrawl.dev)
Définissez la variable d'environnement FIRECRAWL_API_KEY ou éditez ce fichier.
"""

import os
import json
import re
import requests
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from import_ai_data import import_ai_scraped_data

# CONFIGURATION
# ---------------------------------------------------------
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "fYour_API_KEY")
API_URL = "https://api.firecrawl.dev/v0/scrape"
# ---------------------------------------------------------

class FirecrawlDeepScraper:
    def __init__(self):
        self.results = []
        self.headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json"
        }
        self.last_saved_file = None

    def _clean_title(self, title: str) -> str:
        """Nettoie le titre pour enlever le superflu"""
        # Enlever les images Markdown (![alt](url))
        title = re.sub(r'!\[.*?\]\(.*?\)', '', title)
        
        # Enlever le gras (**text**)
        title = title.replace("**", "")
        
        # Enlever les caractères d'échappement Markdown
        title = title.replace("\\|", "|").replace("\\-", "-").replace("\\", "")
        
        # Enlever les suffixes de ville courants (ex: "| Casablanca")
        if "|" in title:
            title = title.split("|")[0]
        if " - " in title:
            # On vérifie si la partie après le tiret est courte (probablement une ville)
            parts = title.split(" - ")
            if len(parts) > 1 and len(parts[-1].strip()) < 20:
                title = parts[0]
                
        # Enlever "(Maroc)"
        title = title.replace("(Maroc)", "")
        
        # Liste noire (Boilerplate)
        blacklist = [
            "Lancer 4K", "Postuler", "Matching", "صاحب العمل", "أضف وظيفة", 
            "نشر وظائف", "التالي", "English", "Add jobs", "Next", "Previous",
            "نشر وظيفة الآن", "أضف موقعك", "كل الحقوق محفوظة", "البحث المتقدم", 
            "استكشاف", "تسجيل الدخول", "إنشاء حساب"
        ]
        
        for noise in blacklist:
            title = title.replace(noise, "")
            
        return title.strip()

    def _parse_date(self, context: str, source: str) -> str:
        """Tente d'extraire une date du contexte Markdown"""
        today = datetime.now()
        
        # 0. Relative hours/minutes: "il y a 3 heure(s)", "36 minute(s)"
        match_rel = re.search(r'(?:il y a|Depuis|منذ|ago)\s+(\d+)\s+(?:heure|hour|ساعة|minute|دقيقة)', context, re.IGNORECASE)
        if match_rel:
            return today.strftime('%Y-%m-%d') # Today

        # 1. Format standard Rekrute: du 25/12/2024
        # On évite de matcher des nombres dans des URLs (contenant /202...)
        clean_context = re.sub(r'https?://\S+', '', context)
        
        match = re.search(r'(\d{2})/(\d{2})/(\d{4})', clean_context)
        if match:
            return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
            
        # 2. Format Emploi.ma: 25.12.2024
        match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', clean_context)
        if match:
            return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"

        # 3. Relatif: "il y a 2 jours", "Depuis 3 jours", "منذ 2 أيام"
        match_days = re.search(r'(?:il y a|Depuis|منذ|ago)\s+(\d+)\s+(?:jour|day|أيام|يوم|week|semaine)', context, re.IGNORECASE)
        if match_days:
            from datetime import timedelta
            days_str = match_days.group(1)
            unit = match_days.group(0).lower()
            days = int(days_str)
            if "week" in unit or "semaine" in unit:
                days *= 7
            date_obj = today - timedelta(days=days)
            return date_obj.strftime('%Y-%m-%d')

        # 4. Relatif court: "2j", "3d"
        match_short = re.search(r'(\d+)(?:j|d)\b', clean_context)
        if match_short:
            from datetime import timedelta
            return (today - timedelta(days=int(match_short.group(1)))).strftime('%Y-%m-%d')

        return today.strftime('%Y-%m-%d')

    def _extract_jobs_from_markdown(self, markdown: str, source: str) -> List[Dict]:
        """Parse le markdown pour trouver les offres selon le site"""
        jobs = []
        
        # Patterns spécifiques par site
        patterns = {
            "rekrute.com": r'\[(.*?)\]\((.*?offre-emploi-.*?)\)',
            "emploi.ma": r'\[(.*?)\]\((.*?offre-emploi-.*?|.*?recrutement-.*?)\)',
            "marocannonces.com": r'\[(.*?/annonce/.*?\.html.*?)\s*\]\((.*?/annonce/.*?)\)', # Fallback on URL in brackets if text is mess
            "bayt.com": r'\[(.*?)\]\((.*?/job/.*?)\)',
            "tanqeeb.com": r'\[(.*?)\]\((.*?/jobs/.*?)\)',
            "indeed.com": r'\[(.*?)\]\((.*?/rc/clk\?jk=.*?|.*?/jobs/.*?)\)',
            "linkedin.com": r'\[(.*?)\]\((.*?/jobs/view/.*?|.*?/jobs/search.*?)\)',
            "stagiaires.ma": r'\[(.*?/offres-de-stages-et-premier-emploi-maroc/.*?\]\(.*?\))' # Match the whole block for advanced split
        }
        
        # Specific override for MarocAnnonces multiline and nested
        if "marocannonces" in source:
            # We look for the whole [ ... ]( URL ) block where URL contains /annonce/
            # Greedy match for the title part to include images and secondary text
            site_pattern = r'\[(.*?/annonce/.*?\.html.*?\]\((.*?/annonce/.*?)\))' 
            # Actually, let's use a simpler approach: match everything between [ and the last ] before ( URL_ANNONCE )
            site_pattern = r'\[(.*?)\s*\]\((.*?/annonce/.*?)\)'
        else:
            site_pattern = patterns.get(source, r'\[(.*?)\]\((.*?)\)')

        # Find all matches in the whole markdown (DOTALL for multiline)
        if "stagiaires" in source:
            # Pour stagiaires.ma, on cherche tous les blocs qui finissent par le lien job
            matches_raw = re.findall(r'\[(.*?)\s*\]\((https?://www\.stagiaires\.ma/offres-de-stages-et-premier-emploi-maroc/.*?/)\)', markdown, re.DOTALL)
            # On simule la structure match
            class MockMatch:
                def __init__(self, c, u, s): self._groups = (c, u); self._start = s
                def group(self, i): return self._groups[i-1]
                def start(self): return self._start
            
            matches = []
            for m in matches_raw:
                matches.append(MockMatch(m[0], m[1], markdown.find(m[0])))
        else:
            matches = list(re.finditer(site_pattern, markdown, re.DOTALL))
        
        for match in matches:
            content = match.group(1).strip()
            url_part = match.group(2).strip()
            
            title = content
            # Special case for MarocAnnonces where group 1 might contain a nested link text later
            if "marocannonces" in source:
                # Filtrer pour ne garder que les Offres d'emploi
                if "Offres-emploi" not in url_part:
                    continue
                    
                # Extraire le titre du texte en gras si présent
                m_bold = re.search(r'\*\*(.*?)\*\*', content)
                if m_bold:
                    title = m_bold.group(1)
                else:
                    # Clean up the image/alt text if bold not found
                    title = self._clean_title(content)
            else:
                title = self._clean_title(content)

            # Validation URL
            if source in url_part or url_part.startswith('/') or "indeed" in url_part or "linkedin" in url_part or "/annonce/" in url_part:
                # Reconstruire URL absolue si besoin
                domain = ""
                if url_part.startswith('/'):
                    if "rekrute" in source: domain = "https://www.rekrute.com"
                    elif "emploi.ma" in source: domain = "https://www.emploi.ma"
                    elif "marocannonces" in source: domain = "https://www.marocannonces.com"
                    elif "bayt" in source: domain = "https://www.bayt.com"
                    elif "tanqeeb" in source: domain = "https://morocco.tanqeeb.com"
                    elif "indeed" in source: domain = "https://ma.indeed.com"
                    elif "linkedin" in source: domain = "https://www.linkedin.com"
                    elif "stagiaires" in source: domain = "https://www.stagiaires.ma"
                
                full_url = f"{domain}{url_part}"
                
                # Ignorer les liens non pertinents (pagination, login, etc)
                if "page=" in full_url or "login" in full_url or "register" in full_url:
                    continue
                
                # Context (surrounding text)
                start_idx = match.start()
                context = markdown[max(0, start_idx-100):min(len(markdown), start_idx+500)]
                
                # Date extraction
                date_posted = self._parse_date(context, source)
                    
                # List of major Moroccan cities for matching
                cities = [
                    "Casablanca", "Rabat", "Marrakech", "Fès", "Tanger", "Agadir", "Meknès", 
                    "Oujda", "Kenitra", "Tetouan", "Temara", "Safi", "Mohammedia", "El Jadida", 
                    "Beni Mellal", "Nador", "Taza", "Settat", "Larache", "Khemisset", "Guelmim", 
                    "Berrechid", "Khouribga", "Ifrane", "Sala al Jadida", "Salé", "Mediouna"
                ]
                
                # Tentative 1: Extraction de la ville depuis le titre (Ex: "Poste | Ville")
                location = "Maroc"
                found_city = False
                
                # Check in title first
                for city in cities:
                    if city.lower() in title.lower():
                        location = city
                        found_city = True
                        break
                
                # Tentative 2: Check in context (next lines)
                if not found_city:
                    for city in cities:
                        if city.lower() in context.lower():
                            location = city
                            found_city = True
                            break

                # Nettoyage du titre
                title = self._clean_title(title)
                
                # Ignorer les titres vides ou trop courts ou contenant du bruit
                is_noise = False
                for noise in ["صاحب العمل", "التالي", "نشر وظائف", "نشر وظيفة"]:
                    if noise in title:
                        is_noise = True
                        break
                
                if is_noise or len(title) < 5 or "..." in title:
                    continue

                job = {
                    "title": title,
                    "company": "N/A", # Difficile à extraire sans structure stricte
                    "location": location,
                    "date_posted": date_posted,
                    "url": full_url,
                    "source": source,
                    "scraped_at": datetime.now().isoformat(),
                    "description_summary": context[:200]
                }
                jobs.append(job)
                
        return jobs

    def scrape_page(self, url: str, source: str) -> List[Dict]:
        """
        Scrape une page de liste et extrait les offres via Firecrawl (Markdown mode).
        """
        if "YOUR_API_KEY" in FIRECRAWL_API_KEY:
            print("❌ ERREUR: Clé API Firecrawl manquante!")
            return []

        payload = {
            "url": url,
            "formats": ["markdown"],
        }

        try:
            print(f"🔥 Firecrawl: {url}...")
            # Firecrawl prend parfois du temps pour le rendu JS
            response = requests.post(API_URL, headers=self.headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    markdown = data['data'].get('markdown', '')
                    jobs = self._extract_jobs_from_markdown(markdown, source)
                    print(f"   ✅ {len(jobs)} offres trouvées (Regex Markdown)")
                    return jobs
                else:
                    print(f"   ⚠️ Firecrawl échec: {data.get('error')}")
            elif response.status_code == 429:
                # GESTION DU RATE LIMIT
                retry_after = 30 # Par défaut
                try:
                    error_data = response.json()
                    msg = error_data.get('error', '')
                    # Chercher un nombre dans "retry after 26s"
                    wait_match = re.search(r'after (\d+)s', msg)
                    if wait_match:
                        retry_after = int(wait_match.group(1)) + 2
                except: pass
                
                print(f"   ⏳ Rate Limit atteint. Pause de {retry_after}s...")
                time.sleep(retry_after)
                return self.scrape_page(url, source) # Réessayer une fois
            else:
                print(f"   ❌ Erreur HTTP {response.status_code}: {response.text}")
                
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"   ⏳ Timeout/Erreur réseau. Nouvelle tentative dans 10s... ({e})")
            time.sleep(10)
            # On peut retenter une fois récursivement (limité par la logique au-dessus)
            return self.scrape_page(url, source)
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            
        return []

    def _save_results(self):
        filename = f"firecrawl_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        self.last_saved_file = filepath
        print(f"💾 Sauvegardé: {filepath}")

    def merge_json_files(self):
        """Fusionne tous les fichiers JSON firecrawl en un seul"""
        print("\n🔄 Fusion des fichiers JSON...")
        directory = os.path.dirname(__file__)
        all_jobs = []
        files = [f for f in os.listdir(directory) if f.startswith("firecrawl_jobs_") and f.endswith(".json")]
        
        for f in files:
            path = os.path.join(directory, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    if isinstance(data, list):
                        all_jobs.extend(data)
            except Exception as e:
                print(f"❌ Erreur lecture {f}: {e}")
        
        # Sauvegarde global
        global_filename = "firecrawl_jobs_GLOBAL.json"
        global_path = os.path.join(directory, global_filename)
        
        with open(global_path, 'w', encoding='utf-8') as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
            
        print(f"✅ FUSION COMPLÈTE: {len(all_jobs)} offres dans {global_filename}")
        return global_path

    # -------------------------------------------------------------------------
    
    def run_rekrute(self, start_date: datetime):
        print("\n🤖 FIRECRAWL SCRAPING: REKRUTE")
        base_url = "https://www.rekrute.com/offres.html"
        MAX_PAGES = 250  # Focus on quality: 250 for Rekrute, 250 for Emploi.ma = 500 total
        
        for page_num in range(1, MAX_PAGES + 1):
            url = f"{base_url}?p={page_num}&s=1&o=1"
            print(f"\n📄 Page {page_num}/{MAX_PAGES}...")
            
            jobs = self.scrape_page(url, "rekrute.com")
            
            if not jobs:
                print("⚠️ Pas de jobs ou erreur, arrêt.")
                break
                
            self.results.extend(jobs)
            
            # Check dates
            page_min_date = datetime.now()
            for job in jobs:
                d_str = job.get('date_posted')
                if d_str:
                    try:
                        d = datetime.strptime(d_str, '%Y-%m-%d')
                        page_min_date = min(page_min_date, d)
                    except: pass
            
            if page_min_date < start_date:
                print(f"🛑 Date limite atteinte ({page_min_date}). Arrêt.")
                break
            
            self._save_results()
            time.sleep(6) # Plus lent pour le plan gratuit (10 req/min max)

    def run_emploi_ma(self, start_date: datetime):
        print("\n🤖 FIRECRAWL SCRAPING: EMPLOI.MA")
        base_url = "https://www.emploi.ma/recherche-jobs-maroc"
        MAX_PAGES = 250
        
        for page_num in range(1, MAX_PAGES + 1):
            url = f"{base_url}?page={page_num}"
            print(f"\n📄 Page {page_num}/{MAX_PAGES}...")
            
            jobs = self.scrape_page(url, "emploi.ma")
            if not jobs: break
            
            self.results.extend(jobs)
            
            page_min_date = datetime.now()
            for job in jobs:
                d_str = job.get('date_posted')
                if d_str:
                    try:
                        d = datetime.strptime(d_str, '%Y-%m-%d')
                        page_min_date = min(page_min_date, d)
                    except: pass
            
            if page_min_date < start_date:
                print("🛑 Date limite atteinte.")
                break
                
            self._save_results()
            time.sleep(6)

    def run_marocannonces(self, start_date: datetime):
        print("\n🤖 FIRECRAWL SCRAPING: MAROCANNONCES")
        base_url = "https://www.marocannonces.com/maroc/offres-emploi-b292.html"
        MAX_PAGES = 165
        
        for page_num in range(1, MAX_PAGES + 1):
            url = f"{base_url}?pge={page_num}"
            print(f"\n📄 Page {page_num}/{MAX_PAGES}...")
            jobs = self.scrape_page(url, "marocannonces.com")
            if not jobs: break
            self.results.extend(jobs)
            self._save_results()
            time.sleep(6)

    def run_bayt(self, start_date: datetime):
        print("\n🤖 FIRECRAWL SCRAPING: BAYT")
        base_url = "https://www.bayt.com/fr/morocco/jobs/"
        MAX_PAGES = 165
        
        for page_num in range(1, MAX_PAGES + 1):
            url = f"{base_url}?page={page_num}"
            print(f"\n📄 Page {page_num}/{MAX_PAGES}...")
            jobs = self.scrape_page(url, "bayt.com")
            if not jobs: break
            self.results.extend(jobs)
            self._save_results()
            time.sleep(6)

    def run_tanqeeb(self, start_date: datetime):
        print("\n🤖 FIRECRAWL SCRAPING: TANQEEB")
        base_url = "https://morocco.tanqeeb.com/ar/jobs/search?country=50"
        MAX_PAGES = 165
        
        for page_num in range(1, MAX_PAGES + 1):
            url = f"{base_url}&page={page_num}"
            print(f"\n📄 Page {page_num}/{MAX_PAGES}...")
            jobs = self.scrape_page(url, "tanqeeb.com")
            if not jobs: break
            self.results.extend(jobs)
            self._save_results()
            time.sleep(6)

    def run_indeed(self, start_date: datetime):
        print("\n🤖 FIRECRAWL SCRAPING: INDEED")
        # Indeed Morocco
        base_url = "https://ma.indeed.com/jobs?q=&l=Maroc"
        MAX_PAGES = 50
        
        for p in range(0, MAX_PAGES):
            start = p * 10
            url = f"{base_url}&start={start}"
            print(f"\n📄 Page {p+1}/{MAX_PAGES}...")
            jobs = self.scrape_page(url, "indeed.com")
            if not jobs: break
            self.results.extend(jobs)
            self._save_results()
            time.sleep(6)

    def run_linkedin(self, start_date: datetime):
        print("\n🤖 FIRECRAWL SCRAPING: LINKEDIN")
        # LinkedIn Morocco (Public Search)
        base_url = "https://www.linkedin.com/jobs/search?keywords=&location=Morocco"
        MAX_PAGES = 50
        
        for p in range(0, MAX_PAGES):
            start = p * 25
            url = f"{base_url}&start={start}"
            print(f"\n📄 Page {p+1}/{MAX_PAGES}...")
            jobs = self.scrape_page(url, "linkedin.com")
            if not jobs: break
            self.results.extend(jobs)
            self._save_results()
            time.sleep(6)

    def run_stagiaires_ma(self, start_date: datetime):
        print("\n🤖 FIRECRAWL SCRAPING: STAGIAIRES.MA")
        base_url = "https://www.stagiaires.ma/offres-de-stages-et-premier-emploi-maroc/"
        MAX_PAGES = 165
        
        for page_num in range(1, MAX_PAGES + 1):
            url = f"{base_url}?pages={page_num}"
            print(f"\n📄 Page {page_num}/{MAX_PAGES}...")
            jobs = self.scrape_page(url, "stagiaires.ma")
            if not jobs: break
            
            self.results.extend(jobs)
            self._save_results()
            time.sleep(6)

def main():
    print("🚀 FIRECRAWL SCRAPER LAUNCH")
    scraper = FirecrawlDeepScraper()
    
    start_date = datetime(2024, 1, 1)
    
    start_date = datetime(2024, 1, 1)
    
    # Run only Stagiaires.ma as requested
    scraper.run_stagiaires_ma(start_date)
    # scraper.run_marocannonces(start_date)
    # scraper.run_indeed(start_date)
    # scraper.run_linkedin(start_date)
    
    # Merge all results at the end
    global_file = scraper.merge_json_files()
    
    if global_file and os.path.exists(global_file):
        print("\n🔄 Auto-Importing Global Data...")
        try:
            import_ai_scraped_data(global_file)
        except Exception as e:
            print(f"❌ Error during import: {e}")

if __name__ == "__main__":
    main()
