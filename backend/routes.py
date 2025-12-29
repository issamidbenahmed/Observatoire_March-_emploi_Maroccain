from flask import Blueprint, jsonify, request
from sqlalchemy import func, desc
from models import db, Job, TechnologyStat, CompetenceStat, ScrapingLog
import datetime

api = Blueprint('api', __name__)

@api.route('/jobs', methods=['GET'])
def get_jobs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filters
    city = request.args.get('city')
    company = request.args.get('company')
    tech = request.args.get('tech')
    
    query = Job.query
    
    if city:
        query = query.filter(Job.location.ilike(f'%{city}%'))
    if company:
        query = query.filter(Job.company.ilike(f'%{company}%'))
    if tech:
        # Recherche dans le tableau JSON des technologies
        # Utilise JSON_CONTAINS pour MySQL qui cherche une valeur exacte dans un tableau JSON
        query = query.filter(Job.technologies.cast(db.String).ilike(f'%"{tech}"%'))

    pagination = query.order_by(Job.date_posted.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'jobs': [job.to_dict() for job in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@api.route('/jobs/<int:id>', methods=['GET'])
def get_job_detail(id):
    job = Job.query.get_or_404(id)
    return jsonify(job.to_dict())

@api.route('/stats/technologies', methods=['GET'])
def get_tech_stats():
    # Top 50 technologies
    stats = TechnologyStat.query.order_by(TechnologyStat.count.desc()).limit(50).all()
    return jsonify([{'name': s.technology, 'count': s.count} for s in stats])

@api.route('/stats/competences', methods=['GET'])
def get_comp_stats():
    stats = CompetenceStat.query.order_by(CompetenceStat.count.desc()).limit(50).all()
    return jsonify([{'name': s.competence, 'count': s.count} for s in stats])

@api.route('/stats/regions', methods=['GET'])
def get_region_stats():
    # Aggregation on the fly or pre-calculated
    # Exclure "Maroc" qui est trop générique
    results = db.session.query(Job.location, func.count(Job.id))\
        .filter(Job.location != 'Maroc')\
        .group_by(Job.location)\
        .order_by(func.count(Job.id).desc())\
        .limit(20)\
        .all()
    return jsonify([{'name': r[0], 'count': r[1]} for r in results])

@api.route('/stats/global', methods=['GET'])
def get_global_stats():
    total_jobs = Job.query.count()
    try:
        total_companies = db.session.query(func.count(func.distinct(Job.company))).scalar()
    except Exception:
        total_companies = 0
        
    latest_update = db.session.query(func.max(Job.date_scraped)).scalar()
    
    # Calculer les nouveaux jobs dans les dernières 24h
    twenty_four_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    new_jobs_24h = Job.query.filter(Job.date_scraped >= twenty_four_hours_ago).count()
    
    return jsonify({
        'total_jobs': total_jobs,
        'total_companies': total_companies,
        'last_update': latest_update.isoformat() if latest_update else None,
        'new_jobs_24h': new_jobs_24h
    })

@api.route('/stats/companies', methods=['GET'])
def get_company_stats():
    # Top 20 Companies
    # Exclude "Non spécifié" and "Anonyme" if possible, or handle on frontend
    results = db.session.query(Job.company, func.count(Job.id)).filter(Job.company != 'Non spécifié').group_by(Job.company).order_by(func.count(Job.id).desc()).limit(20).all()
    return jsonify([{'name': r[0], 'count': r[1]} for r in results])

@api.route('/stats/sources', methods=['GET'])
def get_source_stats():
    # Job distribution by source site
    results = db.session.query(Job.source_site, func.count(Job.id)).group_by(Job.source_site).order_by(func.count(Job.id).desc()).all()
    return jsonify([{'name': r[0], 'count': r[1]} for r in results])

@api.route('/stats/history/jobs', methods=['GET'])
def get_jobs_history():
    # Jobs per month (Jan 2024+)
    # MySQL: DATE_FORMAT(date_posted, '%Y-%m')
    start_date = datetime.datetime(2024, 1, 1)
    
    # SQLite fallback syntax just in case (strftime), but user seems to use MySQL based on models.py
    # Assuming MySQL based on `from sqlalchemy.dialects.mysql import JSON` in models.py
    
    results = db.session.query(
        func.date_format(Job.date_posted, '%Y-%m').label('month'),
        func.count(Job.id)
    ).filter(Job.date_posted >= start_date)\
     .group_by('month')\
     .order_by('month')\
     .all()
     
    return jsonify([{'month': r[0], 'count': r[1]} for r in results])

@api.route('/stats/history/technologies', methods=['GET'])
def get_tech_history():
    # Top technologies per month
    # This is heavy. Let's simplify: Return global top 10 techs, broken down by month.
    
    start_date = datetime.datetime(2024, 1, 1)
    
    # 1. Get Top 10 Techs global
    top_techs = db.session.query(TechnologyStat.technology)\
        .order_by(TechnologyStat.count.desc())\
        .limit(50)\
        .all()
    tech_names = [t[0] for t in top_techs]
    
    # 2. For each month, count these techs
    # Since technologies is a JSON array, we need to be careful.
    # We'll fetch all jobs > Jan 2024 and process in Python (safer than complex JSON SQL queries for now)
    
    jobs = Job.query.filter(Job.date_posted >= start_date).all()
    
    history = {} # {'2024-01': {'Java': 10, 'Python': 5}}
    
    for job in jobs:
        if not job.date_posted: continue
        month = job.date_posted.strftime('%Y-%m')
        if month not in history:
            history[month] = {t: 0 for t in tech_names}
            
        if job.technologies:
            for tech in job.technologies:
                # Normalisation simple
                tech_clean = tech.strip()
                # Check if this tech is in our top 10 (fuzzy match could be better but kept simple)
                # We do exact match against our top 10 list for now
                if tech_clean in tech_names:
                    history[month][tech_clean] += 1
                    
    # Format for recharts: [{'month': '2024-01', 'Java': 10, 'Python': 5}, ...]
    formatted_data = []
    for month in sorted(history.keys()):
        item = {'month': month}
        item.update(history[month])
        formatted_data.append(item)
        
    return jsonify(formatted_data)

@api.route('/stats/history/evolution', methods=['GET'])
def get_tech_evolution():
    # Evolution of specific technologies over time (Line Chart)
    # Similar logic to above but maybe for all techs or user selected?
    # Actually, the frontend Recharts can just take the data from get_tech_history and display lines.
    # We can reuse the same endpoint or make this one return longer history or more techs.
    
    # Let's return the same data structure but maybe for top 20 to allow more selection
    return get_tech_history() # Reuse for now


import csv
import io
from flask import Response, stream_with_context

@api.route('/jobs/export', methods=['GET'])
def export_jobs():
    def generate():
        data = io.StringIO()
        w = csv.writer(data)
        
        # Header
        w.writerow(('Titre', 'Entreprise', 'Ville', 'Source', 'Date Publication', 'URL', 'Technologies', 'Compétences'))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        # Query all jobs (or filtered via query params if needed later)
        # For performance on large DB, use yield_per
        jobs_query = Job.query.order_by(Job.date_posted.desc()).yield_per(100)
        
        for job in jobs_query:
            techs = ", ".join(job.technologies) if job.technologies else ""
            skills = ", ".join(job.skills) if job.skills else ""
            
            w.writerow((
                job.title,
                job.company,
                job.location,
                job.source_site,
                job.date_posted.isoformat() if job.date_posted else "",
                job.url_offre,
                techs,
                skills
            ))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(stream_with_context(generate()), mimetype='text/csv')
    response.headers.set('Content-Disposition', 'attachment', filename='jobs_export.csv')
    return response

# Existing scraping routes...
import threading
import subprocess
import os

def run_scraper_subprocess():
    """Fonction helper pour lancer le process scraper"""
    try:
        # Chemin vers run_scrapers.py
        scraper_path = os.path.join(os.path.dirname(__file__), 'scraper', 'run_scrapers.py')
        print(f"🚀 Lancement manuel du scraping via: {scraper_path}")
        subprocess.run(['python', scraper_path])
        print("✅ Scraping manuel terminé")
    except Exception as e:
        print(f"❌ Erreur scraping manuel: {e}")

def run_enhanced_scraper_subprocess():
    """Fonction helper pour lancer le scrapeur historique"""
    try:
        scraper_path = os.path.join(os.path.dirname(__file__), 'scraper', 'enhanced_scraper.py')
        print(f"🚀 Lancement du scraping HISTORIQUE via: {scraper_path}")
        subprocess.run(['python', scraper_path])
        print("✅ Scraping historique terminé")
    except Exception as e:
        print(f"❌ Erreur scraping historique: {e}")


@api.route('/sync/run', methods=['POST'])
def run_sync():
    # Lancer le scraping dans un thread séparé pour ne pas bloquer la réponse HTTP
    thread = threading.Thread(target=run_scraper_subprocess)
    thread.start()
    
    return jsonify({'status': 'started', 'message': 'Scraping lancé en arrière-plan'})

@api.route('/sync/enhanced', methods=['POST'])
def run_sync_enhanced():
    thread = threading.Thread(target=run_enhanced_scraper_subprocess)
    thread.start()
    return jsonify({'status': 'started', 'message': 'Scraping Historique lancé en arrière-plan'})


@api.route('/sync/status', methods=['GET'])
def get_sync_status():
    latest_log = ScrapingLog.query.order_by(ScrapingLog.start_time.desc()).first()
    if not latest_log:
        return jsonify({'status': 'never_run'})
    
    return jsonify({
        'status': latest_log.status,
        'last_run': latest_log.start_time.isoformat(),
        'jobs_added': latest_log.jobs_added
    })
