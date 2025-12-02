from flask_socketio import emit, join_room, leave_room, rooms
from flask import request, session
from app.extensions import db, redis_client
from app.models import User, SpielSitzung, Teilnahme, Frage, Antwort
from app.services.stats_service import calculate_score, award_xp
import json
import time


def register_handlers(socketio):
    """Register all SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        user_id = session.get('user_id')
        if user_id:
            join_room(f'user_{user_id}')
            emit('connected', {'user_id': user_id})
    
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        user_id = session.get('user_id')
        if user_id:
            leave_room(f'user_{user_id}')
    
    
    @socketio.on('join_game')
    def handle_join_game(data):
        """Player joins a game room"""
        room_code = data.get('room_code')
        user_id = session.get('user_id')
        
        if not user_id or not room_code:
            emit('error', {'message': 'Invalid request'})
            return
        
        # Check if room exists
        if not redis_client.exists(f'room:{room_code}'):
            emit('error', {'message': 'Room not found'})
            return
        
        # Join SocketIO room
        join_room(room_code)
        
        # Add player to Redis
        redis_client.sadd(f'room:{room_code}:players', user_id)
        
        # Get user info
        user = User.query.get(user_id)
        
        # Notify room
        emit('player_joined', {
            'user_id': user_id,
            'username': user.username,
            'avatar': user.get_avatar_config()
        }, room=room_code)
        
        # Send current room state to new player
        players = redis_client.smembers(f'room:{room_code}:players')
        player_list = []
        for pid in players:
            p = User.query.get(int(pid))
            if p:
                player_list.append({
                    'user_id': p.id,
                    'username': p.username,
                    'avatar': p.get_avatar_config()
                })
        
        emit('room_state', {
            'players': player_list,
            'status': redis_client.hget(f'room:{room_code}', 'status')
        })
    
    
    @socketio.on('start_game')
    def handle_start_game(data):
        """Host starts the game"""
        room_code = data.get('room_code')
        user_id = session.get('user_id')
        
        if not user_id or not room_code:
            emit('error', {'message': 'Invalid request'})
            return
        
        # Verify user is host
        spiel = SpielSitzung.query.filter_by(room_code=room_code).first()
        if not spiel or spiel.host_user_id != user_id:
            emit('error', {'message': 'Not authorized'})
            return
        
        # Update status
        spiel.status = 'active'
        from datetime import datetime
        spiel.started_at = datetime.utcnow()
        db.session.commit()
        
        redis_client.hset(f'room:{room_code}', 'status', 'active')
        
        # Load first question
        load_next_question(room_code, spiel)
    
    
    @socketio.on('submit_answer')
    def handle_submit_answer(data):
        """Player submits an answer"""
        room_code = data.get('room_code')
        answer_id = data.get('answer_id')
        time_taken = data.get('time_taken', 0)
        user_id = session.get('user_id')
        
        if not all([user_id, room_code, answer_id]):
            emit('error', {'message': 'Invalid request'})
            return
        
        # Get current question
        spiel = SpielSitzung.query.filter_by(room_code=room_code).first()
        if not spiel or not spiel.frage_id:
            emit('error', {'message': 'No active question'})
            return
        
        frage = Frage.query.get(spiel.frage_id)
        antwort = Antwort.query.get(answer_id)
        
        if not antwort or antwort.frage_id != frage.id:
            emit('error', {'message': 'Invalid answer'})
            return
        
        # Check if already answered (prevent double submission)
        answer_key = f'room:{room_code}:question:{frage.id}:user:{user_id}'
        if redis_client.exists(answer_key):
            emit('error', {'message': 'Already answered'})
            return
        
        # Mark as answered
        redis_client.set(answer_key, answer_id, ex=300)  # Expire after 5 minutes
        
        # Get user's current streak
        teilnahme = Teilnahme.query.filter_by(
            spiel_id=spiel.id,
            user_id=user_id
        ).first()
        
        if not teilnahme:
            emit('error', {'message': 'Not in game'})
            return
        
        # Check if answer is correct
        is_correct = antwort.korrekt
        
        if is_correct:
            # Calculate score
            score = calculate_score(time_taken, frage.zeit_sekunden, teilnahme.streak)
            teilnahme.punkte += score
            teilnahme.streak += 1
            
            # Award XP
            user = User.query.get(user_id)
            xp_info = award_xp(user, score)
            
            result = {
                'correct': True,
                'score': score,
                'total_score': teilnahme.punkte,
                'streak': teilnahme.streak,
                'xp_gained': xp_info['xp_gained'],
                'level': xp_info['level'],
                'leveled_up': xp_info['leveled_up']
            }
        else:
            # Wrong answer
            teilnahme.streak = 0
            
            # In survival hardcore mode, eliminate player
            if spiel.modus == 'survival_hardcore':
                teilnahme.ueberlebt = False
            
            result = {
                'correct': False,
                'score': 0,
                'total_score': teilnahme.punkte,
                'streak': 0,
                'eliminated': not teilnahme.ueberlebt
            }
        
        db.session.commit()
        
        # Send result to player
        emit('answer_result', result)
        
        # Notify host of answer submission
        emit('player_answered', {
            'user_id': user_id,
            'correct': is_correct
        }, room=room_code)
    
    
    @socketio.on('next_question')
    def handle_next_question(data):
        """Host requests next question"""
        room_code = data.get('room_code')
        user_id = session.get('user_id')
        
        if not user_id or not room_code:
            emit('error', {'message': 'Invalid request'})
            return
        
        spiel = SpielSitzung.query.filter_by(room_code=room_code).first()
        if not spiel or spiel.host_user_id != user_id:
            emit('error', {'message': 'Not authorized'})
            return
        
        load_next_question(room_code, spiel)
    
    
    @socketio.on('use_jammer')
    def handle_use_jammer(data):
        """Player uses jammer hack on opponent"""
        room_code = data.get('room_code')
        target_user_id = data.get('target_user_id')
        user_id = session.get('user_id')
        
        if not all([user_id, room_code, target_user_id]):
            emit('error', {'message': 'Invalid request'})
            return
        
        # TODO: Implement jammer cooldown check
        
        # Send glitch effect to target
        emit('jammer_attack', {
            'from_user_id': user_id,
            'duration': 3000  # 3 seconds
        }, room=f'user_{target_user_id}')
    
    
    @socketio.on('reconnect_game')
    def handle_reconnect(data):
        """Handle player reconnection (F5 reload support)"""
        room_code = data.get('room_code')
        user_id = session.get('user_id')
        
        if not user_id or not room_code:
            emit('error', {'message': 'Invalid request'})
            return
        
        # Rejoin room
        join_room(room_code)
        
        # Send current game state
        spiel = SpielSitzung.query.filter_by(room_code=room_code).first()
        if spiel and spiel.frage_id:
            frage = Frage.query.get(spiel.frage_id)
            teilnahme = Teilnahme.query.filter_by(
                spiel_id=spiel.id,
                user_id=user_id
            ).first()
            
            emit('game_state', {
                'question': frage.to_dict() if frage else None,
                'score': teilnahme.punkte if teilnahme else 0,
                'streak': teilnahme.streak if teilnahme else 0,
                'status': spiel.status
            })


def load_next_question(room_code, spiel):
    """Load and broadcast next question to room"""
    from app.extensions import socketio
    
    # Get next question based on game settings
    query = Frage.query
    
    if spiel.schwierigkeit:
        query = query.filter_by(schwierigkeit=spiel.schwierigkeit)
    
    # Get random question
    frage = query.order_by(db.func.random()).first()
    
    if not frage:
        # No more questions, end game
        spiel.status = 'finished'
        from datetime import datetime
        spiel.finished_at = datetime.utcnow()
        db.session.commit()
        
        redis_client.hset(f'room:{room_code}', 'status', 'finished')
        
        # Get final scores
        teilnahmen = Teilnahme.query.filter_by(spiel_id=spiel.id).order_by(
            Teilnahme.punkte.desc()
        ).all()
        
        leaderboard = [{
            'user_id': t.user_id,
            'username': t.user.username,
            'score': t.punkte,
            'streak_max': t.streak
        } for t in teilnahmen]
        
        socketio.emit('game_finished', {
            'leaderboard': leaderboard
        }, room=room_code)
        
        return
    
    # Update game state
    spiel.frage_id = frage.id
    spiel.frage_nummer += 1
    db.session.commit()
    
    redis_client.hset(f'room:{room_code}', 'current_question', frage.id)
    redis_client.hset(f'room:{room_code}', 'question_start_time', time.time())
    
    # Prepare question data (hide correct answers)
    question_data = {
        'id': frage.id,
        'frage_text': frage.frage_text,
        'typ': frage.typ,
        'zeit_sekunden': frage.zeit_sekunden,
        'code_snippet': frage.code_snippet,
        'antworten': [a.to_dict() for a in frage.antworten.all()],
        'question_number': spiel.frage_nummer
    }
    
    # Broadcast to all players
    socketio.emit('new_question', question_data, room=room_code)
