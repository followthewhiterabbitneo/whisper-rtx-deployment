#!/bin/bash
# Setup Ollama COMPLETELY in /moneyball (portable installation)

echo "=== Setting up Portable Ollama in /moneyball ==="

# Create Ollama directory structure
OLLAMA_PREFIX="/moneyball/ollama"
mkdir -p "$OLLAMA_PREFIX/bin"
mkdir -p "$OLLAMA_PREFIX/models"
mkdir -p "$OLLAMA_PREFIX/data"

# Download Ollama binary directly
echo "Downloading Ollama binary..."
cd "$OLLAMA_PREFIX/bin"

# Get the latest Ollama binary
wget -q --show-progress https://github.com/ollama/ollama/releases/download/v0.1.38/ollama-linux-amd64 -O ollama
chmod +x ollama

# Verify download
if [ ! -f "ollama" ]; then
    echo "ERROR: Failed to download Ollama"
    exit 1
fi

echo "✓ Ollama downloaded to $OLLAMA_PREFIX/bin/ollama"

# Set environment variables
export PATH="$OLLAMA_PREFIX/bin:$PATH"
export OLLAMA_HOME="$OLLAMA_PREFIX/data"
export OLLAMA_MODELS="$OLLAMA_PREFIX/models"

# Create wrapper script for easy access
cat > /moneyball/ollama/ollama-env.sh << 'EOF'
#!/bin/bash
# Source this to use Ollama from /moneyball
export PATH="/moneyball/ollama/bin:$PATH"
export OLLAMA_HOME="/moneyball/ollama/data"
export OLLAMA_MODELS="/moneyball/ollama/models"
echo "Ollama environment set. Use 'ollama' command."
EOF
chmod +x /moneyball/ollama/ollama-env.sh

# Start Ollama service
echo ""
echo "Starting Ollama service..."
cd /moneyball/whisper-rtx-deployment
"$OLLAMA_PREFIX/bin/ollama" serve > "$OLLAMA_PREFIX/ollama.log" 2>&1 &
OLLAMA_PID=$!
sleep 5

# Check if running
if ! ps -p $OLLAMA_PID > /dev/null; then
    echo "ERROR: Ollama failed to start. Check $OLLAMA_PREFIX/ollama.log"
    cat "$OLLAMA_PREFIX/ollama.log"
    exit 1
fi

echo "✓ Ollama service running (PID: $OLLAMA_PID)"

# Create Modelfile for Gemma
MODEL_PATH="/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"

echo ""
echo "Creating Modelfile..."
cat > "$OLLAMA_PREFIX/Modelfile" << EOF
FROM $MODEL_PATH

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 2048
EOF

# Create the model
echo ""
echo "Creating Gemma model in Ollama..."
"$OLLAMA_PREFIX/bin/ollama" create gemma2-legal -f "$OLLAMA_PREFIX/Modelfile"

# Test
echo ""
echo "Testing Gemma..."
"$OLLAMA_PREFIX/bin/ollama" run gemma2-legal "Summarize: Customer called about loan status."

# Create convenience script
cat > /moneyball/whisper-rtx-deployment/run_gemma_ollama.sh << 'SCRIPT_EOF'
#!/bin/bash
# Run Gemma with Ollama (portable version)
source /moneyball/ollama/ollama-env.sh
ollama run gemma2-legal "$@"
SCRIPT_EOF
chmod +x /moneyball/whisper-rtx-deployment/run_gemma_ollama.sh

# Create Python wrapper
cat > /moneyball/whisper-rtx-deployment/gemma_portable.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""Use portable Ollama from /moneyball"""
import subprocess
import os

# Set paths
os.environ['PATH'] = '/moneyball/ollama/bin:' + os.environ.get('PATH', '')
os.environ['OLLAMA_HOME'] = '/moneyball/ollama/data'
os.environ['OLLAMA_MODELS'] = '/moneyball/ollama/models'

def query_gemma(prompt):
    cmd = ['/moneyball/ollama/bin/ollama', 'run', 'gemma2-legal', prompt]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

if __name__ == "__main__":
    print(query_gemma("Summarize: Eric Rawlins loan modification call."))
PYTHON_EOF
chmod +x /moneyball/whisper-rtx-deployment/gemma_portable.py

echo ""
echo "=== Setup Complete ==="
echo "EVERYTHING is in /moneyball - no system directories used!"
echo ""
echo "Locations:"
echo "- Ollama binary: $OLLAMA_PREFIX/bin/ollama"
echo "- Models: $OLLAMA_PREFIX/models/"
echo "- Data: $OLLAMA_PREFIX/data/"
echo "- Logs: $OLLAMA_PREFIX/ollama.log"
echo ""
echo "To use:"
echo "1. Source environment: source /moneyball/ollama/ollama-env.sh"
echo "2. Quick test: /moneyball/whisper-rtx-deployment/run_gemma_ollama.sh 'Test prompt'"
echo "3. Python: /moneyball/whisper-rtx-deployment/gemma_portable.py"
echo ""
echo "Stop Ollama: kill $OLLAMA_PID"