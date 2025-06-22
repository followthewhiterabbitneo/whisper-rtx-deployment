#!/bin/bash
# Restart Ollama properly and test

echo "=== RESTARTING OLLAMA PROPERLY ==="
echo "GPU is working fine - this is an Ollama issue"
echo

# 1. Kill ALL Ollama processes
echo "1. Killing all Ollama processes:"
pkill -9 -f ollama
sleep 3

# 2. Clear any locks or temp files
echo
echo "2. Clearing Ollama temp files:"
rm -f /tmp/ollama*
rm -f /moneyball/ollama/tmp/*

# 3. Start Ollama with verbose logging
echo
echo "3. Starting Ollama with debug logging:"
export OLLAMA_MODELS=/moneyball/ollama/models
export OLLAMA_DEBUG=1
export OLLAMA_KEEP_ALIVE=0  # Don't keep models loaded
ollama serve 2>&1 | tee /tmp/ollama_debug.log &
OLLAMA_PID=$!
sleep 5

# 4. Check if it started
echo
echo "4. Checking Ollama status:"
if ps -p $OLLAMA_PID > /dev/null; then
    echo "✓ Ollama server running (PID: $OLLAMA_PID)"
else
    echo "✗ Ollama failed to start"
    tail -20 /tmp/ollama_debug.log
    exit 1
fi

# 5. List models
echo
echo "5. Current models:"
ollama list

# 6. Try running with verbose output
echo
echo "6. Testing model with verbose output:"
timeout 15 ollama run llama3 "Say hi" --verbose

# 7. If that hangs, try pulling a tiny model
echo
echo "7. Alternative - try a tiny model:"
timeout 15 ollama run tinyllama:1b "hi" 2>&1 || echo "Also hanging"

# 8. Check logs
echo
echo "8. Ollama debug logs:"
tail -30 /tmp/ollama_debug.log | grep -E "(error|Error|ERROR|failed|gpu|cuda)"

echo
echo "=== ALTERNATIVE APPROACH ==="
echo "If Ollama keeps hanging, we can use llama.cpp directly:"
echo
echo "1. Install llama.cpp:"
echo "   git clone https://github.com/ggerganov/llama.cpp"
echo "   cd llama.cpp && make LLAMA_CUDA=1"
echo
echo "2. Run directly:"
echo "   ./main -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf -p 'Hello' -n 50"