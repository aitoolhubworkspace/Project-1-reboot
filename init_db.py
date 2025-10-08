from database import Base, Database
from config import Config
import os

def initialize_database():
    db = Database(Config.DATABASE_URL)
    print("✅ Database initialized successfully!")
    
    # Test connection
    users = db.session.query(db.User).all()
    print(f"📊 Current users in database: {len(users)}")

if __name__ == '__main__':
    initialize_database()
