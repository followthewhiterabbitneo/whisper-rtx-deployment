#!/bin/bash
# Set up portable Ollama in /moneyball as root

echo "=== Setting up Portable Ollama ==="

# Create directories
echo "1. Creating directories in /moneyball/ollama..."
mkdir -p /moneyball/ollama/bin
mkdir -p /moneyball/ollama/models
mkdir -p /moneyball/ollama/data
chown -R estillmane:"domain users" /moneyball/ollama

# Download Ollama binary
echo ""
echo "2. Downloading Ollama binary..."
cd /moneyball/ollama/bin
wget -q --show-progress https://github.com/ollama/ollama/releases/download/v0.1.38/ollama-linux-amd64 -O ollama
chmod +x ollama
chown estillmane:"domain users" ollama

# Verify download
if [ -f "ollama" ]; then
    echo "✓ Ollama downloaded successfully"
    ls -la ollama
else
    echo "✗ Download failed!"
    exit 1
fi

# Create start script
echo ""
echo "3. Creating start script..."
cat > /moneyball/ollama/start_ollama.sh << 'EOF'
#!/bin/bash
# Start Ollama with GPU
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOME=/moneyball/ollama/data
export OLLAMA_MODELS=/moneyball/ollama/models
export PATH="/moneyball/ollama/bin:$PATH"

echo "Starting Ollama with GPU support..."
cd /moneyball/whisper-rtx-deployment
/moneyball/ollama/bin/ollama serve > /moneyball/ollama/ollama.log 2>&1 &
PID=$!
echo "Ollama started with PID: $PID"
echo "Logs: /moneyball/ollama/ollama.log"
EOF

chmod +x /moneyball/ollama/start_ollama.sh
chown estillmane:"domain users" /moneyball/ollama/start_ollama.sh

# Create user convenience script
echo ""
echo "4. Creating user script..."
cat > /home/estillmane/run_gemma.sh << 'EOF'
#!/bin/bash
export OLLAMA_HOME=/moneyball/ollama/data
export OLLAMA_MODELS=/moneyball/ollama/models
/moneyball/ollama/bin/ollama "$@"
EOF

chmod +x /home/estillmane/run_gemma.sh
chown estillmane:"domain users" /home/estillmane/run_gemma.sh

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Now switch to user and start Ollama:"
echo "su - estillmane"
echo "/moneyball/ollama/start_ollama.sh"
echo ""
echo "Then load Gemma:"
echo "~/run_gemma.sh create gemma2-legal -f /moneyball/whisper-rtx-deployment/Modelfile"
echo ""
echo "Or use existing model:"
echo "~/run_gemma.sh run gemma2-legal 'test prompt'"