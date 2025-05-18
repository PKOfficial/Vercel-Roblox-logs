from flask import Flask, jsonify, request
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
                  game_name TEXT,
                  ip_address TEXT)''')  # Added IP tracking
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LavaScript - Roblox Tracker</title>
        <style>
            body {
                background: #0a0a0a;
                color: white;
                font-family: Arial, sans-serif;
            }
            .container {
                width: 80%;
                margin: 0 auto;
                padding: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 10px;
                border: 1px solid #7b4bff;
                text-align: left;
            }
            th {
                background-color: #4b2e83;
            }
            tr:nth-child(even) {
                background-color: #1a1a1a;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Roblox Execution Tracker</h1>
            <table id="usersTable">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>HWID</th>
                        <th>Executions</th>
                        <th>Executor</th>
                        <th>Game</th>
                        <th>Last Execution</th>
                        <th>IP</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Data will be inserted here -->
                </tbody>
            </table>
        </div>
        <script>
            fetch('/api/get_users')
                .then(response => response.json())
                .then(data => {
                    const table = document.getElementById('usersTable').getElementsByTagName('tbody')[0];
                    data.forEach(user => {
                        let row = table.insertRow();
                        row.insertCell(0).textContent = user.roblox_username;
                        row.insertCell(1).textContent = user.hwid;
                        row.insertCell(2).textContent = user.executions;
                        row.insertCell(3).textContent = user.executor;
                        row.insertCell(4).textContent = user.game_name;
                        row.insertCell(5).textContent = user.last_execution;
                        row.insertCell(6).textContent = user.ip_address;
                    });
                });
        </script>
    </body>
    </html>
    """

@app.route('/api/log_execution', methods=['POST'])
def log_execution():
    data = request.json
    client_ip = request.remote_addr
    
    if not data or 'roblox_username' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    hwid = data.get('hwid', str(uuid.uuid4()))
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
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
            'game_name': user[6],
            'ip_address': user[7]  # Added IP to response
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
            'roblox_username': user[1],
            'hwid': user[2],
            'executions': user[3],
            'last_execution': user[4],
            'executor': user[5],
            'game_name': user[6],
            'ip_address': user[7]  # Added IP to response
        })
    
    return jsonify(users_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
