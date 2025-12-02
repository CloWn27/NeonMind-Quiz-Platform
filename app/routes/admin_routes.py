from flask import render_template, session, redirect, url_for, request, jsonify
from app.routes import admin_bp
from app.models import User, SpielSitzung, Frage, Lernfeld
from app.extensions import db, redis_client


def is_admin():
    """Check if current user is admin (simplified)"""
    user_id = session.get('user_id')
    if not user_id:
        return False
    user = User.query.get(user_id)
    # TODO: Add admin flag to User model
    return user and user.id == 1  # Temporary: first user is admin


@admin_bp.route('/')
def admin_dashboard():
    """Admin dashboard"""
    if not is_admin():
        return redirect(url_for('main.index'))
    
    # Get active games
    active_games = SpielSitzung.query.filter_by(status='active').all()
    
    # Get statistics
    total_users = User.query.count()
    total_questions = Frage.query.count()
    total_games = SpielSitzung.query.count()
    
    return render_template('admin/dashboard.html',
                         active_games=active_games,
                         total_users=total_users,
                         total_questions=total_questions,
                         total_games=total_games)


@admin_bp.route('/games')
def manage_games():
    """Manage active games"""
    if not is_admin():
        return redirect(url_for('main.index'))
    
    games = SpielSitzung.query.order_by(SpielSitzung.created_at.desc()).limit(50).all()
    
    return render_template('admin/games.html', games=games)


@admin_bp.route('/game/<int:game_id>/control', methods=['POST'])
def control_game(game_id):
    """Control game (pause, skip, annul question)"""
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    action = request.json.get('action')
    spiel = SpielSitzung.query.get_or_404(game_id)
    
    if action == 'pause':
        redis_client.hset(f'room:{spiel.room_code}', 'paused', 'true')
    elif action == 'resume':
        redis_client.hdel(f'room:{spiel.room_code}', 'paused')
    elif action == 'skip':
        # Emit skip event via SocketIO
        from app.extensions import socketio
        socketio.emit('admin_skip', {'room': spiel.room_code}, room=spiel.room_code)
    elif action == 'annul':
        # Mark current question as annulled
        redis_client.hset(f'room:{spiel.room_code}', 'annulled', 'true')
    elif action == 'end':
        spiel.status = 'finished'
        db.session.commit()
        redis_client.hset(f'room:{spiel.room_code}', 'status', 'finished')
    
    return jsonify({'success': True})


@admin_bp.route('/game/<int:game_id>/kick/<int:user_id>', methods=['POST'])
def kick_player(game_id, user_id):
    """Kick player from game"""
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    spiel = SpielSitzung.query.get_or_404(game_id)
    
    # Remove from Redis
    redis_client.srem(f'room:{spiel.room_code}:players', user_id)
    
    # Emit kick event
    from app.extensions import socketio
    socketio.emit('kicked', {'user_id': user_id}, room=f'user_{user_id}')
    
    return jsonify({'success': True})


@admin_bp.route('/questions')
def manage_questions():
    """Manage questions"""
    if not is_admin():
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    questions = Frage.query.order_by(Frage.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/questions.html', questions=questions)


@admin_bp.route('/users')
def manage_users():
    """Manage users"""
    if not is_admin():
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html', users=users)
