from flask import Flask, render_template, jsonify, request
import sqlite3
import uuid
from datetime import datetime
import hashlib

app = Flask(__name__)

# Security enhancement - simple request validation
VALID_EXECUTORS = ['Synapse', 'ScriptWare', 'Krnl', 'Fluxus', 'Unknown']

def validate_request(data):
    if not data or 'roblox_username' not in data:
        return False
    if 'executor' in data and data['executor'] not in VALID_EXECUTORS:
        return False
    return True

def secure_hwid(raw_hwid):
    return hashlib.sha256(raw_hwid.encode()).hexdigest()

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
                  game_name TEXT,
                  ip_address TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/log_execution', methods=['POST'])
def log_execution():
    if not validate_request(request.json):
        return jsonify({'error': 'Invalid request'}), 400
    
    data = request.json
    client_ip = request.remote_addr
    
    # Secure HWID handling
    raw_hwid = data.get('hwid', str(uuid.uuid4()))
    hwid = secure_hwid(raw_hwid)
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        c.execute("SELECT * FROM users WHERE roblox_username=?", (data['roblox_username'],))
        user = c.fetchone()
        
        if user:
            executions = user[3] + 1
            c.execute("""UPDATE users SET 
                        executions=?, 
                        last_execution=?, 
                        executor=?, 
                        game_name=?,
                        ip_address=?
                        WHERE roblox_username=?""",
                    (executions, datetime.now(), 
                     data.get('executor', 'Unknown'), 
                     data.get('game_name', 'Unknown'),
                     client_ip,
                     data['roblox_username']))
        else:
            executions = 1
            c.execute("""INSERT INTO users 
                        (roblox_username, hwid, executions, last_execution, executor, game_name, ip_address) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                     (data['roblox_username'], hwid, executions, datetime.now(), 
                      data.get('executor', 'Unknown'), 
                      data.get('game_name', 'Unknown'),
                      client_ip))
        
        conn.commit()
        c.execute("SELECT * FROM users ORDER BY executions DESC")
        users = c.fetchall()
        
        users_list = []
        for user in users:
            users_list.append({
                'roblox_username': user[1],
                'hwid': user[2][:8] + '...',  # Partial reveal for security
                'executions': user[3],
                'last_execution': user[4],
                'executor': user[5],
                'game_name': user[6]
            })
        
        return jsonify({'status': 'success', 'users': users_list})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/get_users', methods=['GET'])
def get_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM users ORDER BY executions DESC")
        users = c.fetchall()
        
        users_list = []
        for user in users:
            users_list.append({
                'roblox_username': user[1],
                'hwid': user[2][:8] + '...',  # Partial reveal for security
                'executions': user[3],
                'last_execution': user[4],
                'executor': user[5],
                'game_name': user[6]
            })
        
        return jsonify(users_list)
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # debug=False for production
