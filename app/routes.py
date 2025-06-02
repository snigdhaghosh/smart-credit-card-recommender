from flask import (render_template, request, jsonify, current_app, Blueprint,
                   redirect, url_for, flash, session)
from . import db # From app package's __init__.py
from .models import User, Card, PurchaseCategory, UserOwnedCard, db # Added User, UserOwnedCard, and db
from .services import get_card_recommendation # Import your service function
import json

from functools import wraps # For login_required decorator


# This is a simplified way to register routes directly on the app.
# For larger apps, Flask Blueprints are recommended for better organization.
# We assume `app` is accessible; for that, we will call these routes within app_context in __init__.py
# or use a Blueprint. For simplicity here, let's ensure it's called within app_context or
# delay route definition slightly. The `@current_app.route` decorator might be better if defining outside.
# Let's assume these routes are imported and registered within `create_app` in `__init__.py`

# A better way if routes are in a separate file like this:
from flask import Blueprint
main_routes = Blueprint('main', __name__)


# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function



@main_routes.route('/', methods=['GET'])
def index():
    # categories = PurchaseCategory.query.all()
    # return render_template('index.html', categories=categories)
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    try:
        categories = PurchaseCategory.query.all()
    except Exception as e:
        current_app.logger.error(f"Error fetching categories for index page: {e}")
        categories = [] # Prevent error on template if DB query fails
    return render_template('index.html', categories=categories, current_user=user)


# --- User Registration ---
@main_routes.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session: # If already logged in, redirect to home
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        error = None

        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif User.query.filter_by(username=username).first() is not None:
            error = f"User {username} is already registered."
        elif User.query.filter_by(email=email).first() is not None:
            error = f"Email {email} is already registered."

        if error is None:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('main.login'))
        
        flash(error, 'danger')

    return render_template('register.html')


# --- User Login ---
@main_routes.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: # If already logged in, redirect to home
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        error = None
        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()

        if user is None:
            error = 'Incorrect username/email.'
        elif not user.check_password(password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username # Store username for display
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        
        flash(error, 'danger')

    return render_template('login.html')



# --- User Logout ---
@main_routes.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@main_routes.route('/my-cards', methods=['GET', 'POST'])
@login_required # Protect this route
def manage_owned_cards():
    user_id = session['user_id'] # We know user is logged in due to decorator
    user = User.query.get_or_404(user_id) # Get user object or 404 if not found

    if request.method == 'POST':
        # Get list of card IDs selected by the user from the form
        selected_card_ids = request.form.getlist('owned_card_ids', type=int)
        
        # Clear existing owned cards for this user
        UserOwnedCard.query.filter_by(user_id=user_id).delete()
        
        # Add the newly selected cards
        for card_id in selected_card_ids:
            card = Card.query.get(card_id)
            if card: # Ensure card exists
                user_owned_card = UserOwnedCard(user_id=user_id, card_id=card_id)
                db.session.add(user_owned_card)
        
        try:
            db.session.commit()
            flash('Your owned cards have been updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating owned cards for user {user_id}: {e}")
            flash('There was an error updating your cards. Please try again.', 'danger')
        
        return redirect(url_for('main.manage_owned_cards'))

    # GET request:
    all_cards = Card.query.order_by(Card.name).all()
    owned_card_ids = {uoc.card_id for uoc in UserOwnedCard.query.filter_by(user_id=user_id).all()}
    
    return render_template('manage_owned_cards.html', 
                           all_cards=all_cards, 
                           owned_card_ids=owned_card_ids,
                           current_user=user)



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

    user_id = session.get('user_id') # Get user_id from session
    
    # Call the updated service function
    best_card_result, eligible_cards_result = get_card_recommendation(category_name, user_id)

    # Prepare context for the template
    template_context = {
        "category_name": category_name,
        "best_card": None,
        "eligible_cards": [],
        "info_message": None,
        "error_message": None,
        "current_user": User.query.get(user_id) if user_id else None
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