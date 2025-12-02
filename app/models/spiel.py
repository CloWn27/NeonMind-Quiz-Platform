from app.extensions import db
from datetime import datetime


class SpielSitzung(db.Model):
    """Game session model - persistent storage for completed games"""
    __tablename__ = 'spiel_sitzungen'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Session identification
    room_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    host_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Game configuration
    modus = db.Column(db.String(20), nullable=False)  # 'multiplayer', 'survival_normal', 'survival_hardcore'
    schwierigkeit = db.Column(db.String(20))  # Filter: 'Leicht', 'Mittel', 'Schwer', 'Profi', or None for all
    
    # Current question
    frage_id = db.Column(db.Integer, db.ForeignKey('fragen.id'))
    frage_nummer = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.String(20), default='waiting')  # waiting, active, finished
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    
    # Relationships
    frage = db.relationship('Frage', back_populates='spiel_sitzungen')
    teilnahmen = db.relationship('Teilnahme', back_populates='spiel', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SpielSitzung {self.room_code}>'


class Teilnahme(db.Model):
    """Participation model - tracks individual player performance"""
    __tablename__ = 'teilnahmen'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    spiel_id = db.Column(db.Integer, db.ForeignKey('spiel_sitzungen.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Performance metrics
    punkte = db.Column(db.Integer, default=0, nullable=False)
    streak = db.Column(db.Integer, default=0, nullable=False)
    ueberlebt = db.Column(db.Boolean, default=True, nullable=False)  # For survival mode
    
    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    spiel = db.relationship('SpielSitzung', back_populates='teilnahmen')
    user = db.relationship('User', back_populates='teilnahmen')
    
    def __repr__(self):
        return f'<Teilnahme User:{self.user_id} Spiel:{self.spiel_id}>'
