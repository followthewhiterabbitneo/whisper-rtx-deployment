#!/bin/bash
# Check Ollama status after restart

echo "=== CHECKING OLLAMA STATUS ==="
echo

# 1. Check if Ollama is running
echo "1. Ollama processes:"
ps aux | grep ollama | grep -v grep

# 2. Check if port is listening
echo
echo "2. Ollama port (11434):"
netstat -tlnp 2>/dev/null | grep 11434 || ss -tlnp | grep 11434

# 3. Test Ollama API
echo
echo "3. Testing Ollama API:"
curl -s http://localhost:11434/api/tags | jq . 2>/dev/null || echo "API not responding"

# 4. List models
echo
echo "4. Models available:"
ollama list

# 5. Try to run model with very short timeout
echo
echo "5. Quick model test (5 second timeout):"
timeout 5 ollama run llama3 "1+1=" 2>&1

# 6. Check GPU memory
echo
echo "6. GPU memory status:"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv

# 7. Start Ollama if not running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo
    echo "7. Ollama not running! Starting it..."
    export OLLAMA_MODELS=/moneyball/ollama/models
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 5
    echo "Started Ollama"
fi

# 8. Final test
echo
echo "8. Final test with explicit model path:"
cat > /tmp/test_prompt.txt << EOF
Hi
EOF

timeout 10 ollama run llama3 < /tmp/test_prompt.txt

echo
echo "If still hanging, let's use llama.cpp directly instead!"