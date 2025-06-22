#!/bin/bash
# Set up pre-built llama.cpp binary on RHEL8

echo "=== SETTING UP PRE-BUILT LLAMA.CPP ==="
echo

# Create directory for pre-built binary
mkdir -p /moneyball/llama-prebuilt
cd /moneyball/llama-prebuilt

echo "1. Looking for pre-built binaries..."
# Check if any binaries exist
if ls llama* 2>/dev/null || ls main 2>/dev/null || ls server 2>/dev/null; then
    echo "✅ Found pre-built binaries:"
    ls -la llama* main server 2>/dev/null
else
    echo "❌ No binaries found yet"
    echo
    echo "To get pre-built binaries:"
    echo "1. Download from: https://github.com/ggerganov/llama.cpp/releases"
    echo "2. Look for 'llama-[version]-bin-linux-x64.zip'"
    echo "3. Extract to /moneyball/llama-prebuilt/"
    echo
    echo "Or try downloading older release:"
    echo "wget https://github.com/ggerganov/llama.cpp/releases/download/b2781/llama-b2781-bin-ubuntu-x64.zip"
fi

# Make binaries executable
echo
echo "2. Making binaries executable..."
chmod +x llama* main server 2>/dev/null

# Test if they work
echo
echo "3. Testing binaries..."
if [ -f "main" ]; then
    echo "Testing main binary:"
    ./main --version 2>&1 | head -5 || echo "Binary may need different libraries"
elif [ -f "llama-cli" ]; then
    echo "Testing llama-cli:"
    ./llama-cli --version 2>&1 | head -5 || echo "Binary may need different libraries"
fi

# Check library dependencies
echo
echo "4. Checking library dependencies..."
if [ -f "main" ]; then
    ldd main 2>&1 | grep "not found" || echo "✅ All libraries found"
elif [ -f "llama-cli" ]; then
    ldd llama-cli 2>&1 | grep "not found" || echo "✅ All libraries found"
fi

# Create wrapper script
echo
echo "5. Creating wrapper script..."
cat > /moneyball/llama_prebuilt.sh << 'EOF'
#!/bin/bash
# Run pre-built llama.cpp

# Set library paths
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/lib64:$LD_LIBRARY_PATH

# Find binary
BINARY=""
if [ -f "/moneyball/llama-prebuilt/main" ]; then
    BINARY="/moneyball/llama-prebuilt/main"
elif [ -f "/moneyball/llama-prebuilt/llama-cli" ]; then
    BINARY="/moneyball/llama-prebuilt/llama-cli"
else
    echo "No llama binary found!"
    exit 1
fi

# Find model
MODEL="${1:-$(find /moneyball -name "*.gguf" 2>/dev/null | grep -i llama | head -1)}"
if [ -z "$MODEL" ] || [ "$MODEL" = "$1" ]; then
    echo "Usage: $0 [model.gguf] [prompt]"
    echo "Available models:"
    find /moneyball -name "*.gguf" 2>/dev/null | head -10
    exit 1
fi

shift
PROMPT="${*:-What is 2+2?}"

echo "Binary: $BINARY"
echo "Model: $MODEL"
echo "Prompt: $PROMPT"
echo

# Run inference
$BINARY \
    -m "$MODEL" \
    -p "$PROMPT" \
    -n 100 \
    --gpu-layers 33 \
    --threads 8 \
    --temp 0.7
EOF
chmod +x /moneyball/llama_prebuilt.sh

# Create symlink for easy access
ln -sf /moneyball/llama_prebuilt.sh /moneyball/llama_gpu.sh 2>/dev/null

echo
echo "=== SETUP COMPLETE ==="
echo "Test with:"
echo "  /moneyball/llama_prebuilt.sh"
echo
echo "If binary doesn't work due to library issues, try:"
echo "1. Different pre-built version"
echo "2. Static build version"
echo "3. Ubuntu binary on RHEL (may need compat libs)"