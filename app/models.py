from . import db

class CreditCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    categories = db.Column(db.String(200), nullable=False)
    reward_rate = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "categories": self.categories.split(','),
            "reward_rate": self.reward_rate,
            "description": self.description
        }
