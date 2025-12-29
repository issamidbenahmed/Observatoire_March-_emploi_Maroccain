"""
Deep AI Scraper - Extraction intelligente avec Ollama
Scrape les offres d'emploi IT de janvier 2024 à aujourd'hui avec extraction AI
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from playwright.async_api import async_playwright
import sys
import os
import traceback
from import_ai_data import import_ai_scraped_data

# Configuration Ollama
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:7b"  # Changed to available model

# Prompt pour l'extraction structurée
EXTRACTION_PROMPT = """Tu es un expert en extraction de données d'offres d'emploi IT au Maroc.

Analyse cette offre d'emploi et extrait les informations suivantes au format JSON strict :

{{
  "title": "titre exact du poste",
  "company": "nom de l'entreprise (ou null si non mentionné)",
  "location": "ville exacte au Maroc (Casablanca, Rabat, etc.)",
  "date_posted": "date de publication au format YYYY-MM-DD (estime si relative comme 'il y a 2 jours')",
  "technologies": ["liste", "des", "technologies", "mentionnées"],
  "skills": ["liste", "des", "compétences", "requises"],
  "contract_type": "CDI/CDD/Stage/Freelance/null",
  "experience_required": "nombre d'années ou 'débutant' ou null",
  "salary": "fourchette salariale si mentionnée ou null",
  "description_summary": "résumé en 2-3 phrases"
}}

RÈGLES IMPORTANTES:
- Pour la ville: utilise UNIQUEMENT les grandes villes marocaines (Casablanca, Rabat, Marrakech, Fès, Tanger, Agadir, etc.)
- Pour les technologies: extrait TOUS les langages, frameworks, outils (Python, Java, React, Docker, etc.)
- Pour les compétences: extrait les soft skills ET hard skills
- Pour la date: si "il y a X heures" ou "X minutes", utilise AUJOURD'HUI ({today}). 
- IMPORTANT: Nous sommes en DECEMBRE 2025. Toute offre récente doit avoir l'année 2025.
- Si une info n'est pas trouvée, mets null (pas de string vide)

OFFRE D'EMPLOI:
{job_content}

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après.
"""

class AIJobExtractor:
    """Extracteur de données avec Ollama"""
    
    def __init__(self):
        self.today = datetime.now().strftime("%Y-%m-%d")
    
    def extract_with_ollama(self, job_content: str) -> Optional[Dict]:
        """Extrait les données d'une offre avec Ollama"""
        try:
            prompt = EXTRACTION_PROMPT.format(
                job_content=job_content[:4000],  # Limite pour éviter les timeouts
                today=self.today
            )
            
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"  # Force JSON output
                },
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                extracted_text = result.get("response", "")
                
                # Parser le JSON
                try:
                    # Nettoyer le texte pour extraire le JSON
                    json_match = re.search(r'\{.*\}', extracted_text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        
                        if not isinstance(data, dict):
                            print(f"❌ Réponse AI invalide (pas un dict): {type(data)}")
                            return None
                            
                        return self._validate_and_clean(data)
                except json.JSONDecodeError as e:
                    print(f"❌ Erreur JSON: {e}")
                    print(f"Réponse: {extracted_text[:200]}")
                    return None
            else:
                print(f"❌ Erreur Ollama: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur extraction: {e}")
            print(f"Réponse brute: {extracted_text if 'extracted_text' in locals() else 'N/A'}")
            print(traceback.format_exc())
            return None
    
    def _validate_and_clean(self, data: Dict) -> Dict:
        """Valide et nettoie les données extraites"""
        # Convertir les listes vides en None
        cleaned_data = {}
        for k, v in data.items():
            # Clean keys (remove newlines, quotes)
            clean_key = k.replace('\n', '').replace('"', '').strip()
            cleaned_data[clean_key] = v

        data = cleaned_data

        for key in ['technologies', 'skills']:
            if key in data and isinstance(data[key], list) and len(data[key]) == 0:
                data[key] = None
        
        # Valider la date
        if 'date_posted' in data and data['date_posted']:
            try:
                datetime.strptime(data['date_posted'], '%Y-%m-%d')
            except:
                data['date_posted'] = None
        
        return data


class DeepAIScraper:
    """Scraper AI pour extraction en profondeur"""
    
    def __init__(self):
        self.extractor = AIJobExtractor()
        self.results = []
        self.last_saved_file = None
        self.consecutive_old_jobs = 0 # Compteur pour arrêt robuste
    
    async def scrape_stagiaires_ma_deep(self, start_date: datetime, end_date: datetime):
        """Scrape Stagiaires.ma avec extraction AI"""
        print(f"\n🤖 DEEP SCRAPING STAGIAIRES.MA avec AI")
        print("=" * 80)
        
        async with async_playwright() as p:
            # Headless false pour voir ce qui se passe (optionnel)
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            base_url = "https://www.stagiaires.ma/offres-de-stages-et-premier-emploi-maroc/"
            
            for page_num in range(1, 166):
                try:
                    url = f"{base_url}?pages={page_num}"
                    print(f"\n📄 Page {page_num}...")
                    
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                    # Extraire les cartes (l'enveloppe 'a' qui contient la card)
                    job_cards = await page.query_selector_all('a:has(div.card_candidature)')
                    
                    if not job_cards:
                        print("⚠️ Plus d'offres trouvées, arrêt.")
                        break

                    print(f"  Trouvé {len(job_cards)} offres")
                    page_min_date = datetime.now()
                    
                    for idx, card in enumerate(job_cards, 1):
                        card_text = await card.inner_text()
                        job_url = await card.get_attribute('href')
                        if job_url and not job_url.startswith('http'):
                            job_url = f"https://www.stagiaires.ma{job_url}"

                        print(f"    [{idx}/{len(job_cards)}] Extraction AI (Carte)...")
                        job_data = await self._extract_from_card_text(card_text, job_url, source="stagiaires.ma")
                        
                        if job_data:
                            date_posted = job_data.get('date_posted')
                            
                            # Validation IT minimum (optionnel mais recommandé pour l'observatoire)
                            # On laisse passer pour l'instant pour stagiaires.ma
                            
                            if date_posted:
                                try:
                                    d = datetime.strptime(date_posted, '%Y-%m-%d')
                                    if d < start_date:
                                        self.consecutive_old_jobs += 1
                                        print(f"      🛑 Offre ancienne ({date_posted}) [{self.consecutive_old_jobs}/5]")
                                    else:
                                        self.consecutive_old_jobs = 0 # Reset si on trouve une offre récente
                                        self.results.append(job_data)
                                        title = job_data.get('title') or 'N/A'
                                        print(f"      ✅ {title[:40]}... ({date_posted})")
                                except:
                                    self.results.append(job_data)
                            else:
                                self.results.append(job_data)
                    
                    if self.consecutive_old_jobs >= 5:
                        print(f"\n🛑 Plusieurs offres anciennes consécutives. Arrêt robuste.")
                        break
                        
                    self._save_results()
                        
                except Exception as e:
                    print(f"❌ Erreur page {page_num}: {e}")
                    continue
            
            await browser.close()
            self._save_results()

    async def scrape_rekrute_deep(self, start_date: datetime, end_date: datetime):
        """Scrape Rekrute avec extraction AI"""
        print(f"\n🤖 DEEP SCRAPING REKRUTE avec AI")
        print(f"Période: {start_date.date()} → {end_date.date()}")
        print("=" * 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            base_url = "https://www.rekrute.com/offres.html"
            
            # Scraper jusqu'à la date limite
            max_pages = 500
            for page_num in range(1, max_pages + 1):
                try:
                    url = f"{base_url}?p={page_num}&s=1&o=1"
                    print(f"\n📄 Page {page_num}...")
                    
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    # Extraire les cartes d'offres
                    job_cards = await page.query_selector_all('li.post-id')
                    
                    if not job_cards:
                        print("⚠️ Plus d'offres trouvées, arrêt.")
                        break

                    print(f"  Trouvé {len(job_cards)} offres sur la page")
                    page_min_date = datetime.now()
                    
                    for idx, card in enumerate(job_cards, 1):
                        # Extraire le texte complet de la carte
                        card_text = await card.inner_text()
                        
                        # Tenter d'extraire l'URL juste pour référence
                        url_el = await card.query_selector('a.titreJob')
                        if url_el:
                            href = await url_el.get_attribute('href')
                            job_url = f"https://www.rekrute.com{href}" if href.startswith('/') else href
                        else:
                            job_url = "N/A"

                        print(f"    [{idx}/{len(job_cards)}] Extraction AI (Carte)...")
                        
                        job_data = await self._extract_from_card_text(card_text, job_url, source="rekrute.com")
                        
                        if job_data:
                            self.results.append(job_data)
                            title = job_data.get('title') or 'N/A'
                            date_posted = job_data.get('date_posted')
                            
                            print(f"      ✅ {title[:40]}... ({date_posted})")
                            
                            # Update page min date
                            if date_posted:
                                try:
                                    d = datetime.strptime(date_posted, '%Y-%m-%d')
                                    page_min_date = min(page_min_date, d)
                                    if d < start_date:
                                        print(f"      🛑 Offre trop ancienne ({date_posted})")
                                except: pass
                        else:
                            print(f"      ❌ Échec extraction")
                    
                    if page_min_date < start_date:
                        print(f"\n🛑 Date limite atteinte ({start_date.strftime('%Y-%m-%d')}). Arrêt du scraping.")
                        break
                        
                    if page_num % 5 == 0:
                        self._save_results()
                    
                except Exception as e:
                    print(f"❌ Erreur page {page_num}: {e}")
                    continue
            
    async def scrape_emploi_ma_deep(self, start_date: datetime, end_date: datetime):
        """Scrape Emploi.ma avec extraction AI"""
        print(f"\n🤖 DEEP SCRAPING EMPLOI.MA avec AI")
        print("=" * 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            base_url = "https://www.emploi.ma/recherche-jobs-maroc"
            
            for page_num in range(1, 501):
                try:
                    url = f"{base_url}?page={page_num}"
                    print(f"\n📄 Page {page_num}...")
                    
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Extraire les cartes
                    job_cards = await page.query_selector_all('.card-job-detail')
                    
                    if not job_cards:
                        print("⚠️ Plus d'offres trouvées, arrêt.")
                        break

                    print(f"  Trouvé {len(job_cards)} offres")
                    page_min_date = datetime.now()
                    
                    for idx, card in enumerate(job_cards, 1):
                        card_text = await card.inner_text()
                        
                        # Url
                        url_el = await card.query_selector('h3 a')
                        if url_el:
                            href = await url_el.get_attribute('href')
                            job_url = f"https://www.emploi.ma{href}" if href.startswith('/') else href
                        else:
                            job_url = "N/A"

                        print(f"    [{idx}/{len(job_cards)}] Extraction AI (Carte)...")
                        job_data = await self._extract_from_card_text(card_text, job_url, source="emploi.ma")
                        
                        if job_data:
                            self.results.append(job_data)
                            title = job_data.get('title') or 'N/A'
                            date_posted = job_data.get('date_posted')
                            print(f"      ✅ {title[:40]}... ({date_posted})")
                            
                            if date_posted:
                                try:
                                    d = datetime.strptime(date_posted, '%Y-%m-%d')
                                    page_min_date = min(page_min_date, d)
                                    if d < start_date:
                                        print(f"      🛑 Offre trop ancienne ({date_posted})")
                                except: pass
                        else:
                            print(f"      ❌ Échec extraction")
                    
                    if page_min_date < start_date:
                        print(f"\n🛑 Date limite atteinte ({start_date.strftime('%Y-%m-%d')}). Arrêt.")
                        break
                        
                    if page_num % 5 == 0:
                        self._save_results()
                        
                except Exception as e:
                    print(f"❌ Erreur page {page_num}: {e}")
                    continue
            
            await browser.close()
            self._save_results()

    async def scrape_marocannonces_deep(self, start_date: datetime, end_date: datetime):
        """Scrape MarocAnnonces avec extraction AI"""
        print(f"\n🤖 DEEP SCRAPING MAROCANNONCES avec AI")
        print("=" * 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            base_url = "https://www.marocannonces.com/maroc/offres-emploi-b292.html"
            
            for page_num in range(1, 501):
                try:
                    url = f"{base_url}?pge={page_num}"
                    print(f"\n📄 Page {page_num}...")
                    
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Extraire les cartes
                    job_cards = await page.query_selector_all('ul.cars-list li, ul.content_list li')
                    
                    if not job_cards:
                        print("⚠️ Plus d'offres trouvées, arrêt.")
                        break

                    print(f"  Trouvé {len(job_cards)} offres")
                    page_min_date = datetime.now()
                    
                    for idx, card in enumerate(job_cards, 1):
                        card_text = await card.inner_text()
                        
                        # Url
                        url_el = await card.query_selector('h3 a')
                        if url_el:
                            href = await url_el.get_attribute('href')
                            if not href.startswith('http'):
                                job_url = f"https://www.marocannonces.com/{href.lstrip('/')}"
                            else:
                                job_url = href
                        else:
                            job_url = "N/A"

                        print(f"    [{idx}/{len(job_cards)}] Extraction AI (Carte)...")
                        job_data = await self._extract_from_card_text(card_text, job_url, source="marocannonces.com")
                        
                        if job_data:
                            self.results.append(job_data)
                            title = job_data.get('title') or 'N/A'
                            date_posted = job_data.get('date_posted')
                            print(f"      ✅ {title[:40]}... ({date_posted})")
                            
                            if date_posted:
                                try:
                                    d = datetime.strptime(date_posted, '%Y-%m-%d')
                                    page_min_date = min(page_min_date, d)
                                    if d < start_date:
                                        print(f"      🛑 Offre trop ancienne ({date_posted})")
                                except: pass
                        else:
                             print(f"      ❌ Échec extraction")

                    if page_min_date < start_date:
                        print(f"\n🛑 Date limite atteinte. Arrêt.")
                        break
                        
                    if page_num % 5 == 0:
                        self._save_results()
                        
                except Exception as e:
                    print(f"❌ Erreur page {page_num}: {e}")
                    continue
            
            await browser.close()
            self._save_results()

    async def scrape_bayt_deep(self, start_date: datetime, end_date: datetime):
        """Scrape Bayt avec extraction AI"""
        print(f"\n🤖 DEEP SCRAPING BAYT avec AI")
        print("=" * 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            base_url = "https://www.bayt.com/fr/morocco/jobs/"
            
            for page_num in range(1, 501):
                try:
                    url = f"{base_url}?page={page_num}"
                    print(f"\n📄 Page {page_num}...")
                    
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Extraire les cartes
                    job_cards = await page.query_selector_all('.t-regular-job-card, li.has-pointer-d')
                    
                    if not job_cards:
                        print("⚠️ Plus d'offres trouvées sur cette page.")
                        if page_num > 1: break

                    print(f"  Trouvé {len(job_cards)} offres")
                    page_min_date = datetime.now()
                    
                    for idx, card in enumerate(job_cards, 1):
                        card_text = await card.inner_text()
                        
                        # Url
                        url_el = await card.query_selector('h2 a')
                        if url_el:
                            href = await url_el.get_attribute('href')
                            job_url = f"https://www.bayt.com{href}" if not href.startswith('http') else href
                        else:
                            job_url = "N/A"

                        print(f"    [{idx}/{len(job_cards)}] Extraction AI (Carte)...")
                        job_data = await self._extract_from_card_text(card_text, job_url, source="bayt.com")
                        
                        if job_data:
                            self.results.append(job_data)
                            title = job_data.get('title') or 'N/A'
                            date_posted = job_data.get('date_posted')
                            print(f"      ✅ {title[:40]}... ({date_posted})")
                            
                            if date_posted:
                                try:
                                    d = datetime.strptime(date_posted, '%Y-%m-%d')
                                    page_min_date = min(page_min_date, d)
                                    if d < start_date:
                                        print(f"      🛑 Offre trop ancienne ({date_posted})")
                                except: pass
                        else:
                            print(f"      ❌ Échec extraction")

                    if page_min_date < start_date:
                        print(f"\n🛑 Date limite atteinte. Arrêt.")
                        break
                        
                    self._save_results()
                        
                except Exception as e:
                    print(f"❌ Erreur page {page_num}: {e}")
                    continue
            
            await browser.close()
            self._save_results()
            
    async def scrape_tanqeeb_deep(self, start_date: datetime, end_date: datetime):
        """Scrape Tanqeeb avec extraction AI"""
        print(f"\n🤖 DEEP SCRAPING TANQEEB avec AI")
        print("=" * 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            base_url = "https://morocco.tanqeeb.com/ar/jobs/search?country=50"
            
            for page_num in range(1, 501):
                try:
                    url = f"{base_url}&page={page_num}"
                    print(f"\n📄 Page {page_num}...")
                    
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Extraire les cartes
                    job_cards = await page.query_selector_all('.card-list-item')
                    
                    if not job_cards:
                        print("⚠️ Plus d'offres trouvées, arrêt.")
                        break

                    print(f"  Trouvé {len(job_cards)} offres")
                    page_min_date = datetime.now()
                    
                    for idx, card in enumerate(job_cards, 1):
                        card_text = await card.inner_text()
                        
                        # Url (le card est souvent un a href direct ou contient un a)
                        href = await card.get_attribute('href')
                        if not href:
                            a_tag = await card.query_selector('a')
                            if a_tag: href = await a_tag.get_attribute('href')

                        if href:
                            job_url = f"https://morocco.tanqeeb.com{href}" if not href.startswith('http') else href
                        else:
                            job_url = "N/A"

                        print(f"    [{idx}/{len(job_cards)}] Extraction AI (Carte)...")
                        job_data = await self._extract_from_card_text(card_text, job_url, source="tanqeeb.com")
                        
                        if job_data:
                            self.results.append(job_data)
                            title = job_data.get('title') or 'N/A'
                            date_posted = job_data.get('date_posted')
                            print(f"      ✅ {title[:40]}... ({date_posted})")
                            
                            if date_posted:
                                try:
                                    d = datetime.strptime(date_posted, '%Y-%m-%d')
                                    page_min_date = min(page_min_date, d)
                                    if d < start_date:
                                        print(f"      🛑 Offre trop ancienne ({date_posted})")
                                except: pass
                        else:
                            print(f"      ❌ Échec extraction")
                    
                    if page_min_date < start_date:
                         # Tanqeeb mixe parfois, on laisse un peu de marge
                        print(f"\n🛑 Date limite atteinte. Arrêt.")
                        break
                        
                    self._save_results()
                        
                except Exception as e:
                    print(f"❌ Erreur page {page_num}: {e}")
                    continue
            
            await browser.close()
            self._save_results()

    
    async def _extract_from_card_text(self, card_text: str, job_url: str, source: str) -> Optional[Dict]:
        """Extrait les données à partir du texte de la carte"""
        try:
             # Préparer le contenu pour l'AI
            job_content = f"""
SOURCE: {source}
URL: {job_url}
CONTENU CARTE:
{card_text[:4000]}
"""
            # Extraction AI
            extracted_data = self.extractor.extract_with_ollama(job_content)
            
            if extracted_data:
                extracted_data['url'] = job_url
                extracted_data['source'] = source
                extracted_data['scraped_at'] = datetime.now().isoformat()
                return extracted_data
            
            return None
            
        except Exception as e:
            print(f"      ⚠️ Erreur: {e}")
            return None
    
    def _save_results(self):
        """Sauvegarde les résultats en JSON"""
        filename = f"ai_scraped_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        self.last_saved_file = filepath
        print(f"💾 Sauvegardé: {filepath}")


async def main():
    """Point d'entrée principal"""
    print("\n" + "="*80)
    print("🤖 DEEP AI SCRAPER - Extraction Intelligente avec Ollama")
    print("="*80)
    
    # Vérifier Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama connecté - Modèles disponibles: {len(models)}")
            for model in models:
                print(f"   - {model.get('name', 'unknown')}")
        else:
            print("❌ Ollama non accessible")
            return
    except Exception as e:
        print(f"❌ Erreur connexion Ollama: {e}")
        print("💡 Assure-toi qu'Ollama est lancé: ollama serve")
        return
    
    # Définir la période
    start_date = datetime(2024, 1, 1)
    end_date = datetime.now()
    
    # Lancer le scraping
    scraper = DeepAIScraper()
    
    # Executer séquentiellement
    await scraper.scrape_stagiaires_ma_deep(start_date, end_date)
    # await scraper.scrape_rekrute_deep(start_date, end_date)
    # await scraper.scrape_emploi_ma_deep(start_date, end_date)
    # await scraper.scrape_marocannonces_deep(start_date, end_date)
    # await scraper.scrape_bayt_deep(start_date, end_date)
    # await scraper.scrape_tanqeeb_deep(start_date, end_date)

    
    print("\n" + "="*80)
    print("✅ SCRAPING TERMINÉ")
    print("="*80)

    # Auto-Import
    if scraper.last_saved_file and os.path.exists(scraper.last_saved_file):
        print(f"\n🔄 LANCEMENT DE L'IMPORT AUTOMATIQUE...")
        try:
            import_ai_scraped_data(scraper.last_saved_file)
        except Exception as e:
            print(f"❌ Erreur lors de l'import automatique: {e}")
    else:
        print("⚠️ Aucun fichier à importer.")


if __name__ == "__main__":
    asyncio.run(main())
