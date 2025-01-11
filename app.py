from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import json
from scraper import RealEstateScraper
from models import db, Property, SearchCriteria, ScrapingLog
from sheets_handler import GoogleSheetsHandler
import pandas as pd
from config import Config
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)

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
        # Get URLs from config
        urls = app.config.get('URLS', [])
        if urls and urls[0]:  # Check if URLs list is not empty and first item is not empty
            asyncio.run(scraper.scrape_urls(urls))
        logger.info("Scraper started successfully")
    except Exception as e:
        logger.error(f"Error starting scraper: {str(e)}")

def setup_scheduler():
    """Setup scheduled tasks"""
    try:
        scheduler = BackgroundScheduler()
        interval = app.config.get('SCRAPING_INTERVAL', 3600)  # Default to 1 hour
        scheduler.add_job(start_scraper, 'interval', seconds=interval)
        scheduler.start()
        logger.info(f"Scheduler started with interval: {interval} seconds")
    except Exception as e:
        logger.error(f"Error setting up scheduler: {str(e)}")

@app.route('/')
def home():
    """Home page"""
    try:
        properties = Property.query.order_by(Property.date_scraped.desc()).limit(10).all()
        return render_template('index.html', properties=properties)
    except Exception as e:
        logger.error(f"Error in home route: {str(e)}")
        return "Internal Server Error", 500

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
        return "Internal Server Error", 500

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
        return "Internal Server Error", 500

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
        return "Internal Server Error", 500

@app.route('/logs')
def view_logs():
    """View scraping logs"""
    try:
        logs = ScrapingLog.query.order_by(ScrapingLog.start_time.desc()).limit(100).all()
        return render_template('logs.html', logs=logs)
    except Exception as e:
        logger.error(f"Error in logs route: {str(e)}")
        return "Internal Server Error", 500

if __name__ == '__main__':
    init_db()
    setup_scheduler()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
