import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'you-will-never-guess')
    # For SQLite, the database will be created in the 'instance' folder
    # The 'instance' folder should be at the same level as your 'app' package
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Add other configurations here if needed
    # For example, LLM API keys (load from environment variables for security)
    # OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
