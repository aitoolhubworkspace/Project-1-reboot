from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import logging
import uuid
import datetime
from database import Database, User, ChatSession, Message
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db = Database(Config.DATABASE_URL)

class AnonymousChatBot:
    def __init__(self):
        self.active_sessions = {}  # user_id -> session_data
        self.user_states = {}  # user_id -> state
        self.waiting_users = {
            'male': [],
            'female': [],
            'any': []
        }
    
    async def start(self, update: Update, context: CallbackContext):
        user = update.effective_user
        user_id = user.id
        
        # Add user to database
        existing_user = db.session.query(User).filter_by(user_id=user_id).first()
        if not existing_user:
            new_user = User(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                join_date=datetime.datetime.utcnow()
            )
            db.session.add(new_user)
            db.session.commit()
        
        keyboard = [
            [InlineKeyboardButton("🚀 Start Chatting", callback_data='start_chat')],
            [InlineKeyboardButton("👤 Set Gender", callback_data='set_gender')],
            [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👋 Welcome to Anonymous Chat Bot!\n\n"
            "• Chat completely anonymously\n"
            "• Meet new people\n"
            "• Your privacy is protected\n\n"
            "Click 'Start Chatting' to begin!",
            reply_markup=reply_markup
        )
    
    async def handle_message(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Log message for surveillance
        if user_id in self.active_sessions:
            session_data = self.active_sessions[user_id]
            partner_id = session_data['partner_id']
            
            # Log the message
            db.log_message(
                session_id=session_data['session_id'],
                from_user_id=user_id,
                to_user_id=partner_id,
                message_text=message_text
            )
            
            # Forward message to partner
            try:
                await context.bot.send_message(
                    chat_id=partner_id,
                    text=f"🗣️: {message_text}"
                )
                await update.message.reply_text("✅ Message sent!")
            except Exception as e:
                await update.message.reply_text("❌ Partner disconnected. Starting new search...")
                await self.start_search(update, context, user_id)
        else:
            await update.message.reply_text("❌ You're not in an active chat. Use /start to begin.")
    
    async def button_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == 'start_chat':
            await self.start_search(update, context, user_id)
        elif data == 'set_gender':
            await self.set_gender(update, context)
        elif data == 'help':
            await query.edit_message_text(
                "📖 **Help Guide**\n\n"
                "• Use /start to begin\n"
                "• Click 'Start Chatting' to find a partner\n"
                "• Set your gender for better matching\n"
                "• Type /stop to end current chat\n"
                "• Be respectful to others!\n\n"
                "Your chats are anonymous and secure."
            )
    
    async def start_search(self, update: Update, context: CallbackContext, user_id=None):
        if not user_id:
            user_id = update.effective_user.id
        
        # Get user gender preference
        user = db.session.query(User).filter_by(user_id=user_id).first()
        gender = user.gender if user and user.gender else 'any'
        
        # Add to waiting list
        if user_id not in self.waiting_users[gender]:
            self.waiting_users[gender].append(user_id)
        
        # Try to find match
        await self.find_match(user_id, gender, context)
        
        if isinstance(update, Update) and update.callback_query:
            await update.callback_query.edit_message_text(
                "🔍 Searching for a chat partner...\n"
                "Please wait while we find someone for you to talk with!"
            )
    
    async def find_match(self, user_id, gender, context):
        # Simple matching algorithm
        potential_partners = []
        
        # Add opposite gender matches
        if gender == 'male':
            potential_partners.extend(self.waiting_users['female'])
        elif gender == 'female':
            potential_partners.extend(self.waiting_users['male'])
        
        # Add any gender matches
        potential_partners.extend(self.waiting_users['any'])
        
        # Remove self and find available partner
        for partner_id in potential_partners:
            if partner_id != user_id and partner_id not in self.active_sessions:
                # Create chat session
                session_id = str(uuid.uuid4())
                
                self.active_sessions[user_id] = {
                    'session_id': session_id,
                    'partner_id': partner_id,
                    'start_time': datetime.datetime.utcnow()
                }
                self.active_sessions[partner_id] = {
                    'session_id': session_id,
                    'partner_id': user_id,
                    'start_time': datetime.datetime.utcnow()
                }
                
                # Remove from waiting lists
                for gender_list in self.waiting_users.values():
                    if user_id in gender_list:
                        gender_list.remove(user_id)
                    if partner_id in gender_list:
                        gender_list.remove(partner_id)
                
                # Create session in database
                chat_session = ChatSession(
                    session_id=session_id,
                    user1_id=user_id,
                    user2_id=partner_id
                )
                db.session.add(chat_session)
                db.session.commit()
                
                # Notify both users
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="✅ **Connected!** You're now chatting anonymously.\n\n"
                             "Type your messages and they'll be sent to your partner.\n"
                             "Use /stop to end the chat."
                    )
                    await context.bot.send_message(
                        chat_id=partner_id,
                        text="✅ **Connected!** You're now chatting anonymously.\n\n"
                             "Type your messages and they'll be sent to your partner.\n"
                             "Use /stop to end the chat."
                    )
                except Exception as e:
                    logger.error(f"Error notifying users: {e}")
                
                return True
        
        return False
    
    async def set_gender(self, update: Update, context: CallbackContext):
        keyboard = [
            [InlineKeyboardButton("👨 Male", callback_data='gender_male')],
            [InlineKeyboardButton("👩 Female", callback_data='gender_female')],
            [InlineKeyboardButton("❓ Prefer not to say", callback_data='gender_any')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Please select your gender for better matching:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Please select your gender for better matching:",
                reply_markup=reply_markup
            )
    
    async def gender_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        gender = query.data.replace('gender_', '')
        
        # Update user in database
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.gender = gender
            db.session.commit()
        
        gender_display = {
            'male': '👨 Male',
            'female': '👩 Female', 
            'any': '❓ Prefer not to say'
        }
        
        await query.edit_message_text(f"✅ Gender set to: {gender_display[gender]}")
    
    async def stop_chat(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        
        if user_id in self.active_sessions:
            session_data = self.active_sessions[user_id]
            partner_id = session_data['partner_id']
            
            # End session in database
            chat_session = db.session.query(ChatSession).filter_by(
                session_id=session_data['session_id']
            ).first()
            if chat_session:
                chat_session.end_time = datetime.datetime.utcnow()
                db.session.commit()
            
            # Remove from active sessions
            self.active_sessions.pop(user_id, None)
            self.active_sessions.pop(partner_id, None)
            
            # Notify partner
            try:
                await context.bot.send_message(
                    chat_id=partner_id,
                    text="❌ Your partner has ended the chat. Use /start to find a new partner."
                )
            except:
                pass
            
            await update.message.reply_text("✅ Chat ended. Use /start to find a new partner.")
        else:
            await update.message.reply_text("❌ You're not in an active chat.")

def setup_bot():
    """Setup and run the bot for Replit"""
    if not Config.BOT_TOKEN:
        print("❌ BOT_TOKEN not set! Please add it in Replit Secrets")
        return
    
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    bot = AnonymousChatBot()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("stop", bot.stop_chat))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(CallbackQueryHandler(bot.button_handler, pattern='^(start_chat|set_gender|help)$'))
    application.add_handler(CallbackQueryHandler(bot.gender_handler, pattern='^gender_'))
    
    print("✅ Bot setup complete - Starting polling...")
    application.run_polling()
