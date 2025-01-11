import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-12345'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google Sheets configuration
    GOOGLE_SHEETS_CREDENTIALS = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
    SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
    
    # Email configuration
    EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    EMAIL_RECIPIENTS = os.environ.get('EMAIL_RECIPIENTS', '').split(',')
    
    # Scraping configuration
    SCRAPING_INTERVAL = int(os.environ.get('SCRAPING_INTERVAL', 3600))  # Default: 1 hour
    KEYWORDS = os.environ.get('KEYWORDS', '').split(',')
    URLS = os.environ.get('URLS', '').split(',')
