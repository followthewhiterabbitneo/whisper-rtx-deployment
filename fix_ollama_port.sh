#!/bin/bash
# Fix Ollama port conflict and restart

echo "=== Fixing Ollama Port Conflict ==="

# Find what's using port 11434
echo "1. Checking port 11434..."
lsof -i :11434 2>/dev/null || netstat -tlnp 2>/dev/null | grep 11434

# Find Ollama processes
echo ""
echo "2. Finding Ollama processes..."
ps aux | grep -i ollama | grep -v grep

# Try to kill your own Ollama processes
echo ""
echo "3. Killing user's Ollama processes..."
# Get PIDs of ollama processes owned by current user
PIDS=$(ps aux | grep -i "ollama" | grep -v grep | grep $USER | awk '{print $2}')
if [ -n "$PIDS" ]; then
    echo "Found PIDs: $PIDS"
    for pid in $PIDS; do
        kill $pid 2>/dev/null && echo "Killed PID $pid" || echo "Cannot kill PID $pid"
    done
else
    echo "No Ollama processes found for $USER"
fi

sleep 2

# Check if port is free now
echo ""
echo "4. Checking if port is free..."
if lsof -i :11434 >/dev/null 2>&1; then
    echo "Port 11434 still in use. Starting on different port..."
    export OLLAMA_HOST="0.0.0.0:11435"
    PORT=11435
else
    echo "Port 11434 is free!"
    PORT=11434
fi

# Start Ollama with GPU
echo ""
echo "5. Starting Ollama on port $PORT..."
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOME=/moneyball/ollama
export OLLAMA_MODELS=/moneyball/ollama/models

cd /moneyball/whisper-rtx-deployment
nohup ollama serve > /moneyball/ollama/ollama_port_$PORT.log 2>&1 &
PID=$!

sleep 5

# Test
echo ""
echo "6. Testing on port $PORT..."
if [ "$PORT" = "11435" ]; then
    export OLLAMA_HOST="localhost:11435"
fi

ollama list

echo ""
echo "Ollama PID: $PID"
echo "Port: $PORT"
echo "Log: /moneyball/ollama/ollama_port_$PORT.log"

if [ "$PORT" = "11435" ]; then
    echo ""
    echo "IMPORTANT: Ollama is running on port 11435"
    echo "Use: OLLAMA_HOST=localhost:11435 ollama run gemma2-legal 'test'"
fi