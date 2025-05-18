from flask import Flask, render_template, jsonify, request
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  roblox_username TEXT,
                  hwid TEXT,
                  executions INTEGER,
                  last_execution TIMESTAMP,
                  executor TEXT,
                  game_name TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/log_execution', methods=['POST'])
def log_execution():
    data = request.json
    
    # Validate required fields
    if not data or 'roblox_username' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Generate or get HWID
    hwid = data.get('hwid', str(uuid.uuid4()))
    
    # Connect to database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Check if user exists
    c.execute("SELECT * FROM users WHERE roblox_username=?", (data['roblox_username'],))
    user = c.fetchone()
    
    if user:
        # Update existing user
        executions = user[3] + 1
        c.execute("UPDATE users SET executions=?, last_execution=?, executor=?, game_name=? WHERE roblox_username=?",
                  (executions, datetime.now(), data.get('executor', 'Unknown'), 
                   data.get('game_name', 'Unknown'), data['roblox_username']))
    else:
        # Create new user
        executions = 1
        c.execute("INSERT INTO users (roblox_username, hwid, executions, last_execution, executor, game_name) VALUES (?, ?, ?, ?, ?, ?)",
                 (data['roblox_username'], hwid, executions, datetime.now(), 
                  data.get('executor', 'Unknown'), data.get('game_name', 'Unknown')))
    
    conn.commit()
    
    # Get all users for response
    c.execute("SELECT * FROM users ORDER BY executions DESC")
    users = c.fetchall()
    
    conn.close()
    
    # Format users for response
    users_list = []
    for user in users:
        users_list.append({
            'id': user[0],
            'roblox_username': user[1],
            'hwid': user[2],
            'executions': user[3],
            'last_execution': user[4],
            'executor': user[5],
            'game_name': user[6]
        })
    
    return jsonify({'message': 'Execution logged successfully', 'users': users_list})

@app.route('/api/get_users', methods=['GET'])
def get_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY executions DESC")
    users = c.fetchall()
    conn.close()
    
    users_list = []
    for user in users:
        users_list.append({
            'id': user[0],
            'roblox_username': user[1],
            'hwid': user[2],
            'executions': user[3],
            'last_execution': user[4],
            'executor': user[5],
            'game_name': user[6]
        })
    
    return jsonify(users_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
