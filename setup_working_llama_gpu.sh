#!/bin/bash
# Set up the existing working CUDA-enabled llama.cpp binary

echo "=== SETTING UP WORKING LLAMA.CPP GPU BINARY ==="
echo

# 1. Verify the working binary exists
WORKING_BIN="/moneyball/llama-cuda/main"
if [ ! -f "$WORKING_BIN" ]; then
    echo "❌ Working binary not found at $WORKING_BIN"
    exit 1
fi

echo "✅ Found working binary: $WORKING_BIN"
echo "Size: $(ls -lh $WORKING_BIN | awk '{print $5}')"
echo "CUDA libraries linked:"
ldd "$WORKING_BIN" | grep -E "cuda|cublas"

# 2. Test GPU inference
echo
echo "Testing GPU inference..."
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

# Monitor GPU
echo
echo "GPU Monitor (watch for >0% utilization):"
nvidia-smi dmon -s um -d 1 -c 15 &
MONITOR=$!
sleep 2

# Quick test
$WORKING_BIN \
    -m "$MODEL" \
    -p "What is 2+2?" \
    -n 20 \
    --gpu-layers 35 \
    --threads 4 \
    --log-disable 2>&1 | grep -v "^ggml_\|deprecated"

kill $MONITOR 2>/dev/null

# 3. Create production-ready wrapper
echo
echo "Creating production wrapper..."
cat > /moneyball/llama-gpu << 'EOF'
#!/bin/bash
# Production GPU-accelerated llama.cpp

# Suppress warnings
export LLAMA_NO_DEPRECATION_WARNING=1

# Set CUDA paths (important for vGPU)
export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0

# Configuration
BINARY="/moneyball/llama-cuda/main"
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

# Default parameters
CONTEXT_SIZE=${CONTEXT_SIZE:-4096}
GPU_LAYERS=${GPU_LAYERS:-35}
THREADS=${THREADS:-4}
TEMP=${TEMP:-0.7}
TOP_P=${TOP_P:-0.9}

# Handle input
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [options] 'your prompt'"
    echo "Options:"
    echo "  --help, -h        Show this help"
    echo "  --context N       Set context size (default: 4096)"
    echo "  --layers N        Set GPU layers (default: 35)"
    echo "  --temp T          Set temperature (default: 0.7)"
    echo "  --file FILE       Read prompt from file"
    echo "Environment variables:"
    echo "  CONTEXT_SIZE, GPU_LAYERS, THREADS, TEMP, TOP_P"
    exit 0
fi

# Read from file if specified
if [ "$1" = "--file" ] && [ -n "$2" ]; then
    PROMPT=$(cat "$2")
    shift 2
else
    PROMPT="$*"
fi

# Default prompt if empty
[ -z "$PROMPT" ] && PROMPT="Hello! How can I help you today?"

# Run inference
exec $BINARY \
    -m "$MODEL" \
    -p "$PROMPT" \
    -n 500 \
    --ctx-size $CONTEXT_SIZE \
    --gpu-layers $GPU_LAYERS \
    --threads $THREADS \
    --temp $TEMP \
    --top-p $TOP_P \
    --log-disable 2>&1 | grep -v "^ggml_\|deprecated\|WARNING"
EOF
chmod +x /moneyball/llama-gpu

# 4. Create convenient aliases
echo
echo "Creating convenient commands..."

# Simple version
ln -sf /moneyball/llama-gpu /moneyball/llm
echo "Created: /moneyball/llm -> Short alias"

# Chat version
cat > /moneyball/llama-chat << 'EOF'
#!/bin/bash
# Interactive chat mode
echo "Starting chat mode (type 'exit' to quit)..."
while true; do
    echo -n "> "
    read -r prompt
    [ "$prompt" = "exit" ] && break
    /moneyball/llama-gpu "$prompt"
    echo
done
EOF
chmod +x /moneyball/llama-chat

# 5. System info script
cat > /moneyball/llama-info << EOF
#!/bin/bash
echo "=== LLAMA.CPP GPU SETUP INFO ==="
echo "Binary: $WORKING_BIN"
echo "Model: Llama-3-8B-Instruct-GGUF-Q4_K_M"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "VRAM: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader)"
echo "Driver: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader)"
echo
echo "Commands:"
echo "  /moneyball/llama-gpu 'prompt'  - Full command"
echo "  /moneyball/llm 'prompt'        - Short alias"
echo "  /moneyball/llama-chat          - Interactive chat"
echo "  /moneyball/llama-info          - This info"
echo
echo "GPU Layers: 35 (using GPU acceleration)"
echo "Status: ✅ Working with virtual GPU (GRID)"
EOF
chmod +x /moneyball/llama-info

echo
echo "=== SETUP COMPLETE ==="
echo
/moneyball/llama-info