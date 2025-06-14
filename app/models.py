from . import db # Imports the db object created in __init__.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # Increased length for potentially longer hashes
    owned_cards = db.relationship('UserOwnedCard', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Card(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    issuer = db.Column(db.String(100))
    annual_fee = db.Column(db.Float, default=0.0)
    # Using JSON for flexible reward rules.
    # For SQLite, JSON type support might need specific handling or be treated as TEXT.
    # PostgreSQL has native JSONB support which is excellent.
    # For simplicity with SQLite, we might store as TEXT and parse, or use a related table.
    # Let's use TEXT for now for broadest SQLite compatibility, assuming JSON-formatted strings.
    reward_rules = db.Column(db.Text) # Store as JSON string: '{"dining": 0.03, "travel": 0.02}'
    benefits_summary = db.Column(db.Text, nullable=True) # e.g., "Travel insurance, No foreign transaction fees"
    img_url = db.Column(db.String(200), nullable=True) # URL to an image of the card

    def __repr__(self):
        return f'<Card {self.name}>'



# Association table for User and Cards (Many-to-Many if a card can be owned by many users)
# Or simple one-to-many if UserOwnedCard stores unique instances of a card per user.
# Let's go with UserOwnedCard as a direct link for simplicity in Phase 1.
class UserOwnedCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    # Add any user-specific notes or details about this card ownership if needed

    # Relationship to get Card details easily
    card = db.relationship('Card')

    # Unique constraint to prevent duplicate entries
    __table_args__ = (db.UniqueConstraint('user_id', 'card_id', name='_user_card_uc'),)

    def __repr__(self):
        return f'<UserOwnedCard User {self.user_id} owns Card {self.card_id}>'



class PurchaseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # e.g., "Dining", "Groceries", "Travel", "Gas"

    def __repr__(self):
        return f'<PurchaseCategory {self.name}>'