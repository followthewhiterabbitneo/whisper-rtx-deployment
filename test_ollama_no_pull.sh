#!/bin/bash
# Test Ollama GPU without pulling manifest

echo "=== TESTING OLLAMA GPU (NO MANIFEST PULL) ==="
echo

# 1. Check what models are already available
echo "1. Currently available models:"
ollama list

# 2. Test with existing model
echo
echo "2. Testing with already loaded model..."
echo "Starting GPU monitor..."

# Monitor GPU
nvidia-smi dmon -s u -d 1 -c 30 &
MONITOR_PID=$!
sleep 2

# Test with simple prompt and timeout
echo
echo "Running inference (30 second timeout)..."
START=$(date +%s)
timeout 30 bash -c 'echo "2+2=" | ollama run llama3:8b --nowordwrap' 2>&1 | tee /tmp/quick_test.log
END=$(date +%s)

kill $MONITOR_PID 2>/dev/null

echo
echo "Test took: $((END-START)) seconds"

# 3. Alternative: Use API directly
echo
echo "3. Testing via API (avoids manifest check)..."
cat > /moneyball/test_ollama_api.sh << 'EOF'
#!/bin/bash
# Test Ollama via API

# Check if server is running
if ! curl -s http://localhost:11434/api/tags >/dev/null; then
    echo "Ollama server not running!"
    exit 1
fi

echo "Testing Ollama API directly..."

# Monitor GPU
nvidia-smi dmon -s u -d 1 -c 20 &
MONITOR=$!
sleep 1

# Send API request
curl -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama3:8b",
        "prompt": "What is 2+2?",
        "stream": false,
        "options": {
            "num_predict": 20,
            "temperature": 0
        }
    }' 2>/dev/null | jq '.response' 2>/dev/null || echo "API call failed"

kill $MONITOR 2>/dev/null

echo
echo "Check if GPU usage went above 0%"
EOF
chmod +x /moneyball/test_ollama_api.sh

# 4. Force local only mode
echo
echo "4. Creating force-local script..."
cat > /moneyball/ollama_local_test.sh << 'EOF'
#!/bin/bash
# Force Ollama to use local model only

export OLLAMA_OFFLINE=1
export OLLAMA_MODELS=~/.ollama/models

echo "Testing in offline mode (no manifest pull)..."

# Monitor GPU
echo "GPU Usage Monitor:"
nvidia-smi dmon -s u -d 1 -c 20 &
MONITOR=$!
sleep 1

# Quick test
echo "Test" | timeout 20 ollama run llama3:8b --nowordwrap 2>&1

kill $MONITOR 2>/dev/null
EOF
chmod +x /moneyball/ollama_local_test.sh

# 5. Check GPU memory to confirm model is loaded
echo
echo "5. Checking GPU memory (model should be loaded):"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv

echo
echo "=== QUICK TEST OPTIONS ==="
echo "1. API test: /moneyball/test_ollama_api.sh"
echo "2. Offline mode: /moneyball/ollama_local_test.sh"
echo "3. Skip Ollama: Use llama.cpp directly"
echo
echo "If manifest pulling is blocking, try the API or offline mode"