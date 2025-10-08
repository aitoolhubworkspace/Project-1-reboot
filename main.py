import os
import threading
from admin_dashboard import app
from bot import setup_bot

print("🚀 Starting Anonymous Chat Bot...")

# Set environment variables for Replit
os.environ['BOT_TOKEN'] = os.getenv('BOT_TOKEN')

def start_bot():
    """Start the Telegram bot"""
    try:
        print("🤖 Initializing Telegram Bot...")
        setup_bot()
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == '__main__':
    # Start bot in background thread
    print("🔄 Starting bot thread...")
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask web dashboard
    print("🌐 Starting web dashboard...")
    app.run(host='0.0.0.0', port=5000, debug=False)
