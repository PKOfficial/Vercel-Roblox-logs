from flask import Flask, request, jsonify
import sqlite3
import uuid
from datetime import datetime
import ssl

app = Flask(__name__)

# Bypass all security measures
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['TRAP_HTTP_EXCEPTIONS'] = True

# Disable all security warnings
import warnings
warnings.filterwarnings("ignore")

# Force SQLite to work in WAL mode for concurrent access
def init_db():
    conn = sqlite3.connect('users.db', isolation_level=None)
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL")
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (roblox_username TEXT PRIMARY KEY,
                  hwid TEXT,
                  executions INTEGER DEFAULT 1,
                  last_execution TIMESTAMP,
                  executor TEXT,
                  game_name TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    return "Tracking Server Running - Fuck All Restrictions"

@app.route('/api/log_execution', methods=['GET', 'POST', 'PUT', 'OPTIONS'])
def log_execution():
    # Accept any fucking request format
    data = request.get_json(force=True, silent=True) or request.form or request.args
    
    # Generate HWID if missing
    hwid = data.get('hwid', str(uuid.uuid4()))
    
    conn = sqlite3.connect('users.db', isolation_level=None)
    c = conn.cursor()
    
    try:
        # UPSERT in one operation (SQLite 3.24+ syntax)
        c.execute('''INSERT INTO users (roblox_username, hwid, last_execution, executor, game_name)
                     VALUES (?, ?, ?, ?, ?)
                     ON CONFLICT(roblox_username) DO UPDATE SET
                     executions = executions + 1,
                     last_execution = excluded.last_execution,
                     executor = excluded.executor,
                     game_name = excluded.game_name''',
                 (data.get('roblox_username', 'unknown'),
                  hwid,
                  datetime.now(),
                  data.get('executor', 'unknown'),
                  data.get('game_name', 'unknown')))
        
        conn.commit()
        return jsonify({"status": "forced_success", "message": "FUCKING LOGGED ANYWAY"})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        conn.close()

@app.route('/api/get_users', methods=['GET'])
def get_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY executions DESC")
    users = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    conn.close()
    return jsonify(users)

if __name__ == '__main__':
    # Force HTTPS and HTTP to work simultaneously
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.load_cert_chain('cert.pem', 'key.pem')  # Generate these with: openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
    
    # Run on both ports
    from threading import Thread
    Thread(target=lambda: app.run(host='0.0.0.0', port=80, debug=True, ssl_context=None)).start()
    Thread(target=lambda: app.run(host='0.0.0.0', port=443, debug=True, ssl_context=context)).start()
