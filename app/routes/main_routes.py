from flask import render_template, session, redirect, url_for, request
from app.routes import main_bp
from app.models import User
from app.extensions import db


@main_bp.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@main_bp.route('/dashboard')
def dashboard():
    """User dashboard - The Safehouse"""
    # Check if user is logged in (simplified - in production use proper auth)
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    # Get user stats by Lernfeld for radar chart
    stats = user.get_stats_by_lernfeld()
    
    return render_template('dashboard/safehouse.html', user=user, stats=stats)


@main_bp.route('/avatar-editor')
def avatar_editor():
    """Avatar editor - Ripperdoc"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    return render_template('dashboard/ripperdoc.html', user=user)


@main_bp.route('/language/<lang>')
def set_language(lang):
    """Set user language preference"""
    if lang in ['de', 'en']:
        session['language'] = lang
    return redirect(request.referrer or url_for('main.index'))


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with password verification"""
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session.permanent = True  # Use permanent session
            user.last_login = db.func.now()
            db.session.commit()
            return redirect(url_for('main.dashboard'))
        else:
            error = 'Ungültiger Benutzername oder Passwort'
    
    return render_template('login.html', error=error)


@main_bp.route('/logout')
def logout():
    """Logout user"""
    session.pop('user_id', None)
    return redirect(url_for('main.index'))
