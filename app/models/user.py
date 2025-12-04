from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json


class User(db.Model):
    """User model with gamification features"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Gamification
    xp = db.Column(db.Integer, default=0, nullable=False)
    level = db.Column(db.Integer, default=1, nullable=False)
    
    # Avatar configuration (JSON)
    # Structure: {"head": "style1", "cyberware": "implant2", "color": "#00ff00"}
    avatar_config = db.Column(db.Text, default='{}', nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    teilnahmen = db.relationship('Teilnahme', back_populates='user', lazy='dynamic')
    achievements = db.relationship('Achievement', secondary='user_achievements', back_populates='users')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_avatar_config(self):
        """Parse avatar config from JSON"""
        try:
            return json.loads(self.avatar_config)
        except:
            return {}
    
    def set_avatar_config(self, config_dict):
        """Set avatar config as JSON"""
        self.avatar_config = json.dumps(config_dict)
    
    def add_xp(self, amount):
        """Add XP and handle level-up"""
        self.xp += amount
        # Simple level formula: level = floor(sqrt(xp / 100)) + 1
        new_level = int((self.xp / 100) ** 0.5) + 1
        if new_level > self.level:
            self.level = new_level
            return True  # Level up occurred
        return False
    
    def get_stats_by_lernfeld(self):
        """Get user performance statistics grouped by Lernfeld"""
        from app.models.spiel import Teilnahme, SpielSitzung
        from app.models.frage import Frage
        from app.models.lernfeld import Lernfeld
        from sqlalchemy import func
        
        # Query to get correct answers per Lernfeld
        stats = db.session.query(
            Lernfeld.name,
            func.count(Teilnahme.id).label('total_questions'),
            func.sum(db.case((Teilnahme.punkte > 0, 1), else_=0)).label('correct_answers')
        ).join(
            SpielSitzung, Teilnahme.spiel_id == SpielSitzung.id
        ).join(
            Frage, SpielSitzung.frage_id == Frage.id
        ).join(
            Lernfeld, Frage.lernfeld_id == Lernfeld.id
        ).filter(
            Teilnahme.user_id == self.id
        ).group_by(
            Lernfeld.name
        ).all()
        
        return stats
