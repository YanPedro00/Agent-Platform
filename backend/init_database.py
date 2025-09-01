#!/usr/bin/env python3
"""
Initialize the database and create native actions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Base, Action
from app.main import create_native_actions

def init_database():
    """Initialize database and create native actions"""
    print("🚀 Initializing Agent Platform Database...")
    
    try:
        # Create tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Create native actions
        print("Creating native actions...")
        create_native_actions()
        print("✅ Native actions created successfully")
        
        # Verify actions were created
        db = SessionLocal()
        actions = db.query(Action).all()
        print(f"✅ Total actions in database: {len(actions)}")
        
        for action in actions:
            print(f"   - {action.name}: {action.description}")
            
        db.close()
        
        print("\n🎉 Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
