import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from models import db, Property, ScrapingLog
from flask import current_app
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealEstateScraper:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def create_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    def clean_text(self, text):
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())

    def extract_price(self, text):
        if not text:
            return None
        price_match = re.search(r'[\d,]+', text)
        if price_match:
            return int(price_match.group().replace(',', ''))
        return None

    async def scrape_url(self, url):
        try:
            site_key = next((key for key, config in current_app.config['SITE_CONFIGS'].items() 
                           if config['base_url'] in url), None)
            
            if not site_key:
                logger.warning(f"No configuration found for URL: {url}")
                return []

            session = await self.create_session()
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch {url}: {response.status}")
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                properties = []
                
                if site_key == 'globes':
                    properties = await self.parse_globes(soup)
                elif site_key == 'menivim':
                    properties = await self.parse_menivim(soup)
                elif site_key == 'homeless':
                    properties = await self.parse_homeless(soup)
                elif site_key == 'madlan':
                    properties = await self.parse_madlan(soup)
                elif site_key == 'yad2':
                    properties = await self.parse_yad2(soup)
                elif site_key == 'gevarom':
                    properties = await self.parse_gevarom(soup)
                elif site_key == 'komo':
                    properties = await self.parse_komo(soup)
                
                return properties

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return []

    async def parse_globes(self, soup):
        properties = []
        # Add specific parsing logic for Globes
        return properties

    async def parse_menivim(self, soup):
        properties = []
        # Add specific parsing logic for Menivim
        return properties

    async def parse_homeless(self, soup):
        properties = []
        # Add specific parsing logic for Homeless
        return properties

    async def parse_madlan(self, soup):
        properties = []
        # Add specific parsing logic for Madlan
        return properties

    async def parse_yad2(self, soup):
        properties = []
        # Add specific parsing logic for Yad2
        return properties

    async def parse_gevarom(self, soup):
        properties = []
        # Add specific parsing logic for Geva Rom
        return properties

    async def parse_komo(self, soup):
        properties = []
        # Add specific parsing logic for Komo
        return properties

    async def scrape_urls(self, urls):
        log = ScrapingLog(start_time=datetime.utcnow())
        try:
            all_properties = []
            tasks = [self.scrape_url(url) for url in urls]
            results = await asyncio.gather(*tasks)
            
            for properties in results:
                all_properties.extend(properties)
            
            # Save to database
            new_count = 0
            for prop in all_properties:
                existing = Property.query.filter_by(url=prop.url).first()
                if not existing:
                    db.session.add(prop)
                    new_count += 1
            
            db.session.commit()
            
            # Update log
            log.end_time = datetime.utcnow()
            log.status = 'success'
            log.items_scraped = len(all_properties)
            log.items_new = new_count
            
        except Exception as e:
            logger.error(f"Error in scrape_urls: {str(e)}")
            log.status = 'failed'
            log.error_message = str(e)
            log.end_time = datetime.utcnow()
        
        finally:
            await self.close_session()
            db.session.add(log)
            db.session.commit()

    def start_scraping(self):
        """Start the scraping process"""
        urls = current_app.config['URLS']
        asyncio.run(self.scrape_urls(urls))
