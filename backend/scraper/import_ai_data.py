"""
Importe les données scrapées par l'AI dans la base de données
"""

import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Job

def import_ai_scraped_data(json_file: str):
    """Importe les données du fichier JSON dans la BD"""
    
    print(f"\n📥 IMPORT DES DONNÉES AI")
    print("=" * 80)
    
    # Charger le fichier JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            jobs_data = json.load(f)
        print(f"✅ Fichier chargé: {len(jobs_data)} offres")
    except Exception as e:
        print(f"❌ Erreur lecture fichier: {e}")
        return
    
    with app.app_context():
        added = 0
        skipped = 0
        errors = 0
        
        for idx, job_data in enumerate(jobs_data, 1):
            try:
                # Vérifier si l'offre existe déjà
                existing = Job.query.filter_by(url_offre=job_data.get('url')).first()
                
                if existing:
                    skipped += 1
                    if idx % 50 == 0:
                        print(f"  [{idx}/{len(jobs_data)}] Traité: {added} ajoutés, {skipped} doublons")
                    continue
                
                # Parser la date
                date_posted = None
                if job_data.get('date_posted'):
                    try:
                        date_posted = datetime.strptime(job_data['date_posted'], '%Y-%m-%d')
                    except:
                        pass
                
                # Créer l'offre
                job = Job(
                    title=job_data.get('title', 'N/A'),
                    company=job_data.get('company'),
                    location=job_data.get('location'),
                    skills=job_data.get('skills'),
                    technologies=job_data.get('technologies'),
                    description_text=job_data.get('description_summary'),
                    salary=job_data.get('salary'),
                    date_posted=date_posted,
                    source_site=job_data.get('source', 'unknown'),
                    url_offre=job_data.get('url'),
                    date_scraped=datetime.now(),
                    is_new=True
                )
                
                db.session.add(job)
                added += 1
                
                # Commit par batch
                if added % 50 == 0:
                    db.session.commit()
                    print(f"  [{idx}/{len(jobs_data)}] ✅ {added} offres ajoutées, {skipped} doublons")
                
            except Exception as e:
                errors += 1
                print(f"  ❌ Erreur offre {idx}: {e}")
                db.session.rollback()
                continue
        
        # Commit final
        try:
            db.session.commit()
            print(f"\n✅ IMPORT TERMINÉ")
            print(f"   Ajoutées: {added}")
            print(f"   Doublons: {skipped}")
            print(f"   Erreurs: {errors}")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erreur commit final: {e}")
    
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_ai_data.py <fichier_json>")
        print("\nFichiers disponibles:")
        scraper_dir = os.path.dirname(os.path.abspath(__file__))
        for f in os.listdir(scraper_dir):
            if f.startswith('ai_scraped_jobs_') and f.endswith('.json'):
                print(f"  - {f}")
        sys.exit(1)
    
    json_file = sys.argv[1]
    if not os.path.isabs(json_file):
        json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), json_file)
    
    import_ai_data(json_file)
