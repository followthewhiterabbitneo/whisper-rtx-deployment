#!/bin/bash
# Test llama.cpp GPU compute performance vs Ollama

echo "=== TESTING LLAMA.CPP GPU COMPUTE ==="
echo "Comparing llama.cpp direct GPU vs Ollama's CPU-on-GPU issue"
echo

# 1. Check if llama.cpp is built
if [ ! -f "/moneyball/llama.cpp/main" ]; then
    echo "❌ llama.cpp not found! Run install_llama_cpp_cuda.sh first"
    exit 1
fi

# 2. Monitor GPU during test
echo "1. Starting GPU monitor (watch for utilization %):"
nvidia-smi dmon -s um -d 1 -c 15 &
MONITOR_PID=$!
sleep 2

# 3. Test llama.cpp with GPU
echo
echo "2. Testing llama.cpp with GPU layers:"
echo "   Prompt: 'What is 10 times 10?'"
echo

START=$(date +%s.%N)
/moneyball/llama.cpp/main \
    -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
    -p "What is 10 times 10?" \
    -n 50 \
    --gpu-layers 999 \
    --threads 8 \
    --temp 0 \
    --repeat-penalty 1.0 \
    --log-disable 2>&1 | grep -v "^llama_"

END=$(date +%s.%N)
LLAMA_TIME=$(echo "$END - $START" | bc)

# Stop monitor
kill $MONITOR_PID 2>/dev/null
wait $MONITOR_PID 2>/dev/null

echo
echo "⏱️  llama.cpp time: ${LLAMA_TIME}s"

# 4. Compare with Ollama (if running)
if pgrep -f ollama > /dev/null; then
    echo
    echo "3. Comparing with Ollama (expect slow):"
    
    # Monitor GPU again
    nvidia-smi dmon -s um -d 1 -c 15 &
    MONITOR_PID=$!
    sleep 2
    
    START=$(date +%s.%N)
    echo "What is 10 times 10?" | timeout 30 ollama run llama3 2>/dev/null || echo "Timeout after 30s"
    END=$(date +%s.%N)
    OLLAMA_TIME=$(echo "$END - $START" | bc)
    
    kill $MONITOR_PID 2>/dev/null
    wait $MONITOR_PID 2>/dev/null
    
    echo "⏱️  Ollama time: ${OLLAMA_TIME}s"
fi

# 5. Performance test with longer prompt
echo
echo "4. Performance test with longer generation:"
echo "   Monitoring GPU utilization..."

nvidia-smi dmon -s um -d 1 -c 20 &
MONITOR_PID=$!
sleep 2

/moneyball/llama.cpp/main \
    -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
    -p "List 5 reasons why GPUs are faster than CPUs for AI:" \
    -n 200 \
    --gpu-layers 999 \
    --threads 8 \
    --temp 0.7 \
    --top-p 0.9 \
    --log-disable 2>&1 | grep -v "^llama_"

kill $MONITOR_PID 2>/dev/null
wait $MONITOR_PID 2>/dev/null

# 6. Create simple benchmark script
echo
echo "5. Creating quick benchmark script:"
cat > /moneyball/quick_llama_test.sh << 'EOF'
#!/bin/bash
# Quick GPU test
echo "Testing: $1"
time /moneyball/llama.cpp/main \
    -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
    -p "$1" \
    -n 100 \
    --gpu-layers 999 \
    --threads 8 \
    --log-disable 2>&1 | grep -v "^llama_"
EOF
chmod +x /moneyball/quick_llama_test.sh

echo
echo "=== RESULTS ==="
echo "✅ If you saw GPU utilization % going up (not just memory),"
echo "   then llama.cpp is properly using GPU compute!"
echo
echo "🚀 Quick test: /moneyball/quick_llama_test.sh 'your prompt'"
echo "🚀 Full control: /moneyball/llama_gpu.sh 'your prompt'"
echo
echo "Compare:"
echo "- Ollama: GPU memory used but 0% utilization (CPU compute)"
echo "- llama.cpp: GPU memory AND utilization % (GPU compute)"