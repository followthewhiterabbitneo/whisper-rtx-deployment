#!/bin/bash
# Alternative: Use pre-built llama.cpp binary or build older version

echo "=== ALTERNATIVE LLAMA.CPP SOLUTIONS ==="
echo

echo "Option 1: Download pre-built binary"
echo "===================================="
cd /moneyball
mkdir -p llama-prebuilt && cd llama-prebuilt

# Download a pre-built release
echo "Downloading pre-built llama.cpp..."
wget -q https://github.com/ggerganov/llama.cpp/releases/download/b3719/llama-b3719-bin-ubuntu-x64.zip 2>/dev/null || {
    echo "Can't download directly. Manual steps:"
    echo "1. On your local machine, download:"
    echo "   https://github.com/ggerganov/llama.cpp/releases"
    echo "2. Look for Linux x64 release"
    echo "3. Upload via GitHub"
}

echo
echo "Option 2: Build older stable version"
echo "===================================="
cat > /moneyball/build_older_llama.sh << 'EOF'
#!/bin/bash
cd /moneyball
rm -rf llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
# Checkout older version before filesystem issues
git checkout b3447
# Simple make without cmake
LLAMA_CUDA=1 make -j$(nproc)
EOF
chmod +x /moneyball/build_older_llama.sh

echo
echo "Option 3: Use Ollama (already installed)"
echo "========================================"
echo "Since llama.cpp is having issues, you can use Ollama:"
echo

# Check Ollama status
if pgrep -f ollama > /dev/null; then
    echo "✅ Ollama is running"
    echo "Models available:"
    ollama list 2>/dev/null || echo "Can't list models"
else
    echo "Start Ollama:"
    echo "ollama serve &"
fi

echo
echo "Quick Ollama test:"
cat > /moneyball/test_ollama_llama.sh << 'EOF'
#!/bin/bash
echo "Testing Llama 3 via Ollama..."
time echo "What is 2+2?" | ollama run llama3:8b
EOF
chmod +x /moneyball/test_ollama_llama.sh

echo
echo "Choose an option:"
echo "1. /moneyball/build_older_llama.sh    # Build older llama.cpp"
echo "2. /moneyball/test_ollama_llama.sh    # Use Ollama instead"
echo "3. Continue debugging filesystem issue"