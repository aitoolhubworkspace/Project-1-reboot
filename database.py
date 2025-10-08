from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    gender = Column(String(20))
    interests = Column(JSON)
    join_date = Column(DateTime, default=datetime.datetime.utcnow)
    is_banned = Column(Boolean, default=False)
    message_count = Column(Integer, default=0)
    last_active = Column(DateTime, default=datetime.datetime.utcnow)

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True)
    user1_id = Column(Integer)
    user2_id = Column(Integer)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)
    message_count = Column(Integer, default=0)

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100))
    from_user_id = Column(Integer)
    to_user_id = Column(Integer)
    message_text = Column(Text)
    message_type = Column(String(50))  # text, image, etc.
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_reported = Column(Boolean, default=False)

class AdminLog(Base):
    __tablename__ = 'admin_logs'
    
    id = Column(Integer, primary_key=True)
    admin_username = Column(String(100))
    action = Column(String(200))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Database:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_user(self, user_data):
        user = User(**user_data)
        self.session.add(user)
        self.session.commit()
        return user
    
    def log_message(self, session_id, from_user_id, to_user_id, message_text, message_type='text'):
        message = Message(
            session_id=session_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            message_text=message_text,
            message_type=message_type
        )
        self.session.add(message)
        
        # Update user message count
        user = self.session.query(User).filter_by(user_id=from_user_id).first()
        if user:
            user.message_count += 1
            user.last_active = datetime.datetime.utcnow()
        
        self.session.commit()
        return message
    
    def get_all_users(self):
        return self.session.query(User).all()
    
    def get_user_messages(self, user_id):
        return self.session.query(Message).filter(
            (Message.from_user_id == user_id) | (Message.to_user_id == user_id)
        ).order_by(Message.timestamp).all()
    
    def get_all_chats(self):
        return self.session.query(Message).order_by(Message.timestamp.desc()).limit(1000).all()
    
    def get_active_sessions(self):
        return self.session.query(ChatSession).filter(ChatSession.end_time == None).all()
