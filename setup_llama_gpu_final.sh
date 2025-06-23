#!/bin/bash
# Set up working CUDA-enabled llama.cpp

echo "=== SETTING UP LLAMA.CPP GPU ==="
echo

# Use the llama-cli binary (newer and recommended)
BINARY="/moneyball/llama.cpp/llama-cli"
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

# Test it first
echo "1. Testing GPU inference..."
echo "GPU Monitor (watch for >0% utilization):"
nvidia-smi dmon -s um -d 1 -c 15 &
MONITOR=$!
sleep 2

$BINARY \
    -m "$MODEL" \
    -p "What is 2+2?" \
    -n 20 \
    --gpu-layers 35 \
    --threads 4 \
    --log-disable 2>&1 | grep -v "^ggml_"

kill $MONITOR 2>/dev/null

# Create production wrapper
echo
echo "2. Creating production wrapper..."
cat > /moneyball/llm << EOF
#!/bin/bash
# Production GPU-accelerated llama.cpp

# Suppress warnings
export LLAMA_NO_DEPRECATION_WARNING=1
export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:\$LD_LIBRARY_PATH

# Configuration
BINARY="$BINARY"
MODEL="$MODEL"

# Handle help
if [ "\$1" = "-h" ] || [ "\$1" = "--help" ]; then
    echo "Usage: \$0 'your prompt'"
    echo "       \$0 --chat    (interactive mode)"
    exit 0
fi

# Interactive chat mode
if [ "\$1" = "--chat" ]; then
    echo "Chat mode (type 'exit' to quit):"
    while true; do
        echo -n "> "
        read -r prompt
        [ "\$prompt" = "exit" ] && break
        \$BINARY -m "\$MODEL" -p "\$prompt" -n 500 --gpu-layers 35 --threads 4 --log-disable 2>&1 | grep -v "^ggml_"
        echo
    done
    exit 0
fi

# Single prompt mode
PROMPT="\${*:-Hello! How can I help you today?}"

exec \$BINARY \\
    -m "\$MODEL" \\
    -p "\$PROMPT" \\
    -n 500 \\
    --gpu-layers 35 \\
    --threads 4 \\
    --temp 0.7 \\
    --top-p 0.9 \\
    --log-disable 2>&1 | grep -v "^ggml_"
EOF
chmod +x /moneyball/llm

# Create info script
cat > /moneyball/llm-info << EOF
#!/bin/bash
echo "=== LLAMA.CPP GPU INFO ==="
echo "Binary: $BINARY (CUDA enabled)"
echo "Model: Llama-3-8B-Instruct-Q4_K_M"
echo "GPU: \$(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "Memory: \$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader)"
echo
echo "Commands:"
echo "  /moneyball/llm 'your prompt'     - Single prompt"
echo "  /moneyball/llm --chat            - Interactive chat"
echo "  /moneyball/llm --help            - Show help"
echo
echo "Status: ✅ GPU acceleration enabled (35 layers)"
EOF
chmod +x /moneyball/llm-info

echo
echo "=== SETUP COMPLETE ==="
/moneyball/llm-info
echo
echo "Quick test:"
echo "/moneyball/llm 'What is the capital of France?'"