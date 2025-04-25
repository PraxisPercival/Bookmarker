from flask import Blueprint, request, jsonify, session, redirect, url_for
from app.auth.auth import login_required, admin_required, get_db, verify_password
from bookmark_tracker import BookmarkTracker
import secrets
import hashlib

api = Blueprint('api', __name__)
bookmark_tracker = BookmarkTracker()

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (data['username'],))
    user = cursor.fetchone()
    db.close()
    
    if not user or not verify_password(data['password'], user['password_hash'], user['salt']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    session['logged_in'] = True
    session['username'] = user['username']
    session['is_admin'] = bool(user['is_admin'])
    session['user_id'] = user['id']
    
    return jsonify({'message': 'Login successful'})

@api.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('main.login_page'))

@api.route('/bookmarks', methods=['GET'])
@login_required
def get_bookmarks():
    bookmarks = bookmark_tracker.get_bookmarks()
    return jsonify(bookmarks)

@api.route('/bookmarks', methods=['POST'])
@login_required
def add_bookmark():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing URL'}), 400
    
    bookmark_tracker.add_bookmark(data['url'], user_id=session.get('user_id'))
    return jsonify({'message': 'Bookmark added successfully'})

@api.route('/bookmarks/<int:bookmark_id>', methods=['DELETE'])
@login_required
def delete_bookmark(bookmark_id):
    bookmark_tracker.delete_bookmark(bookmark_id)
    return jsonify({'message': 'Bookmark deleted successfully'})

@api.route('/browsers', methods=['GET'])
@login_required
def get_browsers():
    browsers = bookmark_tracker.get_browsers()
    return jsonify(browsers)

@api.route('/import', methods=['POST'])
@login_required
def import_bookmarks():
    data = request.get_json()
    if not data or 'browser' not in data:
        return jsonify({'error': 'Missing browser name'}), 400
    
    bookmarks = bookmark_tracker.import_from_browser(data['browser'])
    
    # Add imported bookmarks to the database
    for bookmark in bookmarks:
        bookmark_tracker.add_bookmark(
            bookmark['url'],
            title=bookmark['title'],
            user_id=session.get('user_id')
        )
    
    return jsonify({'message': f'Successfully imported {len(bookmarks)} bookmarks'})

@api.route('/docs', methods=['GET'])
def get_documentation():
    return jsonify({
        'endpoints': {
            '/api/login': {
                'method': 'POST',
                'description': 'Login to the system',
                'required_fields': ['username', 'password'],
                'response': {
                    'success': {'message': 'Login successful'},
                    'error': {'error': 'Invalid credentials'}
                }
            },
            '/api/logout': {
                'method': 'POST',
                'description': 'Logout from the system',
                'response': {'message': 'Logged out successfully'}
            },
            '/api/bookmarks': {
                'GET': {
                    'description': 'Get all bookmarks',
                    'authentication': 'Required',
                    'response': 'List of bookmarks'
                },
                'POST': {
                    'description': 'Add a new bookmark',
                    'authentication': 'Required',
                    'required_fields': ['url'],
                    'response': {'message': 'Bookmark added successfully'}
                }
            },
            '/api/bookmarks/<id>': {
                'DELETE': {
                    'description': 'Delete a bookmark',
                    'authentication': 'Required',
                    'response': {'message': 'Bookmark deleted successfully'}
                }
            },
            '/api/browsers': {
                'GET': {
                    'description': 'Get detected browsers',
                    'authentication': 'Required',
                    'response': 'List of browsers'
                }
            },
            '/api/import': {
                'POST': {
                    'description': 'Import bookmarks from a browser',
                    'authentication': 'Required',
                    'required_fields': ['browser'],
                    'response': {'message': 'Import success message'}
                }
            }
        }
    })

@api.route('/create-admin', methods=['POST'])
@admin_required
def create_admin():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if username exists
    cursor.execute('SELECT * FROM users WHERE username = ?', (data['username'],))
    if cursor.fetchone():
        db.close()
        return jsonify({'error': 'Username already exists'}), 400
    
    # Create new admin user
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((data['password'] + salt).encode()).hexdigest()
    
    cursor.execute('''
        INSERT INTO users (username, password_hash, salt, is_admin)
        VALUES (?, ?, ?, 1)
    ''', (data['username'], password_hash, salt))
    
    db.commit()
    db.close()
    return jsonify({'message': 'Admin user created successfully'}) 