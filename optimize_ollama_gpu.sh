#!/bin/bash
# Optimize Ollama GPU usage

echo "=== Ollama GPU Memory Optimization ==="
echo

# 1. Check what models are loaded
echo "1. Currently loaded Ollama models:"
ollama list
echo

# 2. Check running models
echo "2. Models currently in memory:"
ollama ps
echo

# 3. Show model details
echo "3. Model sizes:"
for model in $(ollama list | tail -n +2 | awk '{print $1}'); do
    echo -n "  $model: "
    ollama show $model --modelfile 2>/dev/null | grep -E "PARAMETER|size" | head -3
done
echo

# 4. Memory usage before/after
echo "4. Current GPU memory:"
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
echo "MiB used"

# Options to free memory
echo
echo "=== Options to Free GPU Memory ==="
echo
echo "Option 1: Unload current model"
echo "  ollama stop"
echo
echo "Option 2: Remove unused models"
echo "  ollama rm model-name"
echo
echo "Option 3: Use smaller quantized models"
echo "  ollama pull llama3:8b-instruct-q4_0  # 4-bit quantized"
echo
echo "Option 4: Set memory limit"
echo "  export OLLAMA_MAX_LOADED_MODELS=1"
echo "  export OLLAMA_NUM_PARALLEL=1"
echo
echo "The 5.3GB is likely a larger model (Llama 3 70B?) already loaded."
echo "Your llama3-legal model only needs ~1.8GB."