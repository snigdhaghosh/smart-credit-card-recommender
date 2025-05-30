from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

db = SQLAlchemy()

def create_app():
    # instance_relative_config=True tells Flask to look for config files relative to the instance folder
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config.Config')

    # ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    CORS(app)

    # register blueprints or routes
    # from .routes import main_routes as routes_bp
    # app.register_blueprint(routes_bp)

    # Register Blueprints or import routes here
    with app.app_context():
        from .routes import main_routes as routes_bp
        app.register_blueprint(routes_bp)
        # from . import routes # Import routes after app is created and configured
        # If you had Blueprints:
        # from .main_blueprint import main as main_blueprint
        # app.register_blueprint(main_blueprint)

        # Create database tables if they don't exist
        # For a new setup, or simple projects, this is okay.
        # For more complex changes, use Flask-Migrate.
        db.create_all()

    return app
