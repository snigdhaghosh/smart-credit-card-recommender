from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from flask_cors import CORS

db = SQLAlchemy()
login = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # CORS(app, supports_credentials=True, origins="http://localhost:3001")
    # CORS(app, resources={r"/api/*": {"origins": "http://localhost:3001"}})
    CORS(app)

    db.init_app(app)
    login.init_app(app)
    # migrate.init_app(app, db)

    # Import and register the blueprint AFTER initializing extensions
    

    with app.app_context():
        from app.routes import bp as main_blueprint
        app.register_blueprint(main_blueprint, url_prefix='/api')
        db.create_all()

    return app