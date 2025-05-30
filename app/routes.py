from flask import render_template, request, jsonify, current_app # current_app to access app context
from . import db # From app package's __init__.py
from .models import Card, PurchaseCategory # Import your models
from .services import get_card_recommendation # Import your service function
import json

# This is a simplified way to register routes directly on the app.
# For larger apps, Flask Blueprints are recommended for better organization.
# We assume `app` is accessible; for that, we will call these routes within app_context in __init__.py
# or use a Blueprint. For simplicity here, let's ensure it's called within app_context or
# delay route definition slightly. The `@current_app.route` decorator might be better if defining outside.
# Let's assume these routes are imported and registered within `create_app` in `__init__.py`

# A better way if routes are in a separate file like this:
from flask import Blueprint
main_routes = Blueprint('main', __name__)

@main_routes.route('/', methods=['GET'])
def index():
    categories = PurchaseCategory.query.all()
    return render_template('index.html', categories=categories)

@main_routes.route('/recommend', methods=['POST', 'GET']) # Allow GET for easy testing via URL
def recommend():
    if request.method == 'POST':
        category_name = request.form.get('category')
    else: # GET request
        category_name = request.args.get('category')

    if not category_name:
        return jsonify({"error": "Category not provided."}), 400

    # user_id = session.get('user_id') # If you have user login
    user_id = None # Placeholder for now
    
    recommendation, eligible_cards = get_card_recommendation(category_name, user_id)

    if "error" in recommendation:
        return jsonify(recommendation), 404
    
    # For an HTML response:
    # return render_template('recommend.html', recommendation=recommendation, category_name=category_name, eligible_cards=eligible_cards)
    
    # For an API-like JSON response:
    return jsonify({
        "query_category": category_name,
        "best_recommendation": recommendation,
        "other_eligible_cards": eligible_cards
    })

@main_routes.route('/add_card_data', methods=['GET'])
def add_sample_data():
    try:
        # --- Add Purchase Categories ---
        categories_to_add = ["Dining", "Travel", "Groceries", "Gas", "Online Shopping"]
        for cat_name in categories_to_add:
            category = PurchaseCategory.query.filter_by(name=cat_name).first()
            if not category:
                category = PurchaseCategory(name=cat_name)
                db.session.add(category)
        # Commit after adding all categories (or after each, but batching is often better)
        # db.session.commit() # Option 1: Commit categories before cards

        # --- Add Sample Cards ---
        cards_data = [
            {
                "name": "Super Diner Card", "issuer": "Bank A", "annual_fee": 95.0,
                "reward_rules": json.dumps({"dining": 0.04, "online shopping": 0.03, "groceries": 0.01}),
                "benefits_summary": "Bonus points at restaurants, travel credits",
                "img_url": "https://via.placeholder.com/150/FF0000/FFFFFF?Text=SuperDiner"
            },
            {
                "name": "TravelMaster Gold", "issuer": "Bank B", "annual_fee": 250.0,
                "reward_rules": json.dumps({"travel": 0.05, "dining": 0.02}),
                "benefits_summary": "Airport lounge access, travel insurance",
                "img_url": "https://via.placeholder.com/150/0000FF/FFFFFF?Text=TravelMaster"
            },
            {
                "name": "Everyday Saver", "issuer": "Credit Union C", "annual_fee": 0.0,
                "reward_rules": json.dumps({"groceries": 0.06, "gas": 0.03}),
                "benefits_summary": "Cashback on essentials",
                "img_url": "https://via.placeholder.com/150/00FF00/000000?Text=EverydaySaver"
            },
            {
                "name": "Flat Rewards Plus", "issuer": "Bank D", "annual_fee": 0.0,
                "reward_rules": json.dumps({"all_purchases": 0.02}), # Example of a flat-rate card
                "benefits_summary": "Simple 2% on everything",
                "img_url": "https://via.placeholder.com/150/FFFF00/000000?Text=FlatRewards"
            }
        ]

        for card_data_item in cards_data:
            card = Card.query.filter_by(name=card_data_item["name"]).first() # Check if card with this name exists
            if not card:
                new_card = Card( # Create new card object
                    name=card_data_item["name"],
                    issuer=card_data_item["issuer"],
                    annual_fee=card_data_item["annual_fee"],
                    reward_rules=card_data_item["reward_rules"],
                    benefits_summary=card_data_item["benefits_summary"],
                    img_url=card_data_item["img_url"]
                )
                db.session.add(new_card)

        # Commit all changes (categories and cards)
        db.session.commit()
        current_app.logger.info("Sample data added/verified successfully!")
        return jsonify({"message": "Sample data added/verified successfully!"})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding sample data: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while adding sample data. Check server logs.", "details": str(e)}), 500

# Helper method for get_or_create pattern (add this to models.py or a utils.py)
# In models.py:
# class Base(db.Model):
#     __abstract__ = True
#     @classmethod
#     def get_or_create(cls, **kwargs):
#         instance = db.session.query(cls).filter_by(**kwargs).first()
#         if instance:
#             return instance, False
#         else:
#             instance = cls(**kwargs)
#             db.session.add(instance)
#             # db.session.commit() # Commit outside or pass session
#             return instance, True
# And then make Card, PurchaseCategory inherit from Base
# For now, to keep it simple in routes.py for this temporary route:
def get_or_create_temp(model, **kwargs):
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        db.session.add(instance)
        return instance, True

# Modify `add_sample_data` to use `get_or_create_temp`:
# cat_dining, _ = get_or_create_temp(PurchaseCategory, name="Dining")
# card1, _ = get_or_create_temp(Card, name="Super Diner Card", ...)

# To make this work, you need to modify app/__init__.py to register the blueprint:
# In app/__init__.py:
# ...
# def create_app(config_class=Config):
#     ...
#     with app.app_context():
#         from .routes import main_routes # Import the blueprint
#         app.register_blueprint(main_routes) # Register it
#         ...
#     return app