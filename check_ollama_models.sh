#!/bin/bash
# Check Ollama model status and GPU usage

echo "=== CHECKING OLLAMA MODELS ==="
echo

# 1. List models with details
echo "1. Current models:"
ollama list

# 2. Check model location and size
echo
echo "2. Model storage location:"
ls -la ~/.ollama/models/manifests/registry.ollama.ai/library/llama3/ 2>/dev/null || \
ls -la /usr/share/ollama/.ollama/models/manifests/registry.ollama.ai/library/llama3/ 2>/dev/null || \
echo "Models not in standard location"

# 3. Check actual model files
echo
echo "3. Model blob files:"
find ~/.ollama -name "*.bin" -size +1G 2>/dev/null | head -5 || \
find /usr/share/ollama -name "*.bin" -size +1G 2>/dev/null | head -5

# 4. Test without pulling
echo
echo "4. Testing model that's already loaded..."
echo "Monitoring GPU during test..."

# Monitor GPU
nvidia-smi dmon -s u -d 1 -c 15 &
MONITOR=$!
sleep 1

# Use --nowordwrap to avoid manifest pull
echo "Test" | timeout 30 ollama run llama3:8b --nowordwrap 2>&1 | grep -v "pulling" | head -20

kill $MONITOR 2>/dev/null

# 5. Check Ollama settings
echo
echo "5. Checking Ollama GPU settings..."
echo "OLLAMA_NUM_GPU_LAYERS: ${OLLAMA_NUM_GPU_LAYERS:-not set}"
echo "CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-not set}"

# 6. Force local model loading
echo
echo "6. Creating script to force local model..."
cat > /moneyball/ollama_local_only.sh << 'EOF'
#!/bin/bash
# Force Ollama to use local model only

export OLLAMA_MODELS=~/.ollama/models
export OLLAMA_NUM_GPU_LAYERS=35
export CUDA_VISIBLE_DEVICES=0

echo "Using local model only..."
echo "What is 2+2?" | ollama run llama3:8b --nowordwrap
EOF
chmod +x /moneyball/ollama_local_only.sh

echo
echo "=== QUICK FIX ==="
echo "To skip manifest pulling:"
echo "1. Use --nowordwrap flag"
echo "2. Run: /moneyball/ollama_local_only.sh"
echo
echo "If GPU still at 0%, the issue is CUDA libraries, not model loading"