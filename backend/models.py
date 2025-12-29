from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON

db = SQLAlchemy()

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255))
    location = db.Column(db.String(255), index=True)
    skills = db.Column(JSON)  # Utilise JSON natif MySQL
    technologies = db.Column(JSON)
    description_text = db.Column(db.Text)
    salary = db.Column(db.String(100))
    date_posted = db.Column(db.DateTime, index=True)
    source_site = db.Column(db.String(100))
    url_offre = db.Column(db.String(500), unique=True, nullable=False)
    date_scraped = db.Column(db.DateTime, default=datetime.utcnow)
    is_new = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'skills': self.skills,
            'technologies': self.technologies,
            'date_posted': self.date_posted.isoformat() if self.date_posted else None,
            'source_site': self.source_site,
            'url_offre': self.url_offre,
            'salaire': self.salary
        }

class ScrapingLog(db.Model):
    __tablename__ = 'scraping_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    jobs_found = db.Column(db.Integer, default=0)
    jobs_added = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='running') # running, success, failed
    error_message = db.Column(db.Text)

class TechnologyStat(db.Model):
    __tablename__ = 'technologies_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    technology = db.Column(db.String(100), index=True)
    count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class CompetenceStat(db.Model):
    __tablename__ = 'competences_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    competence = db.Column(db.String(100), index=True)
    count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
