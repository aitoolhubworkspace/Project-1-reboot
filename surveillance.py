import datetime
from database import Database
from config import Config

class SurveillanceSystem:
    def __init__(self, db):
        self.db = db
    
    def log_admin_action(self, admin_username, action):
        admin_log = self.db.session.query(AdminLog).filter_by(
            admin_username=admin_username,
            action=action
        ).first()
        
        if not admin_log:
            admin_log = AdminLog(admin_username=admin_username, action=action)
            self.db.session.add(admin_log)
            self.db.session.commit()
    
    def get_system_stats(self):
        total_users = self.db.session.query(User).count()
        total_messages = self.db.session.query(Message).count()
        active_sessions = self.db.session.query(ChatSession).filter_by(end_time=None).count()
        banned_users = self.db.session.query(User).filter_by(is_banned=True).count()
        
        return {
            'total_users': total_users,
            'total_messages': total_messages,
            'active_sessions': active_sessions,
            'banned_users': banned_users,
            'timestamp': datetime.datetime.utcnow()
        }
    
    def search_messages(self, keyword):
        return self.db.session.query(Message).filter(
            Message.message_text.ilike(f'%{keyword}%')
        ).order_by(Message.timestamp.desc()).all()
    
    def get_user_analytics(self, user_id):
        user = self.db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return None
        
        messages = self.db.get_user_messages(user_id)
        total_messages = len(messages)
        
        # Calculate activity hours
        if messages:
            first_message = min(messages, key=lambda x: x.timestamp)
            time_span = (datetime.datetime.utcnow() - first_message.timestamp).total_seconds() / 3600
            messages_per_hour = total_messages / time_span if time_span > 0 else total_messages
        else:
            messages_per_hour = 0
        
        return {
            'user_info': user,
            'total_messages': total_messages,
            'messages_per_hour': round(messages_per_hour, 2),
            'join_date': user.join_date,
            'last_active': user.last_active
      }
