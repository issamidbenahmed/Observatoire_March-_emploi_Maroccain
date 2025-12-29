import re
import json
import requests
from datetime import datetime
import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, Job, ScrapingLog, TechnologyStat, CompetenceStat
from app import create_app

class DataPipeline:
    def __init__(self):
        self.app = create_app(with_scheduler=False)
        self.new_jobs_count = 0

    def is_duplicate(self, url):
        with self.app.app_context():
            exists = Job.query.filter_by(url_offre=url).first()
            return exists is not None

    def extract_details(self, text):
        """Extraction améliorée des technologies et compétences"""
        # Liste étendue de technologies
        technologies = [
            # Langages
            'Python', 'Java', 'JavaScript', 'TypeScript', 'PHP', 'C#', 'C++', 'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin', 'Scala', 'R', 'Dart', 'Lua', 'Perl', 'Bash', 'PowerShell',
            # Frontend
            'React', 'Angular', 'Vue.js', 'Next.js', 'Nuxt.js', 'Svelte', 'jQuery', 'Bootstrap', 'Tailwind', 'Material UI', 'HTML5', 'CSS3', 'Sass', 'Webpack', 'Vite',
            # Backend
            'Node.js', 'Django', 'Flask', 'FastAPI', 'Spring Boot', 'Laravel', 'Symfony', 'Express.js', 'NestJS', 'ASP.NET Core', 'Ruby on Rails', 'GraphQL', 'REST API', 'gRPC',
            # Mobile
            'React Native', 'Flutter', 'Android', 'iOS', 'Xamarin', 'Ionic', 'Expo', 'SwiftUI',
            # Data & AI
            'Machine Learning', 'Deep Learning', 'Data Science', 'Big Data', 'AI', 'NLP', 'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn', 'Pandas', 'NumPy', 'Hadoop', 'Spark', 'Kafka', 'Airflow', 'Snowflake', 'Databricks', 'Power BI', 'Tableau',
            # DevOps & Cloud
            'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins', 'GitLab CI', 'GitHub Actions', 'CircleCI', 'Terraform', 'Ansible', 'Prometheus', 'Grafana', 'ELK Stack', 'Linux', 'Nginx', 'Apache',
            # Database
            'MySQL', 'PostgreSQL', 'MongoDB', 'Oracle', 'SQL Server', 'Redis', 'Elasticsearch', 'Cassandra', 'DynamoDB', 'MariaDB', 'SQLite', 'Firebase', 'Supabase',
            # Security & Others
            'Cybersecurity', 'Blockchain', 'IoT', 'Salesforce', 'SAP', 'Odoo', 'WordPress', 'Shopify', 'Jira', 'Confluence', 'Agile', 'Scrum'
        ]
        
        # Liste étendue de compétences
        skills = [
            # Soft skills
            'Communication', 'Leadership', 'Travail équipe', 'Autonomie', 'Rigueur', 'Dynamisme',
            'Créativité', 'Organisation', 'Gestion temps', 'Adaptabilité', 'Problem solving',
            # Langues
            'Anglais', 'Français', 'Arabe', 'Espagnol', 'Allemand',
            # Méthodologies
            'Agile', 'Scrum', 'Kanban', 'Management', 'Gestion projet', 'Analyse',
            # Techniques
            'Comptabilité', 'Marketing', 'Commercial', 'Vente', 'Négociation', 'Service client',
            'RH', 'Finance', 'Logistique', 'Maintenance', 'Qualité', 'HSE', 'BTP'
        ]
        
        # Recherche insensible à la casse
        found_tech = list(set([t for t in technologies if re.search(r'\b' + re.escape(t) + r'\b', text, re.IGNORECASE)]))
        found_skills = list(set([s for s in skills if re.search(r'\b' + re.escape(s) + r'\b', text, re.IGNORECASE)]))
        
        return found_tech, found_skills

    def save_job(self, job_data):
        if self.is_duplicate(job_data['url']):
            return  # Silent skip for known duplicates

        with self.app.app_context():
            try:
                # Combiner titre + description + company pour meilleure extraction
                full_text = f"{job_data['title']} {job_data.get('description', '')} {job_data.get('company', '')}"
                techs, skills = self.extract_details(full_text)
                
                new_job = Job(
                    title=job_data['title'],
                    company=job_data.get('company', 'Non spécifié'),
                    location=job_data.get('location', 'Maroc'),
                    description_text=job_data.get('description', ''),
                    url_offre=job_data['url'],
                    source_site=job_data['source'],
                    date_posted=job_data.get('date_posted', datetime.utcnow()),
                    technologies=techs,
                    skills=skills
                )
                
                db.session.add(new_job)
                
                # Update Stats
                for t in techs:
                    stat = TechnologyStat.query.filter_by(technology=t).first()
                    if not stat:
                        stat = TechnologyStat(technology=t, count=0)
                        db.session.add(stat)
                    stat.count += 1
                    stat.last_updated = datetime.utcnow()

                for s in skills:
                    stat = CompetenceStat.query.filter_by(competence=s).first()
                    if not stat:
                        stat = CompetenceStat(competence=s, count=0)
                        db.session.add(stat)
                    stat.count += 1
                    stat.last_updated = datetime.utcnow()

                db.session.commit()
                self.new_jobs_count += 1
                self.notify_if_needed(new_job)
            except Exception as e:
                db.session.rollback()
                # Check if it's a duplicate entry error (IntegrityError)
                if 'Duplicate entry' in str(e) or 'IntegrityError' in str(type(e).__name__):
                    # Silently skip duplicates caught at DB level
                    return
                else:
                    # Re-raise other errors
                    print(f"   ⚠️ Erreur sauvegarde: {e}")
                    raise

    def notify_if_needed(self, job):
        # Placeholder for notification logic
        # requests.post('webhook_url', json=job.to_dict())
        print(f"New Job Notification: {job.title} at {job.company}")

    def log_run(self, status, error=None):
        with self.app.app_context():
            log = ScrapingLog(
                status=status,
                jobs_added=self.new_jobs_count,
                error_message=str(error) if error else None,
                end_time=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
