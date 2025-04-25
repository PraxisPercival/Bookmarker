from flask import Blueprint, render_template, session, redirect, url_for
from app.auth.auth import login_required

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/login')
def login_page():
    if 'logged_in' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@main.route('/register')
def register_page():
    if 'logged_in' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('register.html') 