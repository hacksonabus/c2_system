# Minimal Server/Agent (Command + Control) with some data persistance

## Components
- `server.py` - Flask + SQLite server to manage agents and commands.
- `agent.py` - Python agent that polls the server and executes commands.
- `agent.go` - Golang agent that polls the server and executes commands.

## Setup
Server
```bash
pip install flask requests
python3 server.py
```

Python Agent
```bash
python3 agent.py
```

Golang Agent
```bash
go mod init agent
go get github.com/google/uuid
go build -o agent agent.go
./agent
```

Send commands:
```bash
curl -X POST http://localhost:5000/send_command      -H "Content-Type: application/json"      -d '{"agent_id": "<agent-id>", "command": "ping"}'
```

List agents:
```bash
curl http://localhost:5000/list_agents
```

## Note
This is far from being a complete/useful implementation. There is NO security in place.
