import asyncio
import aiohttp
from datetime import datetime
import logging
from models import db, Property
from flask import current_app
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FacebookScraper:
    def __init__(self):
        self.session = None
        self.config = current_app.config
        self.access_token = None
        self.api_version = self.config['FB_API_VERSION']
        self.base_url = f'https://graph.facebook.com/{self.api_version}'

    async def initialize(self):
        """Initialize the scraper with a valid access token"""
        if not self.access_token:
            self.access_token = self.config.init_facebook_token()
            if not self.access_token:
                raise Exception("Failed to initialize Facebook access token")

    async def create_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def get_group_feed(self, group_id, limit=5):
        """Fetch feed from a Facebook group"""
        try:
            # Ensure we have a valid token
            await self.initialize()
            
            session = await self.create_session()
            url = f"{self.base_url}/{group_id}/feed"
            params = {
                'access_token': self.access_token,
                'limit': limit,
                'fields': 'message,created_time,permalink_url,attachments,from',
                'include_hidden': 'true'
            }

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error fetching group {group_id}: {error_text}")
                    return []

                data = await response.json()
                return data.get('data', [])

        except Exception as e:
            logger.error(f"Error in get_group_feed for group {group_id}: {str(e)}")
            return []

    def extract_property_details(self, post):
        """Extract property details from a Facebook post"""
        message = post.get('message', '')
        
        # Try to extract price
        price = None
        price_patterns = [
            r'₪\s*(\d{1,3}(?:,\d{3})*)',
            r'(\d{1,3}(?:,\d{3})*)\s*₪',
            r'מחיר[:\s]+(\d{1,3}(?:,\d{3})*)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, message)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    break
                except ValueError:
                    continue

        # Try to extract location
        location = None
        location_patterns = [
            r'ב([א-ת\s]+)מחיר',
            r'כתובת[:\s]+([א-ת\s]+)',
            r'שכונת[:\s]+([א-ת\s]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, message)
            if match:
                location = match.group(1).strip()
                break

        return {
            'title': message[:200] if message else None,  # Use first 200 chars as title
            'description': message,
            'price': price,
            'location': location,
            'url': post.get('permalink_url'),
            'date_listed': datetime.strptime(post.get('created_time'), '%Y-%m-%dT%H:%M:%S+0000'),
            'source_website': 'facebook'
        }

    async def scrape_group(self, group):
        """Scrape posts from a single Facebook group"""
        try:
            posts = await self.get_group_feed(group['id'], current_app.config['FB_POSTS_LIMIT'])
            properties = []

            for post in posts:
                if post.get('message'):  # Only process posts with text content
                    property_data = self.extract_property_details(post)
                    if property_data['url']:  # Only add if we have a valid URL
                        # Create Property object
                        property_obj = Property(
                            title=property_data['title'],
                            price=property_data['price'],
                            location=property_data['location'],
                            url=property_data['url'],
                            description=property_data['description'],
                            source_website=f"facebook_{group['id']}",
                            property_type='social',
                            date_listed=property_data['date_listed'],
                            date_scraped=datetime.utcnow(),
                            is_active=True
                        )
                        properties.append(property_obj)

            return properties

        except Exception as e:
            logger.error(f"Error scraping group {group['id']}: {str(e)}")
            return []

    async def scrape_all_groups(self):
        """Scrape all configured Facebook groups"""
        try:
            all_properties = []
            tasks = []
            
            # Create tasks for each group
            for group in current_app.config['FB_GROUPS']:
                tasks.append(self.scrape_group(group))
            
            # Run all tasks concurrently
            results = await asyncio.gather(*tasks)
            
            # Combine all properties
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
            logger.info(f"Scraped {len(all_properties)} properties from Facebook ({new_count} new)")
            
            return all_properties
            
        except Exception as e:
            logger.error(f"Error in scrape_all_groups: {str(e)}")
            return []
        finally:
            await self.close_session()

    def start_scraping(self):
        """Start the Facebook scraping process"""
        if not current_app.config['FB_ACCESS_TOKEN']:
            logger.error("Facebook access token not configured")
            return []
            
        return asyncio.run(self.scrape_all_groups())
