"""
Script pour vérifier la distribution des villes dans la base de données
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Job
from sqlalchemy import func

with app.app_context():
    # Compter les villes
    city_stats = db.session.query(
        Job.location,
        func.count(Job.id).label('count')
    ).group_by(Job.location)\
     .order_by(func.count(Job.id).desc())\
     .limit(50)\
     .all()
    
    print(f"\n📍 Distribution des villes (Top 50):")
    print("=" * 60)
    for location, count in city_stats:
        print(f"  {location:30s} : {count:5d} offres")
    
    print(f"\n📊 Total de villes différentes: {db.session.query(func.count(func.distinct(Job.location))).scalar()}")
    
    # Compter "Maroc"
    maroc_count = db.session.query(func.count(Job.id)).filter(Job.location == 'Maroc').scalar()
    total_count = db.session.query(func.count(Job.id)).scalar()
    
    print(f"\n⚠️  Offres avec 'Maroc' générique: {maroc_count} / {total_count} ({maroc_count*100/total_count:.1f}%)")
