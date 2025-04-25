import sqlite3
import hashlib
import secrets
from functools import wraps
from flask import session, jsonify

def get_db():
    """Get database connection"""
    db = sqlite3.connect('bookmarks.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database with users table"""
    db = get_db()
    cursor = db.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if admin user exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        # Create default admin user
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256(('password123' + salt).encode()).hexdigest()
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, is_admin)
            VALUES (?, ?, ?, 1)
        ''', ('admin', password_hash, salt))
    
    db.commit()
    db.close()

def verify_password(password, stored_hash, salt):
    """Verify password against stored hash"""
    return hashlib.sha256((password + salt).encode()).hexdigest() == stored_hash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('is_admin'):
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def create_admin_user(username, password):
    """Create a new admin user"""
    db = get_db()
    cursor = db.cursor()
    
    # Check if username already exists
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        db.close()
        return False, "Username already exists"
    
    # Create new admin user
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    
    cursor.execute('''
        INSERT INTO users (username, password_hash, salt, is_admin)
        VALUES (?, ?, ?, 1)
    ''', (username, password_hash, salt))
    
    db.commit()
    db.close()
    return True, "Admin user created successfully" 