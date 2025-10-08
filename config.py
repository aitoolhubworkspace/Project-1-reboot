import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Admin credentials (for 2 team members)
    ADMINS = {
        'admin1': {'password': 'admin123', 'name': 'Team Member 1'},
        'admin2': {'password': 'admin456', 'name': 'Team Member 2'}
    }
    
    # Surveillance settings
    MESSAGE_LOG_SIZE = 1000
    USER_SESSION_TIMEOUT = 3600
