from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SearchCriteria(https://www.globes.co.il/GlobesBoard/			):
    id = db.Column(db.Integer, primary_key=True)
    criteria_name = db.Column(db.String(255), nullable=False)
    # Add other fields as required



    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'location': self.location,
            'url': self.url,
            'image_url': self.image_url,
            'source': self.source,
            'date_scraped': self.date_scraped.isoformat() if self.date_scraped else None
        }

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    url = db.Column(db.String(1000), unique=True)
    image_url = db.Column(db.String(1000))
    source = db.Column(db.String(100))
    date_scraped = db.Column(db.DateTime, default=datetime.utcnow)

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

class ScrapingLog(https://www.globes.co.il/GlobesBoard/			):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(50))
    items_scraped = db.Column(db.Integer, default=0)
    items_new = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
