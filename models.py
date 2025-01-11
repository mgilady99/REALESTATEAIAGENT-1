from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize the database object
db = SQLAlchemy()

class SearchCriteria(db.Model):
    __tablename__ = 'search_criteria'

    id = db.Column(db.Integer, primary_key=True)
    criteria_name = db.Column(db.String(255), nullable=False)
    # Add other fields as required

    def __repr__(self):
        return f'<SearchCriteria {self.criteria_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'criteria_name': self.criteria_name
        }

class News(db.Model):
    __tablename__ = 'news'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    url = db.Column(db.String(1000), unique=True)
    image_url = db.Column(db.String(1000))
    source = db.Column(db.String(100))
    date_scraped = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<News {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'image_url': self.image_url,
            'source': self.source,
            'date_scraped': self.date_scraped.isoformat() if self.date_scraped else None
        }

class Property(db.Model):
    __tablename__ = 'properties'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    location = db.Column(db.String(255))
    property_type = db.Column(db.String(50))  # E.g., 'apartment', 'office', etc.
    date_listed = db.Column(db.DateTime, default=datetime.utcnow)
    date_scraped = db.Column(db.DateTime, default=datetime.utcnow)  # Added the missing field
    image_url = db.Column(db.String(1000))

    def __repr__(self):
        return f'<Property {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'location': self.location,
            'property_type': self.property_type,
            'date_listed': self.date_listed.isoformat() if self.date_listed else None,
            'date_scraped': self.date_scraped.isoformat() if self.date_scraped else None,  # Include date_scraped
            'image_url': self.image_url
        }

class ScrapingLog(db.Model):
    __tablename__ = 'scraping_logs'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(50))
    items_scraped = db.Column(db.Integer, default=0)
    items_new = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)

    def __repr__(self):
        return f'<ScrapingLog {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'items_scraped': self.items_scraped,
            'items_new': self.items_new,
            'error_message': self.error_message
        }
