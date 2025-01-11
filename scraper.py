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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
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
        # Look for numbers followed by currency symbols or currency symbols followed by numbers
        price_pattern = r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?(?:\s*[$₪€])|[$₪€]\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        price_match = re.search(price_pattern, text)
        if price_match:
            # Extract just the numbers
            number_str = re.sub(r'[^\d.]', '', price_match.group())
            try:
                return float(number_str)
            except ValueError:
                return None
        return None

    def extract_location(self, text):
        if not text:
            return None
        # Remove common words and clean up
        location = re.sub(r'(?i)(apartment|house|property|in|at|near|next to)', '', text)
        return self.clean_text(location)

    async def scrape_url(self, url):
        try:
            session = await self.create_session()
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch {url}: {response.status}")
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                properties = []
                
                # Common property listing selectors
                selectors = [
                    '.property-item', '.listing-item', '.real-estate-item',
                    '[class*="property"]', '[class*="listing"]', '[class*="apartment"]',
                    'article', '.card', '.item', '.feed-item', '.search-result'
                ]
                
                for selector in selectors:
                    listings = soup.select(selector)
                    if listings:
                        for listing in listings:
                            try:
                                # Extract title
                                title_elem = listing.find(['h1', 'h2', 'h3', 'h4', '.title', '[class*="title"]', '[class*="header"]'])
                                title = self.clean_text(title_elem.text) if title_elem else None
                                
                                # Extract price
                                price_pattern = r'(?:[\d,]+(?:\.\d{2})?(?=\s*[₪$€])|(?<=[$₪€]\s*)[\d,]+(?:\.\d{2})?)'
                                price_text = listing.get_text()
                                price_match = re.search(price_pattern, price_text)
                                price = float(re.sub(r'[^\d.]', '', price_match.group())) if price_match else None
                                
                                # Extract location
                                location_elem = listing.find(['address', '.location', '[class*="location"]', '[class*="address"]'])
                                location = self.extract_location(location_elem.text) if location_elem else None
                                
                                # Extract URL
                                link = listing.find('a')
                                url = link.get('href', '') if link else None
                                
                                # Make URL absolute if it's relative
                                if url and url.startswith('/'):
                                    url = f"https://{response.url.host}{url}"
                                elif url and not url.startswith('http'):
                                    url = f"{response.url.scheme}://{response.url.host}/{url.lstrip('/')}"
                                
                                # Extract image
                                img = listing.find('img')
                                image_url = img.get('src', '') if img else None
                                
                                # Make image URL absolute if it's relative
                                if image_url and image_url.startswith('/'):
                                    image_url = f"https://{response.url.host}{image_url}"
                                elif image_url and not image_url.startswith('http'):
                                    image_url = f"{response.url.scheme}://{response.url.host}/{image_url.lstrip('/')}"
                                
                                # Only add if we have at least title and either price or location
                                if title and (price or location):
                                    properties.append({
                                        'title': title,
                                        'price': price,
                                        'location': location,
                                        'url': url,
                                        'image_url': image_url,
                                        'source': response.url.host
                                    })
                            
                            except Exception as e:
                                logger.error(f"Error parsing listing: {str(e)}")
                                continue
                        
                        # If we found properties using this selector, no need to try others
                        if properties:
                            break
                
                return properties

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return []

    async def scrape_urls(self, urls):
        """Scrape multiple URLs concurrently"""
        try:
            tasks = []
            for url in urls:
                tasks.append(self.scrape_url(url))
            
            results = await asyncio.gather(*tasks)
            
            all_properties = []
            for properties in results:
                all_properties.extend(properties)
            
            # Save to database
            for prop in all_properties:
                # Check if property already exists (based on URL)
                existing = Property.query.filter_by(url=prop['url']).first() if prop['url'] else None
                
                if not existing:
                    new_property = Property(
                        title=prop['title'],
                        price=prop['price'],
                        location=prop['location'],
                        url=prop['url'],
                        image_url=prop['image_url'],
                        source=prop['source'],
                        date_scraped=datetime.utcnow()
                    )
                    db.session.add(new_property)
            
            # Log the scraping
            log = ScrapingLog(
                timestamp=datetime.utcnow(),
                properties_found=len(all_properties)
            )
            db.session.add(log)
            
            db.session.commit()
            logger.info(f"Scraped {len(all_properties)} properties")
            
            return all_properties
            
        except Exception as e:
            logger.error(f"Error in scrape_urls: {str(e)}")
            return []
        finally:
            await self.close_session()

    def scrape_urls_sync(self, urls):
        """Synchronous version of scrape_urls"""
        import requests
        
        properties = []
        session = requests.Session()
        session.headers.update(self.headers)
        
        for url in urls:
            try:
                response = session.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                property_data = self.extract_property_data(soup, url)
                
                if property_data:
                    properties.append(property_data)
                    
                    # Save to database
                    with current_app.app_context():
                        property_obj = Property(**property_data)
                        db.session.add(property_obj)
                        db.session.commit()
                        
                        # Log the scraping
                        log = ScrapingLog(url=url, status='success')
                        db.session.add(log)
                        db.session.commit()
                        
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                # Log the error
                with current_app.app_context():
                    log = ScrapingLog(url=url, status='error', error_message=str(e))
                    db.session.add(log)
                    db.session.commit()
                
        session.close()
        return properties

    def start_scraping(self):
        """Start the scraping process"""
        urls = current_app.config['URLS']
        asyncio.run(self.scrape_urls(urls))
