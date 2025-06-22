#!/bin/bash
# Find and rebuild llama.cpp on RHEL8

echo "=== Finding and Building llama.cpp ==="

# Check common locations
LLAMA_DIRS=(
    "$HOME/llama.cpp"
    "/moneyball/llama.cpp"
    "$PWD/llama.cpp"
    "/moneyball/projects/llama.cpp"
)

FOUND_DIR=""
for dir in "${LLAMA_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ Found llama.cpp at: $dir"
        FOUND_DIR="$dir"
        break
    fi
done

if [ -z "$FOUND_DIR" ]; then
    echo "llama.cpp not found. Cloning fresh copy..."
    cd /moneyball
    git clone https://github.com/ggerganov/llama.cpp
    FOUND_DIR="/moneyball/llama.cpp"
fi

cd "$FOUND_DIR"
echo "Working in: $(pwd)"

# Check if executables exist
if [ -f "main" ] && [ -f "server" ]; then
    echo "✓ Executables already exist"
    echo "  - main: $(ls -la main)"
    echo "  - server: $(ls -la server)"
else
    echo "Building llama.cpp..."
    
    # Clean previous build
    make clean 2>/dev/null
    
    # Build with GPU support if available
    if command -v nvcc &> /dev/null; then
        echo "CUDA found, building with GPU support..."
        make LLAMA_CUBLAS=1 -j4
    else
        echo "Building CPU version..."
        make -j4
    fi
    
    # Check build results
    if [ -f "main" ]; then
        echo "✓ main built successfully"
    else
        echo "✗ main build failed"
    fi
    
    if [ -f "server" ]; then
        echo "✓ server built successfully"
    else
        echo "✗ server build failed"
    fi
fi

# Create test script
cat > test_gemma_now.sh << 'EOF'
#!/bin/bash
MODEL="/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"

echo "=== Testing Gemma Model ==="
echo "Model: $MODEL"

# Simple test
./main -m "$MODEL" -n 50 -p "Summarize: The customer called about a loan."

echo ""
echo "To run server:"
echo "./server -m $MODEL -c 2048 --host 0.0.0.0 --port 8080"
EOF

chmod +x test_gemma_now.sh

echo ""
echo "=== Build Complete ==="
echo "Location: $FOUND_DIR"
echo "To test: cd $FOUND_DIR && ./test_gemma_now.sh"
echo ""
echo "To run server:"
echo "cd $FOUND_DIR"
echo "./server -m /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf -c 2048"