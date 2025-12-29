"""
Script pour nettoyer et normaliser les villes dans la base de données existante
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Job
import re

# Copier la fonction clean_location améliorée
MOROCCAN_CITIES = {
    'casablanca', 'rabat', 'fes', 'fès', 'marrakech', 'tanger', 'agadir', 'meknes', 'meknès',
    'oujda', 'kenitra', 'kénitra', 'tetouan', 'tétouan', 'safi', 'temara', 'mohammedia',
    'khouribga', 'beni mellal', 'béni mellal', 'el jadida', 'nador', 'taza', 'settat',
    'laayoune', 'laâyoune', 'khemisset', 'khmisset', 'berkane', 'taourirt', 'ksar el kebir',
    'larache', 'guelmim', 'berrechid', 'errachidia', 'ouarzazate', 'tiznit', 'tan-tan',
    'essaouira', 'dakhla', 'sidi kacem', 'sidi slimane', 'youssoufia', 'sefrou',
    'ain chock', 'ain sebaa', 'anfa', 'hay hassani', 'hay mohammadi', 'sidi maarouf',
    'sidi moumen', 'maarif', 'gauthier', 'bourgogne', 'californie', 'oulfa',
    'derb sultan', 'roches noires', 'ain diab', 'bouskoura', 'nouaceur',
    'agdal', 'hay riad', 'souissi', 'hassan', 'ocean', 'aviation', 'akkari',
    'grand casablanca', 'casablanca settat', 'rabat sale kenitra', 'rabat salé kénitra',
    'fes meknes', 'fès meknès', 'marrakech safi', 'tanger tetouan', 'tanger tétouan',
    'oriental', 'souss massa', 'draa tafilalet', 'beni mellal khenifra',
    'el kelaa', 'el kelaa des sraghna', 'sidi bennour', 'azrou', 'ifrane', 'midelt',
    'sale', 'salé', 'jadida', 'mohammadia', 'benslimane', 'mediouna', 'nouasseur'
}

def clean_location(loc_str):
    """Nettoie et extrait intelligemment le nom de la ville"""
    if not loc_str: 
        return "Maroc"
    
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
    
    loc_lower = loc_str.lower()
    
    # Essayer de matcher une ville exacte d'abord
    for city in MOROCCAN_CITIES:
        if city == loc_lower:
            return city.title()
    
    # Essayer de trouver une ville dans la chaîne
    for city in sorted(MOROCCAN_CITIES, key=len, reverse=True):
        if city in loc_lower:
            pattern = r'\b' + re.escape(city) + r'\b'
            if re.search(pattern, loc_lower):
                return city.title()
    
    if len(loc_str) < 30 and not any(word in loc_lower for word in ['maroc', 'morocco', 'tout', 'national']):
        return ' '.join(word.capitalize() for word in loc_str.split())
    
    return "Maroc"

with app.app_context():
    print("\n🔧 Nettoyage des villes dans la base de données...")
    print("=" * 60)
    
    # Récupérer toutes les offres
    jobs = Job.query.all()
    updated = 0
    
    for job in jobs:
        old_location = job.location
        new_location = clean_location(old_location)
        
        if old_location != new_location:
            job.location = new_location
            updated += 1
            if updated <= 20:  # Afficher les 20 premiers changements
                print(f"  '{old_location}' → '{new_location}'")
    
    # Sauvegarder
    db.session.commit()
    
    print(f"\n✅ {updated} villes normalisées sur {len(jobs)} offres")
    
    # Afficher les nouvelles stats
    from sqlalchemy import func
    city_stats = db.session.query(
        Job.location,
        func.count(Job.id).label('count')
    ).group_by(Job.location)\
     .order_by(func.count(Job.id).desc())\
     .limit(20)\
     .all()
    
    print(f"\n📍 Top 20 villes après nettoyage:")
    print("=" * 60)
    for location, count in city_stats:
        print(f"  {location:30s} : {count:5d} offres")
    
    maroc_count = db.session.query(func.count(Job.id)).filter(Job.location == 'Maroc').scalar()
    total_count = db.session.query(func.count(Job.id)).scalar()
    print(f"\n📊 Offres 'Maroc' générique: {maroc_count} / {total_count} ({maroc_count*100/total_count:.1f}%)")
