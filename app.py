from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import time

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('executions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS executions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  url TEXT,
                  username TEXT,
                  executor TEXT,
                  hwid TEXT,
                  timestamp DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  total_executions INTEGER DEFAULT 0)''')
    
    # Initialize stats if empty
    c.execute("SELECT COUNT(*) FROM stats")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO stats (total_executions) VALUES (0)")
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    # Get execution count for the current URL
    current_url = request.url_root
    conn = sqlite3.connect('executions.db')
    c = conn.cursor()
    
    # Get URL-specific count
    c.execute("SELECT COUNT(*) FROM executions WHERE url=?", (current_url,))
    url_count = c.fetchone()[0]
    
    # Get total count
    c.execute("SELECT total_executions FROM stats WHERE id=1")
    total_count = c.fetchone()[0]
    
    # Get recent executions
    c.execute("SELECT username, executor, timestamp FROM executions ORDER BY timestamp DESC LIMIT 10")
    recent_executions = c.fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         url_count=url_count,
                         total_count=total_count,
                         recent_executions=recent_executions,
                         current_url=current_url)

@app.route('/log_execution', methods=['POST'])
def log_execution():
    data = request.json
    
    # Validate required fields
    if not all(key in data for key in ['username', 'executor', 'hwid']):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    # Insert into database
    conn = sqlite3.connect('executions.db')
    c = conn.cursor()
    
    try:
        # Log the execution
        c.execute("INSERT INTO executions (url, username, executor, hwid, timestamp) VALUES (?, ?, ?, ?, ?)",
                 (request.url_root, data['username'], data['executor'], data['hwid'], datetime.now()))
        
        # Update total count
        c.execute("UPDATE stats SET total_executions = total_executions + 1 WHERE id=1")
        
        conn.commit()
        
        # Get updated counts
        c.execute("SELECT COUNT(*) FROM executions WHERE url=?", (request.url_root,))
        url_count = c.fetchone()[0]
        
        c.execute("SELECT total_executions FROM stats WHERE id=1")
        total_count = c.fetchone()[0]
        
        return jsonify({
            'status': 'success',
            'url_count': url_count,
            'total_count': total_count
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
