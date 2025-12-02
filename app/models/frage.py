from app.extensions import db
import json


class Frage(db.Model):
    """Question model compatible with JSON structure"""
    __tablename__ = 'fragen'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    lernfeld_id = db.Column(db.Integer, db.ForeignKey('lernfelder.id'), nullable=False, index=True)
    
    # Question content (DE/EN support via Babel)
    frage_text = db.Column(db.Text, nullable=False)
    
    # Metadata from JSON
    themenbereich = db.Column(db.String(200), nullable=False, index=True)
    schwierigkeit = db.Column(db.String(20), nullable=False, index=True)  # Leicht, Mittel, Schwer, Profi
    typ = db.Column(db.String(20), nullable=False)  # mc, text, order, math
    zeit_sekunden = db.Column(db.Integer, nullable=False)
    
    # Optional fields
    code_snippet = db.Column(db.Text)
    bild_idee = db.Column(db.Text)
    erklaerung = db.Column(db.Text)
    
    # Tags stored as JSON array
    tags = db.Column(db.Text, default='[]')
    
    # Relationships
    lernfeld = db.relationship('Lernfeld', back_populates='fragen')
    antworten = db.relationship('Antwort', back_populates='frage', lazy='dynamic', cascade='all, delete-orphan')
    spiel_sitzungen = db.relationship('SpielSitzung', back_populates='frage', lazy='dynamic')
    
    def __repr__(self):
        return f'<Frage {self.id}: {self.frage_text[:50]}...>'
    
    def get_tags(self):
        """Parse tags from JSON"""
        try:
            return json.loads(self.tags)
        except:
            return []
    
    def set_tags(self, tags_list):
        """Set tags as JSON"""
        self.tags = json.dumps(tags_list)
    
    def get_correct_answers(self):
        """Get all correct answers for this question"""
        return self.antworten.filter_by(korrekt=True).all()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'frage_text': self.frage_text,
            'themenbereich': self.themenbereich,
            'schwierigkeit': self.schwierigkeit,
            'typ': self.typ,
            'zeit_sekunden': self.zeit_sekunden,
            'code_snippet': self.code_snippet,
            'bild_idee': self.bild_idee,
            'erklaerung': self.erklaerung,
            'tags': self.get_tags(),
            'lernfeld': self.lernfeld.name if self.lernfeld else None,
            'antworten': [a.to_dict() for a in self.antworten.all()]
        }


class Antwort(db.Model):
    """Answer model for multiple choice and other question types"""
    __tablename__ = 'antworten'
    
    id = db.Column(db.Integer, primary_key=True)
    frage_id = db.Column(db.Integer, db.ForeignKey('fragen.id'), nullable=False, index=True)
    
    # Answer content
    text = db.Column(db.Text, nullable=False)
    korrekt = db.Column(db.Boolean, nullable=False, default=False)
    
    # For 'order' type questions
    reihenfolge = db.Column(db.Integer)
    
    # Relationship
    frage = db.relationship('Frage', back_populates='antworten')
    
    def __repr__(self):
        return f'<Antwort {self.id}: {self.text[:30]}...>'
    
    def to_dict(self):
        """Convert to dictionary (without revealing correct answer in game)"""
        return {
            'id': self.id,
            'text': self.text,
            'reihenfolge': self.reihenfolge
        }
