#!/bin/bash
# Debug why Ollama won't start

echo "=== Debugging Ollama Startup ==="

# 1. Check if binary exists and is executable
echo "1. Checking Ollama binary..."
if [ -f "/moneyball/ollama/bin/ollama" ]; then
    echo "✓ Binary exists"
    ls -la /moneyball/ollama/bin/ollama
    file /moneyball/ollama/bin/ollama
else
    echo "✗ Binary not found!"
    echo "Contents of /moneyball/ollama/bin:"
    ls -la /moneyball/ollama/bin/
fi

# 2. Try running with direct output (no background)
echo ""
echo "2. Testing direct run (not in background)..."
export OLLAMA_HOME="/moneyball/ollama/data"
export OLLAMA_MODELS="/moneyball/ollama/models"

# Run in foreground to see errors
echo "Running: /moneyball/ollama/bin/ollama --version"
/moneyball/ollama/bin/ollama --version 2>&1

echo ""
echo "3. Trying to serve (will show errors)..."
echo "Press Ctrl+C after seeing the error"
/moneyball/ollama/bin/ollama serve 2>&1 | head -20

# 4. Check for port conflicts
echo ""
echo "4. Checking ports..."
netstat -tlnp 2>/dev/null | grep -E "11434|11435" || lsof -i :11434 -i :11435

# 5. Check system limits
echo ""
echo "5. System limits..."
ulimit -a | grep -E "files|processes"

# 6. Alternative: try running with strace to see why it dies
echo ""
echo "6. If you want detailed debug, run:"
echo "strace /moneyball/ollama/bin/ollama serve 2>&1 | head -100"