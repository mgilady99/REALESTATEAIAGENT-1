import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from models import db, NewsArticle
from flask import current_app
import hashlib
from difflib import SequenceMatcher
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScraperService:
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

    def calculate_content_hash(self, title):
        """Calculate a hash of the title for similarity checking"""
        return hashlib.md5(title.lower().encode()).hexdigest()

    def is_similar_content(self, title1, title2, threshold=0.8):
        """Check if two titles are similar using SequenceMatcher"""
        return SequenceMatcher(None, title1.lower(), title2.lower()).ratio() > threshold

    async def scrape_url(self, url):
        """Scrape a single news URL"""
        try:
            session = await self.create_session()
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch {url}: {response.status}")
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                articles = []
                # Try different selectors for news articles
                selectors = [
                    'article', '.article', '.news-item', '.post',
                    '[class*="article"]', '[class*="news"]'
                ]
                
                for selector in selectors:
                    items = soup.select(selector)
                    if items:
                        for item in items:
                            # Try to find title and link
                            title_elem = item.find(['h1', 'h2', 'h3', '.title', '[class*="title"]'])
                            link_elem = item.find('a')
                            
                            if title_elem and link_elem:
                                title = self.clean_text(title_elem.text)
                                url = link_elem.get('href', '')
                                
                                # Make URL absolute if it's relative
                                if url.startswith('/'):
                                    url = f"https://{response.url.host}{url}"
                                elif not url.startswith('http'):
                                    url = f"{response.url.scheme}://{response.url.host}/{url.lstrip('/')}"
                                
                                articles.append({
                                    'title': title,
                                    'url': url,
                                    'source': response.url.host
                                })
                
                return articles

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return []

    def filter_similar_articles(self, articles):
        """Filter out articles with similar content"""
        unique_articles = []
        seen_hashes = set()
        
        for article in articles:
            content_hash = self.calculate_content_hash(article['title'])
            is_similar = False
            
            # Check for similar titles
            for unique_article in unique_articles:
                if self.is_similar_content(article['title'], unique_article['title']):
                    is_similar = True
                    break
            
            if not is_similar and content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                article['content_hash'] = content_hash
                unique_articles.append(article)
        
        return unique_articles

    async def scrape_all_news(self):
        """Scrape all news sources and return unique articles"""
        try:
            all_articles = []
            tasks = []
            
            # Create tasks for each news URL
            urls = current_app.config.get('NEWS_URLS', [])
            for url in urls:
                tasks.append(self.scrape_url(url))
            
            # Run all tasks concurrently
            results = await asyncio.gather(*tasks)
            
            # Combine all articles
            for articles in results:
                all_articles.extend(articles)
            
            # Filter similar articles
            unique_articles = self.filter_similar_articles(all_articles)
            
            # Save to database
            for article in unique_articles:
                existing = NewsArticle.query.filter_by(url=article['url']).first()
                if not existing:
                    new_article = NewsArticle(
                        title=article['title'],
                        url=article['url'],
                        source=article['source'],
                        content_hash=article['content_hash'],
                        scraped_date=datetime.utcnow()
                    )
                    db.session.add(new_article)
            
            db.session.commit()
            logger.info(f"Scraped {len(unique_articles)} unique news articles")
            
            return unique_articles
            
        except Exception as e:
            logger.error(f"Error in scrape_all_news: {str(e)}")
            return []
        finally:
            await self.close_session()

    def scrape_news(self, urls=None):
        """Start the news scraping process"""
        if urls:
            current_app.config['NEWS_URLS'] = urls
        return asyncio.run(self.scrape_all_news())
