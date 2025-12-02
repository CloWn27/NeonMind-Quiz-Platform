from app.models import User, Lernfeld, Frage, Teilnahme, SpielSitzung
from app.extensions import db
from sqlalchemy import func


def get_user_radar_data(user_id):
    """
    Get user performance data for radar chart visualization
    Returns data grouped by Lernfeld
    """
    # Query to calculate performance per Lernfeld
    stats = db.session.query(
        Lernfeld.name,
        Lernfeld.id,
        func.count(Teilnahme.id).label('total_answered'),
        func.sum(db.case((Teilnahme.punkte > 0, 1), else_=0)).label('correct_answers')
    ).join(
        SpielSitzung, Teilnahme.spiel_id == SpielSitzung.id
    ).join(
        Frage, SpielSitzung.frage_id == Frage.id
    ).join(
        Lernfeld, Frage.lernfeld_id == Lernfeld.id
    ).filter(
        Teilnahme.user_id == user_id
    ).group_by(
        Lernfeld.id, Lernfeld.name
    ).all()
    
    # Get all Lernfelder to ensure complete radar chart
    all_lernfelder = Lernfeld.query.all()
    
    # Build data structure
    radar_data = {
        'labels': [],
        'datasets': [{
            'label': 'Kompetenz',
            'data': [],
            'backgroundColor': 'rgba(0, 255, 255, 0.2)',
            'borderColor': 'rgba(0, 255, 255, 1)',
            'pointBackgroundColor': 'rgba(0, 255, 255, 1)',
            'pointBorderColor': '#fff',
            'pointHoverBackgroundColor': '#fff',
            'pointHoverBorderColor': 'rgba(0, 255, 255, 1)'
        }]
    }
    
    # Create lookup for stats
    stats_dict = {stat.name: stat for stat in stats}
    
    # Fill data for all Lernfelder
    for lernfeld in all_lernfelder:
        radar_data['labels'].append(lernfeld.name)
        
        if lernfeld.name in stats_dict:
            stat = stats_dict[lernfeld.name]
            if stat.total_answered > 0:
                percentage = (stat.correct_answers / stat.total_answered) * 100
            else:
                percentage = 0
        else:
            percentage = 0
        
        radar_data['datasets'][0]['data'].append(round(percentage, 1))
    
    return radar_data


def get_global_stats():
    """Get global platform statistics"""
    total_users = User.query.count()
    total_questions = Frage.query.count()
    total_games = SpielSitzung.query.count()
    active_games = SpielSitzung.query.filter_by(status='active').count()
    
    return {
        'total_users': total_users,
        'total_questions': total_questions,
        'total_games': total_games,
        'active_games': active_games
    }


def calculate_score(time_taken, max_time, streak=0):
    """
    Calculate score based on answer time and streak
    
    Args:
        time_taken: Time in seconds to answer
        max_time: Maximum time allowed for question
        streak: Current streak count
    
    Returns:
        int: Calculated score
    """
    # Base score: 1000 points
    base_score = 1000
    
    # Time bonus: faster answers get more points
    time_ratio = 1 - (time_taken / max_time)
    time_bonus = int(base_score * time_ratio * 0.5)  # Up to 50% bonus
    
    # Streak bonus
    streak_bonus = int(base_score * (streak * 0.1))  # 10% per streak
    
    total_score = base_score + time_bonus + streak_bonus
    
    return max(0, total_score)  # Ensure non-negative


def award_xp(user, score):
    """
    Award XP to user based on score
    
    Args:
        user: User object
        score: Score earned
    
    Returns:
        dict: Info about XP gain and level up
    """
    xp_gain = score // 10  # 1 XP per 10 points
    
    leveled_up = user.add_xp(xp_gain)
    
    return {
        'xp_gained': xp_gain,
        'total_xp': user.xp,
        'level': user.level,
        'leveled_up': leveled_up
    }
