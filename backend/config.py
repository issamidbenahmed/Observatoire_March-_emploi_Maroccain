import os

class Config:
    # Database Configuration
    # Replace with your actual MySQL credentials or use environment variables
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost/observatoire_emploi')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    
    # Scraper Configuration
    SCRAPER_HEADLESS = True
    SCRAPER_DELAY_MIN = 1
    SCRAPER_DELAY_MAX = 4
