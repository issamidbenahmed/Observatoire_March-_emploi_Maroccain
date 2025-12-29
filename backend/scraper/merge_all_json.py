import os
import json
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from import_ai_data import import_ai_scraped_data

def merge_and_import():
    directory = os.path.dirname(os.path.abspath(__file__))
    all_jobs = []
    seen_urls = set()
    
    # Patterns to look for
    prefixes = ["firecrawl_jobs_", "ai_scraped_jobs_"]
    
    print(f"🔍 Recherche des fichiers JSON dans {directory}...")
    
    # Collect all files
    files_to_merge = []
    for f in os.listdir(directory):
        if f.endswith(".json") and any(f.startswith(p) for p in prefixes) and "GLOBAL" not in f:
            files_to_merge.append(f)
    
    print(f"📦 Trouvé {len(files_to_merge)} fichiers à fusionner.")
    
    for filename in files_to_merge:
        path = os.path.join(directory, filename)
        try:
            with open(path, 'r', encoding='utf-8') as file:
                jobs = json.load(file)
                if isinstance(jobs, list):
                    new_count = 0
                    for job in jobs:
                        url = job.get('url')
                        if url and url not in seen_urls:
                            all_jobs.append(job)
                            seen_urls.add(url)
                            new_count += 1
                    print(f"   ✅ {filename}: {new_count} nouvelles offres (total unique: {len(all_jobs)})")
        except Exception as e:
            print(f"   ❌ Erreur lecture {filename}: {e}")

    if not all_jobs:
        print("⚠️ Aucune offre trouvée dans les fichiers.")
        return

    # Sauvegarde du fichier global
    global_path = os.path.join(directory, "firecrawl_jobs_GLOBAL.json")
    print(f"\n💾 Sauvegarde de {len(all_jobs)} offres dans {global_path}...")
    
    with open(global_path, 'w', encoding='utf-8') as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)
    
    print("🚀 Démarrage de l'import dans la base de données...")
    import_ai_scraped_data(global_path)

if __name__ == "__main__":
    merge_and_import()
