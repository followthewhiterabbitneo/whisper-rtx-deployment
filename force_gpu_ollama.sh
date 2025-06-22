#!/bin/bash
# Force Ollama to use GPU

echo "=== Forcing Ollama GPU Usage ==="

# Kill all Ollama processes
echo "1. Killing existing Ollama..."
pkill -9 ollama
sleep 2

# Check GPU is available
echo "2. GPU Check:"
nvidia-smi -L
echo ""

# Clear GPU memory
echo "3. Clearing GPU memory..."
nvidia-smi --gpu-reset -i 0 2>/dev/null || echo "Cannot reset GPU (need root)"

# Start Ollama with explicit GPU settings
echo "4. Starting Ollama with GPU forced..."
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOME=/moneyball/ollama
export OLLAMA_MODELS=/moneyball/ollama/models
export OLLAMA_GPU_LAYERS=999  # Force all layers to GPU

# Start in background
cd /moneyball/whisper-rtx-deployment
nohup ollama serve > /moneyball/ollama/gpu_forced.log 2>&1 &
PID=$!

sleep 5

# Verify it's running
echo "5. Verifying..."
if ps -p $PID > /dev/null; then
    echo "✓ Ollama running (PID: $PID)"
else
    echo "✗ Failed to start"
    tail /moneyball/ollama/gpu_forced.log
    exit 1
fi

# Quick GPU test
echo ""
echo "6. GPU Speed Test..."
time ollama run gemma2-legal "Hi" 2>&1 | head -5

echo ""
echo "If still slow, the model might be too big for GPU VRAM."
echo "Try: ollama run gemma:2b 'test'"