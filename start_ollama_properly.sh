#!/bin/bash
# Start Ollama server with proper CUDA setup

echo "=== STARTING OLLAMA WITH CUDA SUPPORT ==="
echo

# 1. Kill any existing Ollama processes
echo "1. Stopping any existing Ollama processes..."
pkill -f ollama || echo "No Ollama process found"
sleep 2

# 2. Set up CUDA environment
echo "2. Setting up CUDA environment..."
export CUDA_HOME=/usr/local/cuda-12.0
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/targets/x86_64-linux/lib:/usr/lib64:$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_NUM_GPU=1
export OLLAMA_NUM_GPU_LAYERS=35

echo "CUDA_HOME: $CUDA_HOME"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"

# 3. Start Ollama server
echo
echo "3. Starting Ollama server..."
nohup ollama serve > /moneyball/ollama_server.log 2>&1 &
OLLAMA_PID=$!
echo "Started Ollama server with PID: $OLLAMA_PID"

# 4. Wait for server to start
echo "4. Waiting for server to start..."
for i in {1..10}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "✅ Ollama server is ready!"
        break
    fi
    echo "Waiting... ($i/10)"
    sleep 2
done

# 5. Check server status
echo
echo "5. Checking server status..."
curl -s http://localhost:11434/api/tags | jq '.models[].name' 2>/dev/null || echo "No models found or jq not installed"

# 6. Check what libraries Ollama loaded
echo
echo "6. Checking loaded CUDA libraries..."
lsof -p $OLLAMA_PID 2>/dev/null | grep -E "cuda|cublas" | head -5

# 7. Test inference with GPU monitoring
echo
echo "7. Testing GPU inference..."
echo "Starting GPU monitor..."
nvidia-smi dmon -s u -d 1 -c 20 &
MONITOR=$!
sleep 2

echo
echo "Running test inference..."
time ollama run llama3:8b "What is 2+2?" 2>&1 | tee /tmp/ollama_gpu_test.log

kill $MONITOR 2>/dev/null

# 8. Check logs
echo
echo "8. Checking server logs for errors..."
tail -20 /moneyball/ollama_server.log | grep -E "error|cuda|gpu|CUDA" -i || echo "No relevant messages"

echo
echo "=== STATUS ==="
echo "Ollama server PID: $OLLAMA_PID"
echo "Server log: /moneyball/ollama_server.log"
echo "To check logs: tail -f /moneyball/ollama_server.log"
echo "To stop: kill $OLLAMA_PID"