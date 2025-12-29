import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Job
from sqlalchemy import func
from datetime import datetime, timedelta

with app.app_context():
    # Statistiques générales
    total_jobs = db.session.query(func.count(Job.id)).scalar()
    print(f"\n📊 STATISTIQUES DES DATES")
    print("=" * 80)
    print(f"Total d'offres dans la BD: {total_jobs}")
    
    # Offres avec dates NULL
    null_dates = db.session.query(func.count(Job.id)).filter(Job.date_posted.is_(None)).scalar()
    print(f"\n⚠️  Offres sans date (NULL): {null_dates} ({null_dates/total_jobs*100:.1f}%)")
    
    # Distribution par date
    print(f"\n📅 DISTRIBUTION PAR DATE:")
    print("-" * 80)
    
    date_distribution = db.session.query(
        func.date(Job.date_posted).label('date'),
        func.count(Job.id).label('count')
    ).filter(Job.date_posted.isnot(None))\
     .group_by(func.date(Job.date_posted))\
     .order_by(func.date(Job.date_posted).desc())\
     .limit(30)\
     .all()
    
    for date, count in date_distribution:
        if date:
            days_ago = (datetime.now().date() - date).days
            print(f"{date} ({days_ago} jours): {count} offres")
    
    # Statistiques par période
    print(f"\n📈 STATISTIQUES PAR PÉRIODE:")
    print("-" * 80)
    
    now = datetime.now()
    
    # Dernières 24h
    last_24h = db.session.query(func.count(Job.id))\
        .filter(Job.date_posted >= now - timedelta(hours=24))\
        .scalar()
    print(f"Dernières 24h: {last_24h} offres")
    
    # Derniers 7 jours
    last_7d = db.session.query(func.count(Job.id))\
        .filter(Job.date_posted >= now - timedelta(days=7))\
        .scalar()
    print(f"Derniers 7 jours: {last_7d} offres")
    
    # Dernier mois
    last_30d = db.session.query(func.count(Job.id))\
        .filter(Job.date_posted >= now - timedelta(days=30))\
        .scalar()
    print(f"Dernier mois: {last_30d} offres")
    
    # Plus de 30 jours
    older_30d = db.session.query(func.count(Job.id))\
        .filter(Job.date_posted < now - timedelta(days=30))\
        .scalar()
    print(f"Plus de 30 jours: {older_30d} offres")
    
    # Date la plus ancienne et la plus récente
    print(f"\n📆 PLAGE DE DATES:")
    print("-" * 80)
    
    oldest = db.session.query(func.min(Job.date_posted)).filter(Job.date_posted.isnot(None)).scalar()
    newest = db.session.query(func.max(Job.date_posted)).filter(Job.date_posted.isnot(None)).scalar()
    
    if oldest:
        print(f"Date la plus ancienne: {oldest}")
    if newest:
        print(f"Date la plus récente: {newest}")
    
    # Exemples d'offres récentes
    print(f"\n🔍 EXEMPLES D'OFFRES RÉCENTES (10 dernières):")
    print("-" * 80)
    
    recent_jobs = db.session.query(Job)\
        .filter(Job.date_posted.isnot(None))\
        .order_by(Job.date_posted.desc())\
        .limit(10)\
        .all()
    
    for job in recent_jobs:
        days_ago = (datetime.now() - job.date_posted).days if job.date_posted else None
        print(f"{job.date_posted} ({days_ago}j) - {job.title[:50]} - {job.company} - {job.source_site}")
    
    print("\n" + "=" * 80)
