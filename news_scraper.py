import aiohttp
import logging
from bs4 import BeautifulSoup
import re
from datetime import datetime
from models import db, News

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScraperService:
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

    async def scrape_news(self, urls):
        """Scrape news from multiple URLs"""
        try:
            all_news = []
            session = await self.create_session()

            for url in urls:
                try:
                    async with session.get(url, timeout=30) as response:
                        if response.status != 200:
                            logger.error(f"Failed to fetch {url}: {response.status}")
                            continue

                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Common article selectors
                        selectors = [
                            'article', '.article', '.post',
                            '[class*="article"]', '[class*="post"]', '[class*="news"]',
                            '.story', '.entry', '.item'
                        ]
                        
                        for selector in selectors:
                            articles = soup.select(selector)
                            if articles:
                                for article in articles:
                                    try:
                                        # Extract title
                                        title_elem = article.find(['h1', 'h2', 'h3', 'h4', '.title', '[class*="title"]', '[class*="headline"]'])
                                        title = self.clean_text(title_elem.text) if title_elem else None
                                        
                                        # Extract description
                                        desc_elem = article.find(['p', '.description', '[class*="description"]', '[class*="summary"]', '[class*="excerpt"]'])
                                        description = self.clean_text(desc_elem.text) if desc_elem else None
                                        
                                        # Extract URL
                                        link = article.find('a')
                                        article_url = link.get('href', '') if link else None
                                        
                                        # Make URL absolute if it's relative
                                        if article_url and article_url.startswith('/'):
                                            article_url = f"https://{response.url.host}{article_url}"
                                        elif article_url and not article_url.startswith('http'):
                                            article_url = f"{response.url.scheme}://{response.url.host}/{article_url.lstrip('/')}"
                                        
                                        # Extract image
                                        img = article.find('img')
                                        image_url = img.get('src', '') if img else None
                                        
                                        # Make image URL absolute if it's relative
                                        if image_url and image_url.startswith('/'):
                                            image_url = f"https://{response.url.host}{image_url}"
                                        elif image_url and not image_url.startswith('http'):
                                            image_url = f"{response.url.scheme}://{response.url.host}/{image_url.lstrip('/')}"
                                        
                                        # Only add if we have at least a title
                                        if title:
                                            news_item = {
                                                'title': title,
                                                'description': description,
                                                'url': article_url,
                                                'image_url': image_url,
                                                'source': response.url.host
                                            }
                                            
                                            # Check if this news item is unique
                                            if not any(n['title'] == title for n in all_news):
                                                all_news.append(news_item)
                                                
                                                # Save to database
                                                existing = News.query.filter_by(url=article_url).first() if article_url else None
                                                if not existing:
                                                    new_news = News(
                                                        title=title,
                                                        description=description,
                                                        url=article_url,
                                                        image_url=image_url,
                                                        source=response.url.host,
                                                        date_scraped=datetime.utcnow()
                                                    )
                                                    db.session.add(new_news)
                                    
                                    except Exception as e:
                                        logger.error(f"Error parsing news article: {str(e)}")
                                        continue
                                
                                # If we found articles using this selector, no need to try others
                                if all_news:
                                    break
                
                except Exception as e:
                    logger.error(f"Error scraping news from {url}: {str(e)}")
                    continue

            # Commit all changes to database
            db.session.commit()
            logger.info(f"Scraped {len(all_news)} unique news articles")
            return all_news

        except Exception as e:
            logger.error(f"Error in scrape_news: {str(e)}")
            return []
            
        finally:
            await self.close_session()

    def scrape_news_sync(self, urls):
        """Synchronous version of scrape_news"""
        import requests
        
        all_news = []
        session = requests.Session()
        session.headers.update(self.headers)
        
        for url in urls:
            try:
                response = session.get(url, timeout=30)
                response.raise_for_status()
                
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract news data
                news_items = self.extract_news_data(soup)
                
                for item in news_items:
                    # Add source URL to the news item
                    item['source_url'] = url
                    
                    # Save to database
                    news_obj = News(**item)
                    db.session.add(news_obj)
                    
                    all_news.append(item)
                
                db.session.commit()
                
            except Exception as e:
                logger.error(f"Error scraping news from {url}: {str(e)}")
                continue
        
        session.close()
        return all_news

    def extract_news_data(self, soup):
        # Common article selectors
        selectors = [
            'article', '.article', '.post',
            '[class*="article"]', '[class*="post"]', '[class*="news"]',
            '.story', '.entry', '.item'
        ]
        
        all_news = []
        for selector in selectors:
            articles = soup.select(selector)
            if articles:
                for article in articles:
                    try:
                        # Extract title
                        title_elem = article.find(['h1', 'h2', 'h3', 'h4', '.title', '[class*="title"]', '[class*="headline"]'])
                        title = self.clean_text(title_elem.text) if title_elem else None
                        
                        # Extract description
                        desc_elem = article.find(['p', '.description', '[class*="description"]', '[class*="summary"]', '[class*="excerpt"]'])
                        description = self.clean_text(desc_elem.text) if desc_elem else None
                        
                        # Extract URL
                        link = article.find('a')
                        article_url = link.get('href', '') if link else None
                        
                        # Extract image
                        img = article.find('img')
                        image_url = img.get('src', '') if img else None
                        
                        # Only add if we have at least a title
                        if title:
                            news_item = {
                                'title': title,
                                'description': description,
                                'url': article_url,
                                'image_url': image_url
                            }
                            all_news.append(news_item)
                    
                    except Exception as e:
                        logger.error(f"Error parsing news article: {str(e)}")
                        continue
                
                # If we found articles using this selector, no need to try others
                if all_news:
                    break
        
        return all_news
