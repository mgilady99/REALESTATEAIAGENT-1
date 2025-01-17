from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import json
from scraper import RealEstateScraper
from news_scraper import NewsScraperService
from models import db, Property, SearchCriteria, ScrapingLog, News
from sheets_handler import GoogleSheetsHandler
import pandas as pd
from config import Config
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)

# Initialize Migrate with the app and db object
migrate = Migrate(app, db)

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Create the database file if it doesn't exist
with app.app_context():
    if not os.path.exists('app.db'):
        db.create_all()
        logger.info("Database created successfully")

def init_db():
    """Initialize database"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

def start_scraper():
    """Initialize and start the scraper"""
    try:
        scraper = RealEstateScraper()
        urls = app.config.get('PROPERTY_URLS', [])
        if urls and urls[0]:  # Check if URLs list is not empty and first item is not empty
            asyncio.run(scraper.scrape_urls(urls))
        logger.info("Property scraper started successfully")
    except Exception as e:
        logger.error(f"Error starting property scraper: {str(e)}")

def start_news_scraper():
    """Initialize and start the news scraper"""
    try:
        news_scraper = NewsScraperService()
        urls = app.config.get('NEWS_URLS', [])
        news_scraper.scrape_news(urls)
        logger.info("News scraper started successfully")
    except Exception as e:
        logger.error(f"Error starting news scraper: {str(e)}")

def setup_scheduler():
    """Setup scheduled tasks"""
    try:
        scheduler = BackgroundScheduler()
        
        # Schedule property scraping
        property_interval = app.config.get('SCRAPING_INTERVAL', 3600)  # Default to 1 hour
        scheduler.add_job(start_scraper, 'interval', seconds=property_interval)
        
        # Schedule news scraping (every 30 minutes)
        news_interval = 1800  # 30 minutes
        scheduler.add_job(start_news_scraper, 'interval', seconds=news_interval)
        
        scheduler.start()
        logger.info(f"Scheduler started with property interval: {property_interval}s, news interval: {news_interval}s")
    except Exception as e:
        logger.error(f"Error setting up scheduler: {str(e)}")

@app.route('/')
def home():
    """Home page"""
    try:
        # Return empty list if no properties yet
        properties = Property.query.order_by(Property.date_scraped.desc()).limit(10).all() or []
        return render_template('index.html', properties=properties)
    except Exception as e:
        logger.error(f"Error in home route: {str(e)}")
        return render_template('error.html', error="Database initialization in progress. Please try again in a few moments."), 500

@app.route('/properties')
def properties():
    """List properties"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        properties = Property.query.order_by(Property.date_scraped.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        return render_template('properties.html', properties=properties)
    except Exception as e:
        logger.error(f"Error in properties route: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/search-criteria', methods=['GET', 'POST'])
def search_criteria():
    """Manage search criteria"""
    try:
        if request.method == 'POST':
            data = request.form
            criteria = SearchCriteria(
                name=data.get('name'),
                min_price=float(data.get('min_price', 0)),
                max_price=float(data.get('max_price', 0)),
                locations=data.get('locations'),
                keywords=data.get('keywords'),
                is_active=bool(data.get('is_active')),
                notification_email=data.get('notification_email')
            )
            db.session.add(criteria)
            db.session.commit()
            return redirect(url_for('search_criteria'))
        
        criteria_list = SearchCriteria.query.all()
        return render_template('search_criteria.html', criteria=criteria_list)
    except Exception as e:
        logger.error(f"Error in search_criteria route: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/properties')
def api_properties():
    """API endpoint for properties"""
    try:
        properties = Property.query.order_by(Property.date_scraped.desc()).limit(50).all()
        return jsonify({
            'status': 'success',
            'properties': [{
                'title': p.title,
                'price': p.price,
                'location': p.location,
                'url': p.url,
                'date_listed': p.date_listed.isoformat() if p.date_listed else None
            } for p in properties]
        })
    except Exception as e:
        logger.error(f"Error in api_properties route: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/scrape', methods=['POST'])
async def scrape_properties():
    """Endpoint to trigger property scraping"""
    try:
        urls = load_urls()
        property_urls = urls.get('property_urls', [])
        
        if not property_urls:
            return jsonify({
                'success': False,
                'message': 'No property URLs configured. Please add URLs in the URL manager.'
            })
        
        scraper = RealEstateScraper()
        properties = await scraper.scrape_urls(property_urls)
        
        return jsonify({
            'success': True,
            'properties': properties
        })
        
    except Exception as e:
        app.logger.error(f"Error in scrape_properties: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/scrape/news', methods=['POST'])
async def scrape_news():
    """Endpoint to trigger news scraping"""
    try:
        urls = load_urls()
        news_urls = urls.get('news_urls', [])
        
        if not news_urls:
            return jsonify({
                'success': False,
                'message': 'No news URLs configured. Please add URLs in the URL manager.'
            })
        
        news_scraper = NewsScraperService()
        news_articles = await news_scraper.scrape_news(news_urls)
        
        return jsonify({
            'success': True,
            'news': news_articles
        })
        
    except Exception as e:
        app.logger.error(f"Error in scrape_news: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        })

# Add URLs you provided
app.config['PROPERTY_URLS'] = [
    "https://www.globes.co.il/GlobesBoard/",
    "https://menivim.net/",
    "https://shorturl.at/Khx3S",
    "https://shorturl.at/5hMsS",
    "https://shorturl.at/0IBGQ",
    "https://gevarom.co.il/properties/",
    "https://www.komo.co.il/"
]

# URL loading and saving helper functions
def load_urls():
    try:
        if os.path.exists('scraping_urls.json'):
            with open('scraping_urls.json', 'r') as f:
                return json.load(f)
        return {'property_urls': [], 'news_urls': []}
    except Exception as e:
        app.logger.error(f"Error loading URLs: {e}")
        return {'property_urls': [], 'news_urls': []}

def save_urls(urls):
    try:
        with open('scraping_urls.json', 'w') as f:
            json.dump(urls, f)
        return True
    except Exception as e:
        app.logger.error(f"Error saving URLs: {e}")
        return False

# Run the application
if __name__ == '__main__':
    init_db()
    setup_scheduler()
    app.run(host='0.0.0.0', port=3001)  # Changed port to 3001
