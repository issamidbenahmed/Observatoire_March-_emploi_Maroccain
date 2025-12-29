import os
from flask import Flask
from flask_cors import CORS
from config import Config
from models import db
from routes import api

from flask_apscheduler import APScheduler
import subprocess
import threading
import time

scheduler = APScheduler()

def run_scraper_task():
    """Exécute le script de scraping en arrière-plan"""
    try:
        print(f"🔄 Lancement du scraping automatique : {time.ctime()}")
        # Exécuter run_scrapers.py comme un sous-processus pour éviter les conflits d'event loop async
        # Assumant que le script est dans backend/scraper/run_scrapers.py
        scraper_path = os.path.join(os.path.dirname(__file__), 'scraper', 'run_scrapers.py')
        # Ne pas capturer la sortie pour qu'elle s'affiche dans le terminal du backend
        result = subprocess.run(['python', '-u', scraper_path])
        
        if result.returncode == 0:
            print("✅ Scraping terminé avec succès")
        else:
            print("❌ Erreur lors du scraping (voir logs ci-dessus)")
    except Exception as e:
        print(f"❌ Exception tache scraping: {e}")

def create_app(with_scheduler=True):
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configurer APScheduler
    app.config['SCHEDULER_API_ENABLED'] = True
    
    # Initialize Extensions
    CORS(app) # Allow frontend to communicate
    db.init_app(app)
    
    if with_scheduler:
        try:
            scheduler.init_app(app)
        except Exception as e:
            print(f"⚠️ Scheduler init skipped: {e}")
    
    # Register Blueprints
    app.register_blueprint(api, url_prefix='/api')
    
    with app.app_context():
        # Create Tables if not exist
        db.create_all()
        
    if with_scheduler:
        # Programmer le job récurrent (toutes les 1 heures)
        # id permet de ne pas le dupliquer si on reload
        try:
            scheduler.add_job(id='scraping_job', func=run_scraper_task, trigger='interval', hours=1, replace_existing=True)
            
            if not scheduler.running:
                scheduler.start()
        except Exception as e:
            print(f"⚠️ Scheduler start skipped: {e}")
    
    return app

app = create_app()

if __name__ == '__main__':
    # Lancer un premier scraping au démarrage dans un thread séparé
    print("🚀 Démarrage du scraping initial...")
    threading.Thread(target=run_scraper_task).start()
    app.run(debug=True, port=int(os.getenv('PORT', 5000)), use_reloader=False) # use_reloader=False évite les doublons de scheduler avec le debug mode
