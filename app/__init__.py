from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from config import Config

# 1. Instantiate extensions in the global scope
# These objects don't have an app attached to them yet.
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    """
    The application factory. This function creates and configures the Flask app.
    """
    # 2. Create the core Flask app object
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, supports_credentials=True, origins="http://localhost:3001")
    # CORS(app, resources={r"/api/*": {"origins": "http://localhost:3001"}})
    # CORS(app)

    db.init_app(app)
    login_manager.init_app(app)
   

    # 4. Import the models and routes *after* the db object is initialized.
    # We do this inside the factory to avoid circular imports.
    from .models import User
    from .routes import bp as main_blueprint

    # 5. Configure Flask-Login's user loader
    # This callback is used to reload the user object from the user ID stored in the session.
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 6. Register the blueprint with the app
    app.register_blueprint(main_blueprint, url_prefix='/api')

    # 7. Create the database tables within the application context
    # This ensures that the application is fully configured before interacting with the database.
    with app.app_context():
        db.create_all()

    return app