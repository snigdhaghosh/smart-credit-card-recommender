# from flask import Blueprint, request, jsonify, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Card, Category, UserCard
from flask import (render_template, request, jsonify, current_app, Blueprint,
                   redirect, url_for, flash, session)
from app.services import get_recommendations

bp = Blueprint('main', __name__)

@bp.route('/recommend', methods=['POST'])
def recommend():
    """Receives a category and returns card recommendations as JSON."""
    data = request.get_json()
    if not data or 'category' not in data:
        return jsonify({"error": "A 'category' is required in the request body."}), 400

    category_name = data['category']
    # user_id = session.get('user_id') # User session logic can be integrated later
    
    # Correctly call the service, which returns a single dictionary
    recommendations = get_recommendations(category_name)

    # Check if the service returned any valid recommendations
    if not recommendations or not recommendations.get('best_option'):
        return jsonify({"error": f"No recommendations available for the '{category_name}' category."}), 200

    # Prepare the JSON response in the format the frontend expects
    # The frontend is looking for 'best_card' and 'eligible_cards'
    return jsonify({
        "best_card": recommendations.get("best_option"),
        "eligible_cards": recommendations.get("other_options"),
    })


@bp.route('/categories', methods=['GET'])
def get_categories():
    """Provides a list of purchase categories to the frontend."""
    try:
        categories = Category.query.all()
        # Convert the list of objects to a list of strings
        return jsonify([category.name for category in categories])
    except Exception as e:
        current_app.logger.error(f"Error fetching categories: {e}")
        return jsonify({"error": "Could not fetch categories"}), 500

@bp.route('/cards', methods=['GET'])
def get_cards():
    cards = Card.query.all()
    # A more detailed card object for the frontend
    return jsonify([{
        'id': c.id, 
        'name': c.name, 
        'annual_fee': c.annual_fee,
        'img_url': c.img_url,
        'benefits': c.benefits_summary,
        'reward_rules': c.reward_rules,
        'category': c.category.name if c.category else None,
        'is_owned': c.id in [uc.card_id for uc in current_user.owned_cards] if current_user.is_authenticated else False
    } for c in cards])

# --- API for Authentication ---
@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email address already in use"}), 409

    new_user = User(email=email, password_hash=generate_password_hash(password, method='pbkdf2:sha256'))
    db.session.add(new_user)
    db.session.commit()

    # In a real app, you might log them in and return an auth token
    return jsonify({"success": "User registered successfully", "user": {"id": new_user.id, "email": new_user.email}}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()

    if user and check_password_hash(user.password_hash, data.get('password')):
        login_user(user) # This manages the server-side session
        # For a true stateless API, you'd return a JWT (JSON Web Token) here
        return jsonify({"success": "Logged in", "user": {"id": user.id, "email": user.email}})

    return jsonify({"error": "Invalid email or password"}), 401



@bp.route('/seed-data', methods=['GET'])
def seed_data():
    """A simple route to add sample data for testing."""
    categories_to_add = ["Dining", "Travel", "Groceries", "Gas", "Online Shopping"]
    for cat_name in categories_to_add:
        # Check if category already exists
        if not Category.query.filter_by(name=cat_name).first():
            new_cat = Category(name=cat_name)
            db.session.add(new_cat)
    
    try:
        db.session.commit()
        return jsonify({"message": f"Successfully added {len(categories_to_add)} categories."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
