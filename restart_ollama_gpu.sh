#!/bin/bash
# Restart Ollama with GPU support

echo "=== Restarting Ollama with GPU ==="

# Kill existing Ollama
echo "1. Stopping Ollama..."
pkill -f ollama
sleep 2

# Check GPU
echo "2. GPU Status:"
nvidia-smi -L

# Start with GPU
echo "3. Starting Ollama with GPU..."
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOME=/moneyball/ollama
export OLLAMA_MODELS=/moneyball/ollama/models

cd /moneyball/whisper-rtx-deployment
nohup ollama serve > /moneyball/ollama/ollama_gpu.log 2>&1 &
OLLAMA_PID=$!

sleep 5

# Test
echo "4. Testing GPU inference..."
time ollama run gemma2-legal "Hello" --verbose

echo ""
echo "Ollama PID: $OLLAMA_PID"
echo "Logs: /moneyball/ollama/ollama_gpu.log"
echo ""
echo "If still slow, try smaller model:"
echo "ollama pull gemma:2b"
echo "ollama run gemma:2b 'test'"