#!/bin/bash
# Download pre-built llama.cpp binaries

echo "=== DOWNLOADING PRE-BUILT LLAMA.CPP ==="
echo

cd /moneyball
mkdir -p llama-prebuilt && cd llama-prebuilt

# Try different release versions
echo "1. Trying to download recent releases..."

# Option 1: Try b3719 release
echo "Attempting download of b3719 release..."
wget -O llama-b3719.zip "https://github.com/ggerganov/llama.cpp/releases/download/b3719/llama-b3719-bin-ubuntu-x64.zip" 2>/dev/null

if [ $? -eq 0 ] && [ -f llama-b3719.zip ]; then
    echo "✅ Downloaded successfully"
    unzip -o llama-b3719.zip
    rm llama-b3719.zip
else
    echo "❌ b3719 download failed"
    
    # Option 2: Try b3447 release
    echo "Trying b3447 release..."
    wget -O llama-b3447.zip "https://github.com/ggerganov/llama.cpp/releases/download/b3447/llama-b3447-bin-ubuntu-x64.zip" 2>/dev/null
    
    if [ $? -eq 0 ] && [ -f llama-b3447.zip ]; then
        echo "✅ Downloaded b3447"
        unzip -o llama-b3447.zip
        rm llama-b3447.zip
    else
        echo "❌ Direct download failed"
    fi
fi

# Check what we got
echo
echo "2. Checking downloaded files..."
ls -la

# Make executable
chmod +x main llama-* server 2>/dev/null

# Test the binary
echo
echo "3. Testing binary..."
if [ -f "main" ]; then
    ./main --help 2>&1 | head -10
elif [ -f "llama-cli" ]; then
    ./llama-cli --help 2>&1 | head -10
else
    echo "No binary found"
fi

echo
echo "=== ALTERNATIVE: Manual Download ==="
echo "If automatic download failed due to network restrictions:"
echo
echo "1. On your local machine with internet:"
echo "   - Go to: https://github.com/ggerganov/llama.cpp/releases"
echo "   - Download: llama-b3719-bin-ubuntu-x64.zip (or similar)"
echo "   - Add to git repo and push"
echo
echo "2. Or use curl with specific options:"
echo "   curl -L -o llama.zip https://github.com/ggerganov/llama.cpp/releases/download/b3719/llama-b3719-bin-ubuntu-x64.zip"
echo
echo "3. Or build simple version without filesystem:"
cat > /moneyball/build_simple_llama.sh << 'EOF'
#!/bin/bash
cd /moneyball
rm -rf llama.cpp-simple
git clone https://github.com/ggerganov/llama.cpp llama.cpp-simple
cd llama.cpp-simple
git checkout b3447  # Older version without filesystem issues
make clean
LLAMA_CUDA=1 make -j4 main
echo "Binary at: $(pwd)/main"
EOF
chmod +x /moneyball/build_simple_llama.sh
echo "   Run: /moneyball/build_simple_llama.sh"