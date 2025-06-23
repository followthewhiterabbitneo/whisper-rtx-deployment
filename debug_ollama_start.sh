#\!/bin/bash
# Debug why Ollama won't start

echo "=== DEBUGGING OLLAMA START ISSUE ==="
echo

# 1. Check if Ollama is installed
echo "1. Checking Ollama installation..."
which ollama || echo "❌ Ollama not found in PATH"

# 2. Check if already running
echo
echo "2. Checking if Ollama is already running..."
ps aux  < /dev/null |  grep -E "ollama|OLLAMA" | grep -v grep

# 3. Try to start in foreground
echo
echo "3. Trying to start Ollama (will show errors)..."
timeout 5 ollama serve 2>&1 || echo "Start failed or timed out"

# 4. Check port
echo
echo "4. Checking port 11434..."
lsof -i :11434 2>/dev/null || echo "Port is free"

echo
echo "Try manually: ollama serve"
