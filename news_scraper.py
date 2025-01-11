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

    async def scrape_globes_news(self, soup):
        articles = []
        try:
            news_items = soup.select('.news-item-content')
            for item in news_items:
                title_elem = item.select_one('.news-item-title')
                if title_elem and 'נדל"ן' in title_elem.text:
                    title = self.clean_text(title_elem.text)
                    url = 'https://www.globes.co.il' + title_elem.find('a')['href']
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'globes'
                    })
        except Exception as e:
            logger.error(f"Error scraping Globes news: {str(e)}")
        return articles

    async def scrape_calcalist_news(self, soup):
        articles = []
        try:
            news_items = soup.select('.real-estate-item')
            for item in news_items:
                title_elem = item.select_one('.title')
                if title_elem:
                    title = self.clean_text(title_elem.text)
                    url = 'https://www.calcalist.co.il' + title_elem.find('a')['href']
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'calcalist'
                    })
        except Exception as e:
            logger.error(f"Error scraping Calcalist news: {str(e)}")
        return articles

    async def scrape_themarker_news(self, soup):
        articles = []
        try:
            news_items = soup.select('.realestate-item')
            for item in news_items:
                title_elem = item.select_one('.title')
                if title_elem:
                    title = self.clean_text(title_elem.text)
                    url = 'https://www.themarker.com' + title_elem.find('a')['href']
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'themarker'
                    })
        except Exception as e:
            logger.error(f"Error scraping TheMarker news: {str(e)}")
        return articles

    async def scrape_bizportal_news(self, soup):
        articles = []
        try:
            news_items = soup.select('.news-item')
            for item in news_items:
                title_elem = item.select_one('.title')
                if title_elem:
                    title = self.clean_text(title_elem.text)
                    url = title_elem.find('a')['href']
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'bizportal'
                    })
        except Exception as e:
            logger.error(f"Error scraping Bizportal news: {str(e)}")
        return articles

    async def scrape_news_source(self, source_key, url):
        try:
            session = await self.create_session()
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch {url}: {response.status}")
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                if source_key == 'globes':
                    return await self.scrape_globes_news(soup)
                elif source_key == 'calcalist':
                    return await self.scrape_calcalist_news(soup)
                elif source_key == 'themarker':
                    return await self.scrape_themarker_news(soup)
                elif source_key == 'bizportal':
                    return await self.scrape_bizportal_news(soup)
                
                return []

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
            
            # Create tasks for each news source
            for source_key, config in current_app.config['NEWS_URLS'].items():
                tasks.append(self.scrape_news_source(source_key, config['url']))
            
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

    def start_news_scraping(self):
        """Start the news scraping process"""
        return asyncio.run(self.scrape_all_news())
