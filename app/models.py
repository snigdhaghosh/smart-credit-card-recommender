from app import db
from flask_login import UserMixin

# Association table for the many-to-many relationship between users and cards
class UserCard(db.Model):
    __tablename__ = 'user_card'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), primary_key=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    username = db.Column(db.String(80), index=True, unique=True)
    # Relationship to access owned cards
    owned_cards = db.relationship('Card', secondary='user_card', lazy='dynamic', backref=db.backref('owners', lazy='dynamic'))

    def __repr__(self):
        return f'<User {self.email}>'

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True, unique=True)
    issuer = db.Column(db.String(100))
    annual_fee = db.Column(db.Integer)
    img_url = db.Column(db.String(200))
    benefits_summary = db.Column(db.Text)
    # This stores the complex reward rules as a JSON string
    reward_rules = db.Column(db.JSON)
    
    # Foreign Key to link to the Category table
    # category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    def __repr__(self):
        return f'<Card {self.name}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    
    # Relationship to access all cards within this category
    # cards = db.relationship('Card', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'