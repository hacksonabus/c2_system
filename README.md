# Minimal Client/Server (Command + Control Demo)

## Components
- `server.py` — Flask + SQLite server to manage agents and commands.
- `agent.py` — Client agent that polls the server and executes commands.

## Setup
```bash
pip install flask requests
python3 server.py
python3 agent.py
```

Send commands:
```bash
curl -X POST http://localhost:5000/send_command      -H "Content-Type: application/json"      -d '{"agent_id": "<agent-id>", "command": "info"}'
```

List agents:
```bash
curl http://localhost:5000/list_agents
```
