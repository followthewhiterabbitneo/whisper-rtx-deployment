#!/bin/bash
# Root-based Ollama cleanup and GPU setup

echo "=== Root Ollama Cleanup and GPU Setup ==="

if [ "$EUID" -ne 0 ]; then 
    echo "Running as root..."
    sudo "$0" "$@"
    exit
fi

echo "Running as root (UID: $EUID)"

# 1. Stop ALL Ollama services and processes
echo ""
echo "1. Stopping ALL Ollama processes..."
systemctl stop ollama 2>/dev/null
pkill -9 ollama
killall -9 ollama 2>/dev/null

# 2. Clean up system Ollama
echo ""
echo "2. Removing system Ollama installation..."
rm -f /usr/local/bin/ollama
rm -rf /usr/local/lib/ollama
rm -f /etc/systemd/system/ollama.service
systemctl daemon-reload

# 3. Check what's on port 11434
echo ""
echo "3. Checking port 11434..."
lsof -i :11434
fuser -k 11434/tcp 2>/dev/null  # Kill anything on port

# 4. Remove Ollama user/group
echo ""
echo "4. Removing Ollama system user..."
userdel ollama 2>/dev/null
groupdel ollama 2>/dev/null

# 5. Clear GPU
echo ""
echo "5. GPU status..."
nvidia-smi

# 6. Set up for user
echo ""
echo "6. Setting up Ollama for user estillmane..."

# Switch back to user
su - estillmane << 'EOF'
echo "Running as user: $(whoami)"

# Set environment
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOME=/moneyball/ollama
export OLLAMA_MODELS=/moneyball/ollama/models
export PATH="/moneyball/ollama/bin:$PATH"

# Check if portable Ollama exists
if [ -f "/moneyball/ollama/bin/ollama" ]; then
    echo "Using portable Ollama from /moneyball"
    OLLAMA_BIN="/moneyball/ollama/bin/ollama"
else
    echo "Downloading Ollama to /moneyball..."
    mkdir -p /moneyball/ollama/bin
    cd /moneyball/ollama/bin
    wget -q https://github.com/ollama/ollama/releases/download/v0.1.38/ollama-linux-amd64 -O ollama
    chmod +x ollama
    OLLAMA_BIN="/moneyball/ollama/bin/ollama"
fi

# Start Ollama with GPU
echo ""
echo "Starting Ollama with GPU..."
cd /moneyball/whisper-rtx-deployment
nohup $OLLAMA_BIN serve > /moneyball/ollama/root_fixed.log 2>&1 &
OLLAMA_PID=$!

sleep 5

# Test
echo ""
echo "Testing Ollama..."
$OLLAMA_BIN list
$OLLAMA_BIN run gemma2-legal "Quick test" || echo "Model not loaded yet"

echo ""
echo "Ollama PID: $OLLAMA_PID"
echo "Everything in: /moneyball/ollama/"
EOF

echo ""
echo "=== Setup Complete ==="
echo "Ollama is now running as user with GPU support"
echo "Check: su - estillmane -c 'ollama list'"