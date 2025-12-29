from app import app
from models import Job
from sqlalchemy import func

with app.app_context():
    print("Database check for Stagiaires.ma jobs:")
    count = Job.query.filter(Job.source_site == 'stagiaires.ma').count()
    print(f"Total jobs from stagiaires.ma: {count}")
    
    if count > 0:
        latest = Job.query.filter(Job.source_site == 'stagiaires.ma').order_by(Job.date_posted.desc()).first()
        print(f"Latest job: {latest.title} | Date: {latest.date_posted}")
        
        oldest = Job.query.filter(Job.source_site == 'stagiaires.ma').order_by(Job.date_posted.asc()).first()
        print(f"Oldest job: {oldest.title} | Date: {oldest.date_posted}")
        
        # Breakdown by month
        results = Job.query.with_entities(func.date_format(Job.date_posted, '%Y-%m'), func.count(Job.id))\
            .filter(Job.source_site == 'stagiaires.ma')\
            .group_by(func.date_format(Job.date_posted, '%Y-%m'))\
            .all()
        print("\nMonthly breakdown for Stagiaires.ma:")
        for res in results:
            print(f" - {res[0]}: {res[1]} jobs")
    else:
        print("No jobs found for stagiaires.ma in database.")
