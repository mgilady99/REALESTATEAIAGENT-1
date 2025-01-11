from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
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
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)

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

@app.route('/export')
def export_properties():
    """Export properties to CSV"""
    try:
        properties = Property.query.all()
        df = pd.DataFrame([{
            'title': p.title,
            'price': p.price,
            'location': p.location,
            'size': p.size,
            'url': p.url,
            'date_listed': p.date_listed,
            'date_scraped': p.date_scraped
        } for p in properties])
        
        csv_file = 'properties_export.csv'
        df.to_csv(csv_file, index=False)
        return send_file(csv_file, as_attachment=True)
    except Exception as e:
        logger.error(f"Error in export route: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/logs')
def view_logs():
    """View scraping logs"""
    try:
        logs = ScrapingLog.query.order_by(ScrapingLog.start_time.desc()).limit(100).all()
        return render_template('logs.html', logs=logs)
    except Exception as e:
        logger.error(f"Error in logs route: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/news')
def news():
    """Display real estate news"""
    try:
        # Get latest news articles
        news_articles = News.query.order_by(News.date_scraped.desc()).all()
        return render_template('news.html', articles=news_articles)
    except Exception as e:
        logger.error(f"Error in news route: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/urls', methods=['GET'])
def get_urls():
    """Get all scraping URLs"""
    try:
        urls = load_urls()
        return jsonify({
            'property_urls': urls.get('property_urls', []),
            'news_urls': urls.get('news_urls', [])
        })
    except Exception as e:
        logger.error(f"Error getting URLs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/scrape', methods=['POST'])
def scrape_properties():
    """Endpoint to trigger property scraping"""
    try:
        scraper = RealEstateScraper()
        urls = load_urls().get('property_urls', [])
        
        if not urls:
            return jsonify({
                'success': False,
                'message': 'No property URLs configured. Please add URLs in the URL manager.'
            })
        
        try:
            # Run synchronously instead of async
            properties = scraper.scrape_urls_sync(urls)
            
            if not properties:
                return jsonify({
                    'success': False,
                    'message': 'No properties found'
                })
            
            return jsonify({
                'success': True,
                'properties': properties
            })
        except Exception as e:
            logger.error(f"Error in property scraping: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Scraping error: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in scrape_properties endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Server error: {str(e)}"
        }), 500

@app.route('/scrape/news', methods=['POST'])
def scrape_news():
    """Endpoint to trigger news scraping"""
    try:
        news_scraper = NewsScraperService()
        urls = load_urls().get('news_urls', [])
        
        if not urls:
            return jsonify({
                'success': False,
                'message': 'No news URLs configured. Please add URLs in the URL manager.'
            })
        
        try:
            # Run synchronously
            news = news_scraper.scrape_news_sync(urls)
            
            if not news:
                return jsonify({
                    'success': False,
                    'message': 'No news found'
                })
            
            return jsonify({
                'success': True,
                'news': news
            })
        except Exception as e:
            logger.error(f"Error in news scraping: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Scraping error: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in scrape_news endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Server error: {str(e)}"
        }), 500

@app.route('/api/properties', methods=['GET'])
def get_properties():
    try:
        properties = Property.query.order_by(Property.date_scraped.desc()).limit(50).all()
        return jsonify({
            'success': True,
            'properties': [prop.to_dict() for prop in properties]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/news', methods=['GET'])
def get_news():
    try:
        news = News.query.order_by(News.date_scraped.desc()).limit(50).all()
        return jsonify({
            'success': True,
            'news': [article.to_dict() for article in news]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

URLS_FILE = 'scraping_urls.json'

def load_urls():
    try:
        if os.path.exists(URLS_FILE):
            with open(URLS_FILE, 'r') as f:
                return json.load(f)
        return {'property_urls': [], 'news_urls': []}
    except Exception as e:
        app.logger.error(f"Error loading URLs: {e}")
        return {'property_urls': [], 'news_urls': []}

def save_urls(urls):
    try:
        with open(URLS_FILE, 'w') as f:
            json.dump(urls, f)
        return True
    except Exception as e:
        app.logger.error(f"Error saving URLs: {e}")
        return False

if __name__ == '__main__':
    init_db()
    setup_scheduler()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
