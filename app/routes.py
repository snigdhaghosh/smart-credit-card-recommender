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
    # categories = PurchaseCategory.query.all()
    # return render_template('index.html', categories=categories)
    try:
        categories = PurchaseCategory.query.all()
    except Exception as e:
        current_app.logger.error(f"Error fetching categories for index page: {e}")
        categories = [] # Prevent error on template if DB query fails
    return render_template('index.html', categories=categories)



@main_routes.route('/recommend', methods=['POST', 'GET'])
def recommend():
    category_name = ""
    if request.method == 'POST':
        category_name = request.form.get('category')
    else: # GET request for easier testing or direct links
        category_name = request.args.get('category')

    if not category_name:
        return render_template('recommend.html', 
                               error_message="No purchase category was selected. Please try again.", 
                               category_name="N/A")

    # user_id = session.get('user_id') # For when user login is implemented
    user_id = None  # Placeholder
    
    # Call the updated service function
    best_card_result, eligible_cards_result = get_card_recommendation(category_name, user_id)

    # Prepare context for the template
    template_context = {
        "category_name": category_name,
        "best_card": None,
        "eligible_cards": [],
        "info_message": None,
        "error_message": None
    }

    if isinstance(best_card_result, dict) and "error" in best_card_result:
        template_context["error_message"] = best_card_result["error"]
    elif isinstance(best_card_result, dict) and "message" in best_card_result: # No specific best card, but a general message
        template_context["info_message"] = best_card_result["message"]
        # eligible_cards_result might be an empty list or contain general cards if logic is expanded
        template_context["eligible_cards"] = eligible_cards_result if isinstance(eligible_cards_result, list) else []
    elif best_card_result: # We have a best card
        template_context["best_card"] = best_card_result
        template_context["eligible_cards"] = eligible_cards_result
    elif isinstance(eligible_cards_result, dict) and "message" in eligible_cards_result: # No eligible cards, service returned a message in second param
         template_context["info_message"] = eligible_cards_result["message"]
    else: # Fallback for unexpected structure
        template_context["error_message"] = "Could not retrieve a recommendation at this time."

    return render_template('recommend.html', **template_context)



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
                "name": "Chase Freedom Unlimited",
                "issuer": "Chase",
                "annual_fee": 0.0,
                "reward_rules": json.dumps({
                    "All": 0.015,
                    "Dining": 0.03,
                    "Travel": 0.05
                }),
                "benefits_summary": "1.5% on all purchases; 3% on dining; 5% on travel booked through Chase.",
                "img_url": "https://www.chase.com/content/services/structured-image/image.mobile.jpg/chase-ux/bucket/secondary/card-freedom-unltd.jpg"
            },
            {
                "name": "Blue Cash Preferred® from American Express",
                "issuer": "Amex",
                "annual_fee": 95.0,
                "reward_rules": json.dumps({
                    "Groceries": 0.06,
                    "Streaming": 0.06,
                    "All": 0.01
                }),
                "benefits_summary": "6% at U.S. supermarkets (up to $6k/year), 6% on select streaming; 1% other.",
                "img_url": "https://icm.aexp-static.com/acquisition/card-art/NUS000000264_480x304_straight_withname.png"
            },
            {
                "name": "Capital One Savor Cash Rewards",
                "issuer": "Capital One",
                "annual_fee": 95.0,
                "reward_rules": json.dumps({
                    "Dining": 0.04,
                    "Entertainment": 0.04,
                    "Streaming": 0.04,
                    "Groceries": 0.03,
                    "All": 0.01
                }),
                "benefits_summary": "4% on dining, entertainment, streaming; 3% at grocery; 1% all else.",
                "img_url": "https://ecm.capitalone.com/WCM/card/products/new-savor-card-art/mobile.png"
            },
            {
                "name": "Discover it® Cash Back",
                "issuer": "Discover",
                "annual_fee": 0.0,
                "reward_rules": json.dumps({
                    "Rotating": 0.05,
                    "All": 0.01
                }),
                "benefits_summary": "5% in rotating quarterly categories (up to $1.5k/quarter); 1% on everything else.",
                "img_url": "https://www.discover.com/content/dam/discover/en_us/credit-cards/card-acquisitions/grey-redesign/global/images/cardart/cardart-student-iridescent-390-243.png"
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