from flask import Flask
import os
from app.auth.auth import init_db
from app.api.routes import api
from app.routes import main

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY='your-secret-key-here',  # Change this in production
            DATABASE=os.path.join(app.instance_path, 'bookmarks.db'),
        )
    else:
        app.config.from_mapping(test_config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(main)
    
    return app 