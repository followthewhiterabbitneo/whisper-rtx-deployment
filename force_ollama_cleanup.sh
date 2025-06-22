#!/bin/bash
# Force Ollama to release GPU memory

echo "=== Force Ollama GPU Memory Release ==="
echo

# 1. Check what's actually loaded
echo "1. Models currently in GPU memory:"
ollama ps
echo

# 2. Current GPU usage
echo "2. Current GPU memory usage:"
nvidia-smi | grep ollama
echo

# 3. Try to unload models properly
echo "3. Attempting to unload models..."
# This should unload models from memory
ollama run llama3-legal <<< "/bye"
ollama run llama3 <<< "/bye"
sleep 2

# 4. Force stop
echo
echo "4. Force stopping Ollama..."
ollama stop
pkill -f "ollama serve"
pkill -f ollama
sleep 3

# 5. Check if memory freed
echo
echo "5. GPU memory after force stop:"
nvidia-smi --query-gpu=memory.used --format=csv,noheader

# 6. If still using memory, need full restart
echo
echo "6. If memory still not freed, do:"
echo "   sudo pkill -9 ollama"
echo "   sudo nvidia-smi --gpu-reset (if allowed)"
echo
echo "The 5.3GB might be:"
echo "- A model that won't unload"
echo "- Ollama bug keeping model in VRAM"
echo "- Need to use 'ollama rm' to fully remove"

# 7. Check which models are installed
echo
echo "7. Installed models:"
ollama list

echo
echo "To completely remove a model from disk AND memory:"
echo "  ollama rm model-name"
echo
echo "To see which model is stuck in memory:"
echo "  ollama ps"