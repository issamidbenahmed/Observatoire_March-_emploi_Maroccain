"""
Script pour vérifier les données historiques dans la base de données
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Job
from sqlalchemy import func
from datetime import datetime

with app.app_context():
    # Compter le total d'offres
    total_jobs = db.session.query(func.count(Job.id)).scalar()
    print(f"\n📊 Total d'offres dans la base: {total_jobs}")
    
    # Compter par mois
    results = db.session.query(
        func.date_format(Job.date_posted, '%Y-%m').label('month'),
        func.count(Job.id)
    ).group_by('month')\
     .order_by('month')\
     .all()
    
    print(f"\n📅 Répartition par mois:")
    print("-" * 40)
    for month, count in results:
        print(f"  {month}: {count} offres")
    
    # Date la plus ancienne
    oldest = db.session.query(func.min(Job.date_posted)).scalar()
    newest = db.session.query(func.max(Job.date_posted)).scalar()
    
    print(f"\n📆 Période couverte:")
    print(f"  Plus ancienne: {oldest}")
    print(f"  Plus récente: {newest}")
    
    # Vérifier janvier 2024
    jan_2024 = db.session.query(func.count(Job.id))\
        .filter(Job.date_posted >= datetime(2024, 1, 1))\
        .filter(Job.date_posted < datetime(2024, 2, 1))\
        .scalar()
    
    print(f"\n🎯 Janvier 2024: {jan_2024} offres")
    
    if jan_2024 == 0:
        print("\n⚠️  PROBLÈME: Aucune donnée pour janvier 2024!")
        print("   → Lancez le scraping historique depuis l'interface")
    elif len(results) < 12:
        print(f"\n⚠️  ATTENTION: Seulement {len(results)} mois de données")
        print("   → Lancez le scraping historique pour compléter")
    else:
        print("\n✅ Données historiques complètes!")
