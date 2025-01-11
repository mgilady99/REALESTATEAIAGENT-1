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
    
    # News URLs for scraping
    NEWS_URLS = {
        'globes': {
            'name': 'Globes',
            'url': 'https://www.globes.co.il/news/home.aspx?fid=607',
            'type': 'news',
            'language': 'hebrew'
        },
        'calcalist': {
            'name': 'Calcalist Real Estate',
            'url': 'https://www.calcalist.co.il/real-estate',
            'type': 'news',
            'language': 'hebrew'
        },
        'themarker': {
            'name': 'TheMarker Real Estate',
            'url': 'https://www.themarker.com/realestate',
            'type': 'news',
            'language': 'hebrew'
        },
        'bizportal': {
            'name': 'Bizportal Real Estate',
            'url': 'https://www.bizportal.co.il/realestates/news',
            'type': 'news',
            'language': 'hebrew'
        }
    }
    
    # Property listing URLs
    LISTING_URLS = [
        'https://www.globes.co.il/GlobesBoard/',
        'https://menivim.net/',
        'https://shorturl.at/Khx3S',  # Homeless Commercial
        'https://shorturl.at/5hMsS',  # Madlan Commercial
        'https://shorturl.at/0IBGQ',  # Yad2 Commercial Search
        'https://gevarom.co.il/properties/',
        'https://www.komo.co.il/'
    ]
    
    # Use environment URLs if provided, otherwise use defaults
    URLS = os.environ.get('URLS', '').split(',') if os.environ.get('URLS') else LISTING_URLS
    
    # Site-specific configurations for property listings
    SITE_CONFIGS = {
        'globes': {
            'name': 'Globes Board',
            'base_url': 'https://www.globes.co.il/GlobesBoard/',
            'type': 'commercial'
        },
        'menivim': {
            'name': 'Menivim',
            'base_url': 'https://menivim.net/',
            'type': 'commercial'
        },
        'homeless': {
            'name': 'Homeless Commercial',
            'base_url': 'https://shorturl.at/Khx3S',
            'type': 'commercial'
        },
        'madlan': {
            'name': 'Madlan Commercial',
            'base_url': 'https://shorturl.at/5hMsS',
            'type': 'commercial'
        },
        'yad2': {
            'name': 'Yad2 Commercial',
            'base_url': 'https://shorturl.at/0IBGQ',
            'type': 'commercial'
        },
        'gevarom': {
            'name': 'Geva Rom Commercial',
            'base_url': 'https://gevarom.co.il/properties/',
            'type': 'commercial'
        },
        'komo': {
            'name': 'Komo Board',
            'base_url': 'https://www.komo.co.il/',
            'type': 'commercial'
        }
    }
