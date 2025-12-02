#!/usr/bin/env python3
"""
Seed script to import quiz questions from JSON into database
Usage: python seed.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.extensions import db
from app.models import Lernfeld, Frage, Antwort


def load_json_data(filepath):
    """Load quiz data from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_or_create_lernfeld(session, name):
    """Get existing Lernfeld or create new one"""
    lernfeld = session.query(Lernfeld).filter_by(name=name).first()
    if not lernfeld:
        lernfeld = Lernfeld(name=name)
        session.add(lernfeld)
        session.flush()  # Get ID without committing
    return lernfeld


def import_question(session, question_data):
    """Import a single question with its answers"""
    
    # Get or create Lernfeld
    lernfeld = get_or_create_lernfeld(session, question_data['lernfeld'])
    
    # Check if question already exists (avoid duplicates)
    existing = session.query(Frage).filter_by(
        frage_text=question_data['frage'],
        lernfeld_id=lernfeld.id
    ).first()
    
    if existing:
        print(f"  ⏭️  Skipping duplicate: {question_data['frage'][:50]}...")
        return False
    
    # Create Frage
    frage = Frage(
        lernfeld_id=lernfeld.id,
        frage_text=question_data['frage'],
        themenbereich=question_data['themenbereich'],
        schwierigkeit=question_data['schwierigkeit'],
        typ=question_data['typ'],
        zeit_sekunden=question_data['zeit_sekunden'],
        code_snippet=question_data.get('code_snippet'),
        bild_idee=question_data.get('bild_idee'),
        erklaerung=question_data.get('erklaerung', '')
    )
    
    # Set tags
    if 'tags' in question_data:
        frage.set_tags(question_data['tags'])
    
    session.add(frage)
    session.flush()  # Get ID for answers
    
    # Create Antworten
    for idx, antwort_data in enumerate(question_data['antworten']):
        antwort = Antwort(
            frage_id=frage.id,
            text=antwort_data['text'],
            korrekt=antwort_data['korrekt'],
            reihenfolge=idx + 1 if question_data['typ'] == 'order' else None
        )
        session.add(antwort)
    
    return True


def seed_database(json_filepath):
    """Main seeding function"""
    print("🚀 Starting database seeding...")
    
    # Load JSON data
    print(f"📂 Loading data from {json_filepath}...")
    questions_data = load_json_data(json_filepath)
    print(f"✅ Loaded {len(questions_data)} questions")
    
    # Create app and database
    app = create_app('development')
    
    with app.app_context():
        # Create tables if they don't exist
        print("🔧 Creating database tables...")
        db.create_all()
        
        # Import questions
        print("📝 Importing questions...")
        imported_count = 0
        skipped_count = 0
        
        for idx, question_data in enumerate(questions_data, 1):
            try:
                if import_question(db.session, question_data):
                    imported_count += 1
                    if imported_count % 100 == 0:
                        print(f"  ✓ Imported {imported_count} questions...")
                        db.session.commit()  # Commit in batches
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"  ❌ Error importing question {idx}: {e}")
                db.session.rollback()
                continue
        
        # Final commit
        db.session.commit()
        
        print(f"\n✅ Seeding complete!")
        print(f"  📊 Imported: {imported_count} questions")
        print(f"  ⏭️  Skipped: {skipped_count} duplicates")
        
        # Print statistics
        total_lernfelder = db.session.query(Lernfeld).count()
        total_fragen = db.session.query(Frage).count()
        total_antworten = db.session.query(Antwort).count()
        
        print(f"\n📈 Database Statistics:")
        print(f"  Lernfelder: {total_lernfelder}")
        print(f"  Fragen: {total_fragen}")
        print(f"  Antworten: {total_antworten}")
        
        # Print breakdown by difficulty
        print(f"\n🎯 Questions by Difficulty:")
        for schwierigkeit in ['Leicht', 'Mittel', 'Schwer', 'Profi']:
            count = db.session.query(Frage).filter_by(schwierigkeit=schwierigkeit).count()
            print(f"  {schwierigkeit}: {count}")
        
        # Print breakdown by type
        print(f"\n📋 Questions by Type:")
        for typ in ['mc', 'text', 'order', 'math']:
            count = db.session.query(Frage).filter_by(typ=typ).count()
            if count > 0:
                print(f"  {typ}: {count}")


def create_sample_users():
    """Create sample users for testing"""
    from app.models import User
    from werkzeug.security import generate_password_hash
    
    print("\n👥 Creating sample users...")
    
    app = create_app('development')
    with app.app_context():
        # Check if users already exist
        if User.query.count() > 0:
            print("  ⏭️  Users already exist, skipping...")
            return
        
        sample_users = [
            {
                'username': 'admin',
                'email': 'admin@neonmind.de',
                'password': 'admin123',
                'xp': 5000,
                'level': 7
            },
            {
                'username': 'player1',
                'email': 'player1@neonmind.de',
                'password': 'player123',
                'xp': 1500,
                'level': 4
            },
            {
                'username': 'player2',
                'email': 'player2@neonmind.de',
                'password': 'player123',
                'xp': 800,
                'level': 3
            }
        ]
        
        for user_data in sample_users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password']),
                xp=user_data['xp'],
                level=user_data['level']
            )
            db.session.add(user)
        
        db.session.commit()
        print(f"  ✅ Created {len(sample_users)} sample users")
        print("  📝 Login credentials:")
        for user_data in sample_users:
            print(f"     {user_data['username']} / {user_data['password']}")


if __name__ == '__main__':
    # Path to JSON file
    json_file = Path(__file__).parent / 'data' / 'ihk_quiz_fragen_4_schwierigkeiten_final1.0.json'
    
    if not json_file.exists():
        print(f"❌ Error: JSON file not found at {json_file}")
        sys.exit(1)
    
    # Run seeding
    seed_database(json_file)
    
    # Create sample users
    create_sample_users()
    
    print("\n🎉 All done! Database is ready.")
