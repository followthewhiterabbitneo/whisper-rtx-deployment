#!/bin/bash
# Fix Ollama GPU hang issue

echo "=== FIXING OLLAMA GPU HANG ==="
echo

# 1. Kill hanging processes
echo "1. Killing hanging Ollama processes:"
pkill -f "ollama run"
pkill -f "ollama runner"
sleep 2

# 2. Check GPU status
echo
echo "2. GPU Status:"
nvidia-smi --query-gpu=memory.used,memory.free,name --format=csv

# 3. Check if CUDA is accessible
echo
echo "3. Testing CUDA access:"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# 4. The issue might be the vGPU blocking again
echo
echo "4. Checking for vGPU issues:"
# Try to reset GPU if allowed
nvidia-smi --gpu-reset 2>&1 | head -5

# 5. Try CPU mode first
echo
echo "5. Testing Ollama in CPU mode:"
CUDA_VISIBLE_DEVICES="" ollama run llama3 "Hi" &
TEST_PID=$!

# Wait 10 seconds
sleep 10

# Check if it responded
if ps -p $TEST_PID > /dev/null; then
    echo "Still hanging in CPU mode too!"
    kill $TEST_PID
else
    echo "CPU mode worked!"
fi

# 6. Check Ollama logs
echo
echo "6. Ollama logs:"
tail -20 /tmp/ollama.log 2>/dev/null || echo "No log file"

# 7. Try with explicit CPU
echo
echo "7. Force CPU inference:"
cat > /moneyball/test_cpu_ollama.sh << 'EOF'
#!/bin/bash
export CUDA_VISIBLE_DEVICES=""
export OLLAMA_NUM_GPU=0
ollama run llama3 "Say hello" --verbose
EOF
chmod +x /moneyball/test_cpu_ollama.sh

echo
echo "=== DIAGNOSIS ==="
echo "The model loaded (4.9GB) but inference is hanging"
echo "This could be:"
echo "1. vGPU blocking CUDA operations again"
echo "2. Model trying to use GPU but failing"
echo "3. Memory allocation issue"
echo
echo "Try:"
echo "  /moneyball/test_cpu_ollama.sh"
echo
echo "Or check GPU state:"
echo "  nvidia-smi"