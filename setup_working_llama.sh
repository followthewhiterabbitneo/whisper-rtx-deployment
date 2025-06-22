#!/bin/bash
# Set up working llama.cpp with proper paths

echo "=== SETTING UP WORKING LLAMA.CPP ==="
echo

# Use the llama-cli binary (newer version)
LLAMA_BIN="/moneyball/llama.cpp/llama-cli"
if [ ! -f "$LLAMA_BIN" ]; then
    # Fall back to main if llama-cli doesn't exist
    LLAMA_BIN="/moneyball/llama.cpp/main"
fi

echo "1. Using binary: $LLAMA_BIN"
echo

# Create proper wrapper script
echo "2. Creating optimized wrapper script..."
cat > /moneyball/llama_run.sh << 'EOF'
#!/bin/bash
# Optimized llama.cpp wrapper for RHEL8

# Set environment
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib64:$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# Use the working binary
LLAMA_BIN="/moneyball/llama.cpp/llama-cli"
[ -f "$LLAMA_BIN" ] || LLAMA_BIN="/moneyball/llama.cpp/main"

# Default model
DEFAULT_MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

# Parse arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [prompt] [options]"
    echo "Examples:"
    echo "  $0 'What is 2+2?'"
    echo "  $0 'Explain quantum physics' -n 200"
    echo "  $0 --model /path/to/model.gguf 'Your prompt'"
    exit 0
fi

# Handle model override
MODEL="$DEFAULT_MODEL"
if [ "$1" = "--model" ] || [ "$1" = "-m" ]; then
    MODEL="$2"
    shift 2
fi

# Get prompt (first argument)
PROMPT="$1"
shift

# Default prompt if none provided
[ -z "$PROMPT" ] && PROMPT="Hello! How can I help you today?"

# Run with optimal settings for RTX
exec $LLAMA_BIN \
    -m "$MODEL" \
    -p "$PROMPT" \
    -n 200 \
    --gpu-layers 33 \
    --threads 8 \
    --ctx-size 4096 \
    --temp 0.7 \
    --top-p 0.9 \
    --repeat-penalty 1.1 \
    --log-disable \
    "$@"
EOF
chmod +x /moneyball/llama_run.sh

# Create quick test script
echo "3. Creating quick test script..."
cat > /moneyball/llama_test.sh << 'EOF'
#!/bin/bash
echo "=== TESTING LLAMA.CPP ==="
echo "Simple math test..."
time /moneyball/llama_run.sh "What is 25 * 4?" -n 50

echo
echo "GPU utilization during inference:"
nvidia-smi dmon -s u -d 1 -c 5 &
MONITOR=$!
sleep 1
/moneyball/llama_run.sh "List 3 benefits of exercise" -n 100
kill $MONITOR 2>/dev/null
EOF
chmod +x /moneyball/llama_test.sh

# Create batch inference script
echo "4. Creating batch inference script..."
cat > /moneyball/llama_batch.sh << 'EOF'
#!/bin/bash
# Batch inference with llama.cpp

if [ $# -eq 0 ]; then
    echo "Usage: $0 prompt1 prompt2 prompt3..."
    echo "Or: $0 < prompts.txt"
    exit 1
fi

# Process each prompt
while IFS= read -r prompt || [ -n "$prompt" ]; do
    [ -z "$prompt" ] && continue
    echo "=== Prompt: $prompt ==="
    /moneyball/llama_run.sh "$prompt" -n 150
    echo
done < <(if [ -t 0 ]; then printf '%s\n' "$@"; else cat; fi)
EOF
chmod +x /moneyball/llama_batch.sh

# Test the setup
echo
echo "5. Quick functionality test..."
/moneyball/llama_run.sh "What is 2+2?" -n 20

echo
echo "=== SETUP COMPLETE ==="
echo "Commands available:"
echo "  /moneyball/llama_run.sh 'your prompt'    # Main inference"
echo "  /moneyball/llama_test.sh                 # Performance test"
echo "  /moneyball/llama_batch.sh                # Batch processing"
echo
echo "Examples:"
echo "  /moneyball/llama_run.sh 'Explain AI in simple terms'"
echo "  /moneyball/llama_run.sh 'Write a Python function' -n 300"
echo "  echo 'What is love?' | /moneyball/llama_batch.sh"