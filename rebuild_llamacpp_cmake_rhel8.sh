#!/bin/bash
# Build llama.cpp with CMake on RHEL8

echo "=== Building llama.cpp with CMake ==="

# Use /moneyball for everything
WORK_DIR="/moneyball/llama.cpp"

# Remove old home directory version if you want
if [ -d "$HOME/llama.cpp" ]; then
    echo "Found llama.cpp in home directory. Moving to /moneyball..."
    if [ ! -d "$WORK_DIR" ]; then
        mv "$HOME/llama.cpp" "$WORK_DIR"
    else
        echo "Already exists in /moneyball, using that version"
    fi
fi

# Clone if needed
if [ ! -d "$WORK_DIR" ]; then
    echo "Cloning llama.cpp to /moneyball..."
    cd /moneyball
    git clone https://github.com/ggerganov/llama.cpp
fi

cd "$WORK_DIR"
echo "Working in: $(pwd)"

# Update to latest
echo "Updating to latest version..."
git pull

# Create build directory
mkdir -p build
cd build

# Configure with CMake
echo "Configuring with CMake..."
if command -v nvcc &> /dev/null; then
    echo "✓ CUDA found! Building with GPU support..."
    cmake .. -DLLAMA_CUDA=ON
else
    echo "Building CPU version..."
    cmake ..
fi

# Build
echo "Building..."
cmake --build . --config Release -j4

# Check if executables were built
echo ""
echo "=== Checking build results ==="
if [ -f "bin/main" ]; then
    echo "✓ main built successfully"
    cp bin/main ../
else
    echo "✗ main not found"
fi

if [ -f "bin/server" ]; then
    echo "✓ server built successfully"
    cp bin/server ../
else
    echo "✗ server not found"
fi

# Create simple run script
cd "$WORK_DIR"
cat > run_gemma.sh << 'EOF'
#!/bin/bash
MODEL="/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"

echo "=== Running Gemma 2 9B ==="

# Quick test
if [ -f "./main" ]; then
    echo "Test prompt: Summarize this call"
    ./main -m "$MODEL" -n 100 -p "Summarize this call: Customer Eric Rawlins called about loan modification. Status pending. Review in 7-10 days."
else
    echo "ERROR: main executable not found"
fi

echo ""
echo "To run server: ./server -m $MODEL -c 2048 --host 0.0.0.0 --port 8080"
EOF

chmod +x run_gemma.sh

echo ""
echo "=== Build Complete ==="
echo "Location: $WORK_DIR"
echo "To test Gemma: cd $WORK_DIR && ./run_gemma.sh"
echo ""
echo "Your Gemma model: /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"