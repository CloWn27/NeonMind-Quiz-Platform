from app.extensions import db


# Many-to-Many association table
user_achievements = db.Table('user_achievements',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('achievement_id', db.Integer, db.ForeignKey('achievements.id'), primary_key=True),
    db.Column('unlocked_at', db.DateTime, default=db.func.now())
)


class Achievement(db.Model):
    """Achievement/Badge model"""
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Achievement details
    name = db.Column(db.String(100), unique=True, nullable=False)
    beschreibung = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50))  # Icon identifier for frontend
    
    # Unlock criteria (stored as JSON or simple fields)
    criteria_type = db.Column(db.String(50), nullable=False)  # 'xp_threshold', 'streak', 'games_won', etc.
    criteria_value = db.Column(db.Integer, nullable=False)
    
    # Relationships
    users = db.relationship('User', secondary=user_achievements, back_populates='achievements')
    
    def __repr__(self):
        return f'<Achievement {self.name}>'
    
    @staticmethod
    def check_and_award(user, criteria_type, current_value):
        """Check if user should receive achievements based on criteria"""
        from app.extensions import db
        
        # Get all achievements of this type that user doesn't have
        eligible_achievements = Achievement.query.filter(
            Achievement.criteria_type == criteria_type,
            Achievement.criteria_value <= current_value,
            ~Achievement.users.any(id=user.id)
        ).all()
        
        newly_awarded = []
        for achievement in eligible_achievements:
            user.achievements.append(achievement)
            newly_awarded.append(achievement)
        
        if newly_awarded:
            db.session.commit()
        
        return newly_awarded
