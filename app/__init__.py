from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

db = SQLAlchemy()

def create_app():
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
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app
