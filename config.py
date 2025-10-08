import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token - for Replit
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Database - Use SQLite for Replit
    DATABASE_URL = 'sqlite:///chatbot.db'
    
    # Admin credentials
    ADMINS = {
        'admin1': {'password': 'admin123', 'name': 'Team Member 1'},
        'admin2': {'password': 'admin456', 'name': 'Team Member 2'}
    }
    
    # Surveillance settings
    MESSAGE_LOG_SIZE = 1000
    USER_SESSION_TIMEOUT = 3600
