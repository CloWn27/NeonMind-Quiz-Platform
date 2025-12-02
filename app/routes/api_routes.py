from flask import jsonify, request, session
from app.routes import api_bp
from app.models import User, Frage, Lernfeld
from app.extensions import db


@api_bp.route('/user/avatar', methods=['PUT'])
def update_avatar():
    """Update user avatar configuration"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get_or_404(user_id)
    avatar_config = request.json
    
    user.set_avatar_config(avatar_config)
    db.session.commit()
    
    return jsonify({'success': True, 'avatar': avatar_config})


@api_bp.route('/user/stats')
def get_user_stats():
    """Get user statistics for radar chart"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get_or_404(user_id)
    stats = user.get_stats_by_lernfeld()
    
    # Format for Chart.js radar chart
    labels = []
    data = []
    
    for stat in stats:
        labels.append(stat.name)
        # Calculate percentage correct
        if stat.total_questions > 0:
            percentage = (stat.correct_answers / stat.total_questions) * 100
        else:
            percentage = 0
        data.append(round(percentage, 1))
    
    return jsonify({
        'labels': labels,
        'data': data
    })


@api_bp.route('/questions')
def get_questions():
    """Get questions with filters"""
    schwierigkeit = request.args.get('schwierigkeit')
    lernfeld = request.args.get('lernfeld')
    typ = request.args.get('typ')
    limit = request.args.get('limit', 10, type=int)
    
    query = Frage.query
    
    if schwierigkeit:
        query = query.filter_by(schwierigkeit=schwierigkeit)
    
    if lernfeld:
        lernfeld_obj = Lernfeld.query.filter_by(name=lernfeld).first()
        if lernfeld_obj:
            query = query.filter_by(lernfeld_id=lernfeld_obj.id)
    
    if typ:
        query = query.filter_by(typ=typ)
    
    questions = query.order_by(db.func.random()).limit(limit).all()
    
    return jsonify({
        'questions': [q.to_dict() for q in questions]
    })


@api_bp.route('/lernfelder')
def get_lernfelder():
    """Get all learning fields"""
    lernfelder = Lernfeld.query.all()
    
    return jsonify({
        'lernfelder': [{'id': lf.id, 'name': lf.name, 'beschreibung': lf.beschreibung} 
                       for lf in lernfelder]
    })


@api_bp.route('/leaderboard')
def get_leaderboard():
    """Get top players by XP"""
    limit = request.args.get('limit', 10, type=int)
    
    users = User.query.order_by(User.xp.desc()).limit(limit).all()
    
    return jsonify({
        'leaderboard': [
            {
                'username': u.username,
                'xp': u.xp,
                'level': u.level,
                'avatar': u.get_avatar_config()
            }
            for u in users
        ]
    })
