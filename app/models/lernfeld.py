from app.extensions import db


class Lernfeld(db.Model):
    """Learning field/topic model"""
    __tablename__ = 'lernfelder'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., "LF 1", "LF 2"
    beschreibung = db.Column(db.Text)
    
    # Relationships
    fragen = db.relationship('Frage', back_populates='lernfeld', lazy='dynamic')
    
    def __repr__(self):
        return f'<Lernfeld {self.name}>'
