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

    # Facebook Groups for scraping
    FB_GROUPS = [
        {
            'id': '250636145007603',
            'name': 'Real Estate Group 1',
            'url': 'https://www.facebook.com/groups/250636145007603/'
        },
        {
            'id': '226696460730867',
            'name': 'Real Estate Group 2',
            'url': 'https://www.facebook.com/groups/226696460730867'
        },
        {
            'id': '736463973967742',
            'name': 'Real Estate Group 3',
            'url': 'https://www.facebook.com/groups/736463973967742'
        },
        {
            'id': '920176614664761',
            'name': 'Real Estate Group 4',
            'url': 'https://www.facebook.com/groups/920176614664761'
        },
        {
            'id': '581262349259655',
            'name': 'Real Estate Group 5',
            'url': 'https://www.facebook.com/groups/581262349259655'
        },
        {
            'id': '1129392941752704',
            'name': 'Real Estate Group 6',
            'url': 'https://www.facebook.com/groups/1129392941752704'
        },
        {
            'id': '163283720393199',
            'name': 'Real Estate Group 7',
            'url': 'https://www.facebook.com/groups/163283720393199'
        },
        {
            'id': '2573303249362318',
            'name': 'Real Estate Group 8',
            'url': 'https://www.facebook.com/groups/2573303249362318'
        },
        {
            'id': '371598040003608',
            'name': 'Real Estate Group 9',
            'url': 'https://www.facebook.com/groups/371598040003608'
        },
        {
            'id': '1201360430008237',
            'name': 'Real Estate Group 10',
            'url': 'https://www.facebook.com/groups/1201360430008237'
        },
        {
            'id': '5437631259682377',
            'name': 'Real Estate Group 11',
            'url': 'https://www.facebook.com/groups/5437631259682377'
        },
        {
            'id': '396733623770714',
            'name': 'Real Estate Group 12',
            'url': 'https://www.facebook.com/groups/396733623770714'
        },
        {
            'id': '712708313030571',
            'name': 'Real Estate Group 13',
            'url': 'https://www.facebook.com/groups/712708313030571'
        },
        {
            'id': '456527333039080',
            'name': 'Real Estate Group 14',
            'url': 'https://www.facebook.com/groups/456527333039080'
        },
        {
            'id': '336105114889885',
            'name': 'Real Estate Group 15',
            'url': 'https://www.facebook.com/groups/336105114889885'
        },
        {
            'id': '175841076508597',
            'name': 'Real Estate Group 16',
            'url': 'https://www.facebook.com/groups/175841076508597'
        },
        {
            'id': '1811109765814622',
            'name': 'Real Estate Group 17',
            'url': 'https://www.facebook.com/groups/1811109765814622'
        },
        {
            'id': 'menivplus',
            'name': 'Meniv Plus',
            'url': 'https://www.facebook.com/menivplus'
        },
        {
            'id': 'rentrishonby',
            'name': 'Rent Rishon',
            'url': 'https://www.facebook.com/groups/rentrishonby'
        },
        {
            'id': '1711226185557597',
            'name': 'Real Estate Group 20',
            'url': 'https://www.facebook.com/groups/1711226185557597/'
        }
    ]

    # Facebook API configuration
    FB_ACCESS_TOKEN = os.environ.get('FB_ACCESS_TOKEN')
    FB_API_VERSION = 'v18.0'
    FB_POSTS_LIMIT = 5  # Number of recent posts to fetch per group
