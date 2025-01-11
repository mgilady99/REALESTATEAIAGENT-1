import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiUrlScraper:
    """Scraper for handling multiple URLs"""
    
    def __init__(self):
        self.session = None
        
    async def create_session(self):
        """Create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def fetch_url(self, url: str) -> str:
        """Fetch content from a URL"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Error fetching {url}: Status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
            
    def parse_html(self, html: str) -> Dict:
        """Parse HTML content and extract relevant information"""
        try:
            if not html:
                return None
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract basic information
            data = {
                'title': soup.title.string if soup.title else None,
                'description': None,
                'price': None,
                'source': None
            }
            
            # Try to find meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                data['description'] = meta_desc.get('content')
                
            return data
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {str(e)}")
            return None
            
    async def scrape_urls(self, urls: List[str]) -> List[Dict]:
        """Scrape multiple URLs concurrently"""
        try:
            await self.create_session()
            
            # Create tasks for each URL
            tasks = [self.fetch_url(url) for url in urls]
            
            # Wait for all requests to complete
            responses = await asyncio.gather(*tasks)
            
            # Process responses
            results = []
            for url, html in zip(urls, responses):
                if html:
                    data = self.parse_html(html)
                    if data:
                        data['url'] = url
                        results.append(data)
                        
            await self.close_session()
            return results
            
        except Exception as e:
            logger.error(f"Error in scrape_urls: {str(e)}")
            await self.close_session()
            return []
            
    def save_results(self, results: List[Dict], filename: str = 'results.json'):
        """Save results to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
