from flask import Flask
from app.auth.auth import init_db
from app.api.routes import api
from app.routes import main

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your-secret-key-here'  # Change this in production
    
    # Initialize database
    init_db()
    
    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(main)
    
    return app 