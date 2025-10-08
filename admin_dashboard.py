from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import Database, User, Message, ChatSession
from surveillance import SurveillanceSystem
from config import Config
import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Initialize database and surveillance
db = Database(Config.DATABASE_URL)
surveillance = SurveillanceSystem(db)

def require_admin_login(f):
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in Config.ADMINS and Config.ADMINS[username]['password'] == password:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_name'] = Config.ADMINS[username]['name']
            surveillance.log_admin_action(username, 'Logged into admin panel')
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return '''
    <html>
        <head><title>Admin Login</title></head>
        <body>
            <h2>Team Surveillance Login</h2>
            <form method="post">
                <input type="text" name="username" placeholder="Username" required><br>
                <input type="password" name="password" placeholder="Password" required><br>
                <button type="submit">Login</button>
            </form>
        </body>
    </html>
    '''

@app.route('/admin')
@require_admin_login
def dashboard():
    stats = surveillance.get_system_stats()
    users = db.get_all_users()
    recent_messages = db.get_all_chats()[:50]  # Last 50 messages
    
    return f'''
    <html>
        <head>
            <title>Chat Surveillance Dashboard</title>
            <meta http-equiv="refresh" content="30">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                .stat-box {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
                .user-list, .chat-list {{ margin: 20px 0; }}
                .user-item, .message-item {{ border: 1px solid #ddd; padding: 10px; margin: 5px 0; }}
            </style>
        </head>
        <body>
            <h1>🤖 Chat Surveillance Dashboard</h1>
            <p>Welcome, {session['admin_name']} | <a href="/admin/logout">Logout</a></p>
            
            <div class="stats">
                <div class="stat-box">
                    <h3>👥 Total Users</h3>
                    <p>{stats['total_users']}</p>
                </div>
                <div class="stat-box">
                    <h3>💬 Total Messages</h3>
                    <p>{stats['total_messages']}</p>
                </div>
                <div class="stat-box">
                    <h3>🔴 Active Sessions</h3>
                    <p>{stats['active_sessions']}</p>
                </div>
                <div class="stat-box">
                    <h3>🚫 Banned Users</h3>
                    <p>{stats['banned_users']}</p>
                </div>
            </div>
            
            <div class="user-list">
                <h2>👥 All Users ({len(users)})</h2>
                {' '.join([f'''
                <div class="user-item">
                    <strong>User ID:</strong> {user.user_id} | 
                    <strong>Name:</strong> {user.first_name or 'N/A'} {user.last_name or ''} | 
                    <strong>Username:</strong> @{user.username or 'N/A'} | 
                    <strong>Messages:</strong> {user.message_count} | 
                    <strong>Joined:</strong> {user.join_date.strftime('%Y-%m-%d %H:%M')} |
                    <a href="/admin/user/{user.user_id}">View Details</a>
                </div>
                ''' for user in users])}
            </div>
            
            <div class="chat-list">
                <h2>💬 Recent Messages</h2>
                {' '.join([f'''
                <div class="message-item">
                    <strong>From:</strong> {msg.from_user_id} | 
                    <strong>To:</strong> {msg.to_user_id} | 
                    <strong>Time:</strong> {msg.timestamp.strftime('%H:%M:%S')} | 
                    <strong>Message:</strong> {msg.message_text[:100]}{'...' if len(msg.message_text) > 100 else ''}
                </div>
                ''' for msg in recent_messages])}
            </div>
        </body>
    </html>
    '''

@app.route('/admin/user/<int:user_id>')
@require_admin_login
def user_detail(user_id):
    user = db.session.query(User).filter_by(user_id=user_id).first()
    if not user:
        return "User not found"
    
    messages = db.get_user_messages(user_id)
    analytics = surveillance.get_user_analytics(user_id)
    
    return f'''
    <html>
        <head><title>User Details - {user_id}</title></head>
        <body>
            <h1>User Details</h1>
            <a href="/admin">← Back to Dashboard</a>
            
            <h2>User Information</h2>
            <p><strong>ID:</strong> {user.user_id}</p>
            <p><strong>Username:</strong> @{user.username or 'N/A'}</p>
            <p><strong>Name:</strong> {user.first_name or 'N/A'} {user.last_name or ''}</p>
            <p><strong>Gender:</strong> {user.gender or 'Not specified'}</p>
            <p><strong>Total Messages:</strong> {user.message_count}</p>
            <p><strong>Joined:</strong> {user.join_date.strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>Last Active:</strong> {user.last_active.strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>Status:</strong> {'🚫 BANNED' if user.is_banned else '✅ Active'}</p>
            
            <h2>Message History ({len(messages)} messages)</h2>
            {' '.join([f'''
            <div style="border:1px solid #ccc; padding:10px; margin:5px;">
                <strong>{'Sent' if msg.from_user_id == user_id else 'Received'}</strong> | 
                <strong>Time:</strong> {msg.timestamp.strftime('%Y-%m-%d %H:%M')} | 
                <strong>To/From:</strong> {msg.to_user_id if msg.from_user_id == user_id else msg.from_user_id}<br>
                {msg.message_text}
            </div>
            ''' for msg in messages])}
        </body>
    </html>
    '''

@app.route('/admin/api/stats')
@require_admin_login
def api_stats():
    return jsonify(surveillance.get_system_stats())

@app.route('/admin/api/messages')
@require_admin_login
def api_messages():
    limit = request.args.get('limit', 100)
    messages = db.get_all_chats()[:int(limit)]
    return jsonify([{
        'id': msg.id,
        'from_user_id': msg.from_user_id,
        'to_user_id': msg.to_user_id,
        'text': msg.message_text,
        'timestamp': msg.timestamp.isoformat(),
        'type': msg.message_type
    } for msg in messages])

@app.route('/admin/logout')
def admin_logout():
    if 'admin_username' in session:
        surveillance.log_admin_action(session['admin_username'], 'Logged out')
    session.clear()
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
