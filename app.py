from flask import Flask, request, jsonify, render_template
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

# Database setup for Render
def get_db():
    # Create database in a writable location
    db_path = os.path.join(os.getcwd(), 'executions.db')
    db = sqlite3.connect(db_path)
    
    # Create tables if they don't exist
    db.execute('''CREATE TABLE IF NOT EXISTS executions
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT,
                 executor TEXT,
                 hwid TEXT,
                 timestamp DATETIME)''')
    db.execute('''CREATE TABLE IF NOT EXISTS stats
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 total INTEGER DEFAULT 0)''')
    
    # Initialize stats if empty
    if db.execute("SELECT COUNT(*) FROM stats").fetchone()[0] == 0:
        db.execute("INSERT INTO stats (total) VALUES (0)")
        db.commit()
    
    return db

@app.route('/')
def index():
    try:
        db = get_db()
        total = db.execute("SELECT total FROM stats WHERE id=1").fetchone()[0]
        recent = db.execute("SELECT username, executor, timestamp FROM executions ORDER BY timestamp DESC LIMIT 10").fetchall()
        db.close()
        return render_template('index.html', total_count=total, recent_executions=recent)
    except Exception as e:
        return f"Database error: {str(e)}", 500

@app.route('/log', methods=['POST'])
def log_execution():
    if not request.json or not all(k in request.json for k in ['username', 'executor', 'hwid']):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    try:
        db = get_db()
        db.execute("INSERT INTO executions (username, executor, hwid, timestamp) VALUES (?, ?, ?, ?)",
                 (request.json['username'], request.json['executor'], request.json['hwid'], datetime.now()))
        db.execute("UPDATE stats SET total = total + 1 WHERE id=1")
        db.commit()
        total = db.execute("SELECT total FROM stats WHERE id=1").fetchone()[0]
        return jsonify({'status': 'success', 'total': total})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
