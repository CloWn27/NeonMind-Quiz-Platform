from flask import render_template, session, redirect, url_for, request, jsonify
from app.routes import game_bp
from app.models import User, SpielSitzung, Teilnahme
from app.extensions import db, redis_client
import random
import string


def generate_room_code():
    """Generate unique 6-character room code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not SpielSitzung.query.filter_by(room_code=code).first():
            return code


@game_bp.route('/create')
def create_game():
    """Create new game session"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('main.index'))
    
    return render_template('game/create.html')


@game_bp.route('/create', methods=['POST'])
def create_game_post():
    """Handle game creation"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    modus = request.json.get('modus', 'multiplayer')
    schwierigkeit = request.json.get('schwierigkeit')
    
    # Create game session
    room_code = generate_room_code()
    spiel = SpielSitzung(
        room_code=room_code,
        host_user_id=user_id,
        modus=modus,
        schwierigkeit=schwierigkeit,
        status='waiting'
    )
    
    db.session.add(spiel)
    db.session.commit()
    
    # Initialize Redis state for real-time game
    redis_client.hset(f'room:{room_code}', 'status', 'waiting')
    redis_client.hset(f'room:{room_code}', 'host_id', user_id)
    redis_client.hset(f'room:{room_code}', 'current_question', 0)
    
    return jsonify({
        'room_code': room_code,
        'redirect': url_for('game.host_view', room_code=room_code)
    })


@game_bp.route('/join')
def join_game():
    """Join game page"""
    return render_template('game/join.html')


@game_bp.route('/host/<room_code>')
def host_view(room_code):
    """Host view - Beamer display"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('main.index'))
    
    spiel = SpielSitzung.query.filter_by(room_code=room_code).first_or_404()
    
    # Check if user is host
    if spiel.host_user_id != user_id:
        return redirect(url_for('game.controller_view', room_code=room_code))
    
    return render_template('game/host.html', spiel=spiel, room_code=room_code)


@game_bp.route('/controller/<room_code>')
def controller_view(room_code):
    """Controller view - Smartphone display"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('main.index'))
    
    spiel = SpielSitzung.query.filter_by(room_code=room_code).first_or_404()
    user = User.query.get(user_id)
    
    # Check if user already joined
    teilnahme = Teilnahme.query.filter_by(spiel_id=spiel.id, user_id=user_id).first()
    if not teilnahme:
        # Create participation record
        teilnahme = Teilnahme(spiel_id=spiel.id, user_id=user_id)
        db.session.add(teilnahme)
        db.session.commit()
        
        # Add to Redis set
        redis_client.sadd(f'room:{room_code}:players', user_id)
    
    return render_template('game/controller.html', spiel=spiel, user=user, room_code=room_code)


@game_bp.route('/survival')
def survival_mode():
    """Survival mode selection"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('main.index'))
    
    return render_template('game/survival.html')
