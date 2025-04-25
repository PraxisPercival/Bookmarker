from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string
from bookmark_tracker import BookmarkTracker
import os
from functools import wraps
import sqlite3
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
tracker = BookmarkTracker()

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

@app.route('/api/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (data['username'],))
    user = cursor.fetchone()
    db.close()
    
    if user and verify_password(data['password'], user['password_hash'], user['salt']):
        session['logged_in'] = True
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['is_admin'] = bool(user['is_admin'])
        return jsonify({'message': 'Login successful'})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user endpoint"""
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if username already exists
    cursor.execute('SELECT * FROM users WHERE username = ?', (data['username'],))
    if cursor.fetchone():
        db.close()
        return jsonify({'error': 'Username already exists'}), 400
    
    # Create new user
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((data['password'] + salt).encode()).hexdigest()
    
    cursor.execute('''
        INSERT INTO users (username, password_hash, salt)
        VALUES (?, ?, ?)
    ''', (data['username'], password_hash, salt))
    
    db.commit()
    db.close()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/users', methods=['GET'])
@admin_required
def list_users():
    """List all users (admin only)"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT id, username, is_admin, created_at FROM users')
    users = [dict(row) for row in cursor.fetchall()]
    
    db.close()
    return jsonify(users)

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    if user_id == session.get('user_id'):
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    if cursor.rowcount == 0:
        db.close()
        return jsonify({'error': 'User not found'}), 404
    
    db.commit()
    db.close()
    return jsonify({'message': 'User deleted successfully'})

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/login-page', methods=['GET'])
def login_page():
    """Serve a complete login page"""
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bookmark Tracker Login</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    width: 400px;
                }
                .form-group {
                    margin-bottom: 1.5rem;
                }
                label {
                    display: block;
                    margin-bottom: 0.5rem;
                    color: #333;
                    font-weight: 500;
                }
                input {
                    width: 100%;
                    padding: 0.75rem;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 1rem;
                    box-sizing: border-box;
                }
                input:focus {
                    outline: none;
                    border-color: #007bff;
                    box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
                }
                button {
                    width: 100%;
                    padding: 0.75rem;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 1rem;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }
                button:hover {
                    background-color: #0056b3;
                }
                .error {
                    color: #dc3545;
                    margin-top: 1rem;
                    padding: 0.75rem;
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 4px;
                    display: none;
                }
                .success {
                    color: #28a745;
                    margin-top: 1rem;
                    padding: 0.75rem;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 4px;
                    display: none;
                }
                .tabs {
                    display: flex;
                    margin-bottom: 1.5rem;
                    border-bottom: 1px solid #ddd;
                }
                .tab {
                    flex: 1;
                    text-align: center;
                    padding: 1rem;
                    cursor: pointer;
                    color: #6c757d;
                    font-weight: 500;
                }
                .tab.active {
                    color: #007bff;
                    border-bottom: 2px solid #007bff;
                }
                .form-container {
                    display: none;
                }
                .form-container.active {
                    display: block;
                }
                .header {
                    text-align: center;
                    margin-bottom: 2rem;
                }
                .header h1 {
                    color: #007bff;
                    margin: 0 0 0.5rem 0;
                }
                .header p {
                    color: #6c757d;
                    margin: 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Bookmark Tracker</h1>
                    <p>Manage your bookmarks across browsers</p>
                </div>
                
                <div class="tabs">
                    <div class="tab active" onclick="showForm('login')">Login</div>
                    <div class="tab" onclick="showForm('register')">Register</div>
                </div>
                
                <div id="loginForm" class="form-container active">
                    <form id="login" onsubmit="handleLogin(event)">
                        <div class="form-group">
                            <label for="loginUsername">Username</label>
                            <input type="text" id="loginUsername" name="username" required>
                        </div>
                        <div class="form-group">
                            <label for="loginPassword">Password</label>
                            <input type="password" id="loginPassword" name="password" required>
                        </div>
                        <button type="submit">Login</button>
                    </form>
                </div>
                
                <div id="registerForm" class="form-container">
                    <form id="register" onsubmit="handleRegister(event)">
                        <div class="form-group">
                            <label for="registerUsername">Username</label>
                            <input type="text" id="registerUsername" name="username" required>
                        </div>
                        <div class="form-group">
                            <label for="registerPassword">Password</label>
                            <input type="password" id="registerPassword" name="password" required>
                        </div>
                        <button type="submit">Register</button>
                    </form>
                </div>
                
                <div id="error" class="error"></div>
                <div id="success" class="success"></div>
            </div>
            
            <script>
                function showForm(formType) {
                    // Update tabs
                    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                    document.querySelector(`.tab:nth-child(${formType === 'login' ? 1 : 2})`).classList.add('active');
                    
                    // Update forms
                    document.querySelectorAll('.form-container').forEach(form => form.classList.remove('active'));
                    document.getElementById(`${formType}Form`).classList.add('active');
                    
                    // Clear messages
                    document.getElementById('error').style.display = 'none';
                    document.getElementById('success').style.display = 'none';
                }
                
                async function handleLogin(event) {
                    event.preventDefault();
                    const username = document.getElementById('loginUsername').value;
                    const password = document.getElementById('loginPassword').value;
                    
                    try {
                        const response = await fetch('/api/login', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ username, password })
                        });
                        
                        if (response.ok) {
                            window.location.href = '/api/docs';
                        } else {
                            const data = await response.json();
                            showError(data.error || 'Login failed');
                        }
                    } catch (error) {
                        showError('An error occurred');
                    }
                }
                
                async function handleRegister(event) {
                    event.preventDefault();
                    const username = document.getElementById('registerUsername').value;
                    const password = document.getElementById('registerPassword').value;
                    
                    try {
                        const response = await fetch('/api/register', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ username, password })
                        });
                        
                        if (response.ok) {
                            showSuccess('Registration successful! Please login.');
                            showForm('login');
                        } else {
                            const data = await response.json();
                            showError(data.error || 'Registration failed');
                        }
                    } catch (error) {
                        showError('An error occurred');
                    }
                }
                
                function showError(message) {
                    const errorDiv = document.getElementById('error');
                    errorDiv.textContent = message;
                    errorDiv.style.display = 'block';
                    document.getElementById('success').style.display = 'none';
                }
                
                function showSuccess(message) {
                    const successDiv = document.getElementById('success');
                    successDiv.textContent = message;
                    successDiv.style.display = 'block';
                    document.getElementById('error').style.display = 'none';
                }
            </script>
        </body>
        </html>
    ''')

def get_api_documentation():
    """Generate API documentation"""
    return {
        'endpoints': {
            '/api/login': {
                'POST': {
                    'description': 'Authenticate a user and create a session',
                    'required_fields': ['username', 'password'],
                    'example_request': {
                        'username': 'admin',
                        'password': 'password123'
                    },
                    'response': 'Session cookie on success, error message on failure'
                }
            },
            '/api/register': {
                'POST': {
                    'description': 'Register a new user account',
                    'required_fields': ['username', 'password'],
                    'example_request': {
                        'username': 'newuser',
                        'password': 'newpassword123'
                    },
                    'response': 'Success message with status code 201'
                }
            },
            '/api/logout': {
                'POST': {
                    'description': 'End the current user session',
                    'response': 'Success message'
                }
            },
            '/api/users': {
                'GET': {
                    'description': 'List all users (admin only)',
                    'response': 'List of users with their details',
                    'example_response': [
                        {
                            'id': 1,
                            'username': 'admin',
                            'is_admin': True,
                            'created_at': '2024-01-01T12:00:00'
                        }
                    ]
                }
            },
            '/api/users/<int:user_id>': {
                'DELETE': {
                    'description': 'Delete a user account (admin only)',
                    'parameters': {
                        'user_id': 'Numeric ID of the user to delete'
                    },
                    'response': 'Success message'
                }
            },
            '/api/users/admin': {
                'POST': {
                    'description': 'Create a new admin user (admin only)',
                    'required_fields': ['username', 'password'],
                    'example_request': {
                        'username': 'newadmin',
                        'password': 'adminpassword123'
                    },
                    'response': 'Success message with status code 201'
                }
            },
            '/api/bookmarks': {
                'GET': {
                    'description': 'Get all bookmarks',
                    'response': 'List of all bookmarks in JSON format',
                    'example_response': {
                        'id': 1,
                        'title': 'Example Bookmark',
                        'url': 'https://example.com',
                        'browser': 'Chrome',
                        'folder': 'Work',
                        'date_added': '2024-01-01T12:00:00',
                        'last_updated': '2024-01-01T12:00:00'
                    }
                },
                'POST': {
                    'description': 'Add a new bookmark',
                    'required_fields': ['title', 'url', 'browser'],
                    'optional_fields': ['folder'],
                    'example_request': {
                        'title': 'Example Bookmark',
                        'url': 'https://example.com',
                        'browser': 'Chrome',
                        'folder': 'Work'
                    },
                    'response': 'Success message with status code 201'
                }
            },
            '/api/bookmarks/<browser>': {
                'GET': {
                    'description': 'Get bookmarks for a specific browser',
                    'parameters': {
                        'browser': 'Name of the browser (e.g., Chrome, Firefox, Edge)'
                    },
                    'response': 'List of bookmarks for the specified browser'
                }
            },
            '/api/bookmarks/<int:bookmark_id>': {
                'DELETE': {
                    'description': 'Delete a bookmark by ID',
                    'parameters': {
                        'bookmark_id': 'Numeric ID of the bookmark to delete'
                    },
                    'response': 'Success message'
                }
            },
            '/api/bookmarks/update': {
                'POST': {
                    'description': 'Update bookmarks from all installed browsers',
                    'response': 'Success message'
                }
            },
            '/api/browsers': {
                'GET': {
                    'description': 'Get list of installed browsers',
                    'response': 'List of browser names'
                }
            },
            '/api/bookmarks/export': {
                'POST': {
                    'description': 'Export bookmarks to a file',
                    'parameters': {
                        'format': 'Export format (csv or json)',
                        'filename': 'Optional filename for the export'
                    },
                    'example_request': {
                        'format': 'csv',
                        'filename': 'my_bookmarks.csv'
                    },
                    'response': 'Success message with filename'
                }
            },
            '/api/docs': {
                'GET': {
                    'description': 'Get API documentation',
                    'response': 'This documentation'
                }
            }
        },
        'base_url': 'http://localhost:5000',
        'version': '1.0.0',
        'authentication': {
            'description': 'Most endpoints require authentication. To authenticate:',
            'steps': [
                '1. Send a POST request to /api/login with username and password',
                '2. Store the session cookie returned in the response',
                '3. Include the session cookie in subsequent requests',
                '4. Use /api/logout to end the session when done'
            ],
            'note': 'The /api/docs and /api/login endpoints do not require authentication'
        }
    }

@app.route('/api/docs', methods=['GET'])
def api_documentation():
    """Return API documentation in a beautiful HTML format"""
    docs = get_api_documentation()
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bookmark Tracker API Documentation</title>
            <style>
                :root {
                    --primary-color: #007bff;
                    --secondary-color: #6c757d;
                    --success-color: #28a745;
                    --danger-color: #dc3545;
                    --light-color: #f8f9fa;
                    --dark-color: #343a40;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }
                
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                
                header {
                    background-color: var(--primary-color);
                    color: white;
                    padding: 2rem 0;
                    margin-bottom: 2rem;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                header h1 {
                    margin: 0;
                    font-size: 2.5rem;
                }
                
                header p {
                    margin: 0.5rem 0 0;
                    opacity: 0.9;
                }
                
                .endpoint {
                    background: white;
                    border-radius: 8px;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }
                
                .endpoint-header {
                    display: flex;
                    align-items: center;
                    margin-bottom: 1rem;
                    padding-bottom: 1rem;
                    border-bottom: 1px solid #eee;
                }
                
                .method {
                    padding: 0.25rem 0.75rem;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-right: 1rem;
                    font-size: 0.9rem;
                }
                
                .method.get { background-color: #e3f2fd; color: #1976d2; }
                .method.post { background-color: #e8f5e9; color: #2e7d32; }
                .method.put { background-color: #fff3e0; color: #f57c00; }
                .method.delete { background-color: #ffebee; color: #c62828; }
                
                .path {
                    font-family: monospace;
                    font-size: 1.1rem;
                    color: var(--dark-color);
                }
                
                .description {
                    color: var(--secondary-color);
                    margin-bottom: 1rem;
                }
                
                .section {
                    margin-bottom: 1.5rem;
                }
                
                .section-title {
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                    color: var(--dark-color);
                }
                
                .parameters, .example {
                    background-color: var(--light-color);
                    padding: 1rem;
                    border-radius: 4px;
                    margin-bottom: 1rem;
                }
                
                .parameter {
                    margin-bottom: 0.5rem;
                }
                
                .parameter-name {
                    font-weight: bold;
                    font-family: monospace;
                }
                
                .parameter-description {
                    color: var(--secondary-color);
                    margin-left: 1rem;
                }
                
                .example pre {
                    background-color: #f8f9fa;
                    padding: 1rem;
                    border-radius: 4px;
                    overflow-x: auto;
                    margin: 0;
                }
                
                .auth-badge {
                    display: inline-block;
                    padding: 0.25rem 0.5rem;
                    background-color: var(--danger-color);
                    color: white;
                    border-radius: 4px;
                    font-size: 0.8rem;
                    margin-left: 1rem;
                }
                
                .response {
                    margin-top: 1rem;
                }
                
                .response pre {
                    background-color: #f8f9fa;
                    padding: 1rem;
                    border-radius: 4px;
                    overflow-x: auto;
                }
            </style>
        </head>
        <body>
            <header>
                <div class="container">
                    <h1>Bookmark Tracker API Documentation</h1>
                    <p>Version {{ docs.version }}</p>
                </div>
            </header>
            
            <div class="container">
                {% for endpoint, methods in docs.endpoints.items() %}
                    <div class="endpoint" id="{{ endpoint.replace('/', '_') }}">
                        {% for method, details in methods.items() %}
                            <div class="endpoint-header">
                                <span class="method {{ method.lower() }}">{{ method }}</span>
                                <span class="path">{{ endpoint }}</span>
                                {% if method != 'GET' or endpoint != '/api/docs' %}
                                    <span class="auth-badge">Requires Auth</span>
                                {% endif %}
                            </div>
                            
                            <div class="description">{{ details.description }}</div>
                            
                            {% if 'parameters' in details %}
                                <div class="section">
                                    <div class="section-title">Parameters</div>
                                    <div class="parameters">
                                        {% for param, desc in details.parameters.items() %}
                                            <div class="parameter">
                                                <span class="parameter-name">{{ param }}</span>
                                                <span class="parameter-description">{{ desc }}</span>
                                            </div>
                                        {% endfor %}
                                    </div>
                                </div>
                            {% endif %}
                            
                            {% if 'example_request' in details %}
                                <div class="section">
                                    <div class="section-title">Example Request</div>
                                    <div class="example">
                                        <pre>{{ details.example_request | tojson(indent=2) }}</pre>
                                    </div>
                                </div>
                            {% endif %}
                            
                            {% if 'example_response' in details %}
                                <div class="section">
                                    <div class="section-title">Example Response</div>
                                    <div class="response">
                                        <pre>{{ details.example_response | tojson(indent=2) }}</pre>
                                    </div>
                                </div>
                            {% endif %}
                            
                            <div class="section">
                                <div class="section-title">Response</div>
                                <div class="response">
                                    {{ details.response }}
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                {% endfor %}
            </div>
            
            <script>
                // Smooth scrolling for navigation
                document.querySelectorAll('.nav a').forEach(anchor => {
                    anchor.addEventListener('click', function (e) {
                        e.preventDefault();
                        document.querySelector(this.getAttribute('href')).scrollIntoView({
                            behavior: 'smooth'
                        });
                    });
                });
            </script>
        </body>
        </html>
    ''', docs=docs)

@app.route('/api/bookmarks', methods=['GET'])
@login_required
def get_all_bookmarks():
    """Get all bookmarks"""
    bookmarks = tracker.get_all_bookmarks()
    return jsonify(bookmarks)

@app.route('/api/bookmarks/<browser>', methods=['GET'])
@login_required
def get_bookmarks_by_browser(browser):
    """Get bookmarks for a specific browser"""
    bookmarks = tracker.get_bookmarks_by_browser(browser)
    return jsonify(bookmarks)

@app.route('/api/bookmarks', methods=['POST'])
@login_required
def add_bookmark():
    """Add a new bookmark"""
    data = request.json
    if not all(k in data for k in ('title', 'url', 'browser')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    tracker.add_bookmark(
        title=data['title'],
        url=data['url'],
        browser=data['browser'],
        folder=data.get('folder', '')
    )
    return jsonify({'message': 'Bookmark added successfully'}), 201

@app.route('/api/bookmarks/<int:bookmark_id>', methods=['DELETE'])
@login_required
def delete_bookmark(bookmark_id):
    """Delete a bookmark"""
    tracker.delete_bookmark(bookmark_id)
    return jsonify({'message': 'Bookmark deleted successfully'})

@app.route('/api/bookmarks/update', methods=['POST'])
@login_required
def update_bookmarks():
    """Update bookmarks from all browsers"""
    tracker.update_database()
    return jsonify({'message': 'Bookmarks updated successfully'})

@app.route('/api/browsers', methods=['GET'])
@login_required
def get_installed_browsers():
    """Get list of installed browsers"""
    browsers = tracker.get_installed_browsers()
    return jsonify(browsers)

@app.route('/api/bookmarks/export', methods=['POST'])
@login_required
def export_bookmarks():
    """Export bookmarks to a file"""
    data = request.json
    format = data.get('format', 'csv')
    filename = data.get('filename')
    
    tracker.export_bookmarks(format=format, filename=filename)
    return jsonify({'message': f'Bookmarks exported successfully to {filename}'})

def view_users():
    """View all users in the database"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT id, username, is_admin, created_at FROM users')
    users = cursor.fetchall()
    
    print("\nUsers in database:")
    print("-" * 50)
    print(f"{'ID':<5} {'Username':<15} {'Admin':<8} {'Created At'}")
    print("-" * 50)
    
    for user in users:
        print(f"{user['id']:<5} {user['username']:<15} {bool(user['is_admin']):<8} {user['created_at']}")
    
    db.close()

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

@app.route('/api/users/admin', methods=['POST'])
@admin_required
def create_admin():
    """Create a new admin user (admin only)"""
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    
    success, message = create_admin_user(data['username'], data['password'])
    if success:
        return jsonify({'message': message}), 201
    return jsonify({'error': message}), 400

def main():
    """Command line interface for admin user creation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bookmark Tracker Admin Tools')
    parser.add_argument('--create-admin', action='store_true', help='Create a new admin user')
    args = parser.parse_args()
    
    if args.create_admin:
        username = input("Enter admin username: ")
        password = input("Enter admin password: ")
        success, message = create_admin_user(username, password)
        print(message)
        if success:
            view_users()  # Show updated user list
    else:
        if not os.path.exists('bookmarks.db'):
            tracker.initialize_database()
        init_db()  # Initialize users table
        view_users()  # Display users
        app.run(debug=True)

if __name__ == '__main__':
    main() 