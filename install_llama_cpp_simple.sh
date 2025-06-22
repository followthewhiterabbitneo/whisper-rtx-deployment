#!/bin/bash
# Simple llama.cpp install without curl dependency

echo "=== SIMPLE LLAMA.CPP CUDA INSTALL ===="
echo "No curl required - using wget or python"
echo

cd /moneyball

# 1. Clone or update llama.cpp
echo "1. Getting llama.cpp:"
if [ -d "llama.cpp" ]; then
    cd llama.cpp
    git pull
    git clean -xdf  # Clean all build files
else
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp
fi

# 2. Simple make with CUDA
echo
echo "2. Building with CUDA (simple make):"
make clean
LLAMA_CUBLAS=1 make -j8

# 3. Check if it built
echo
echo "3. Checking build:"
if [ -f "main" ]; then
    echo "✅ main binary built!"
    ls -la main
else
    echo "❌ Build failed!"
    exit 1
fi

# 4. Test help
echo
echo "4. Testing binary:"
./main --help | head -20

# 5. Create test script
echo
echo "5. Creating test script:"
cat > /moneyball/test_llama_simple.sh << 'EOF'
#!/bin/bash
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

if [ ! -f "$MODEL" ]; then
    echo "Model not found at: $MODEL"
    exit 1
fi

echo "Testing llama.cpp GPU inference..."
echo "Prompt: What is 5+5?"
echo

# Monitor GPU in background
nvidia-smi dmon -s u -d 1 -c 10 &
MON_PID=$!

# Run inference
time /moneyball/llama.cpp/main \
    -m "$MODEL" \
    -p "What is 5+5?" \
    -n 30 \
    -ngl 999 \
    -t 8

kill $MON_PID 2>/dev/null

echo
echo "If you saw GPU utilization %, it's working!"
EOF
chmod +x /moneyball/test_llama_simple.sh

# 6. Alternative Python test server
echo
echo "6. Creating Python test helper:"
cat > /moneyball/test_llama_api.py << 'EOF'
#!/usr/bin/env python3
"""Test llama.cpp without curl"""
import subprocess
import time

print("Starting llama.cpp test...")

# Simple command
cmd = [
    "/moneyball/llama.cpp/main",
    "-m", "/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf",
    "-p", "Count from 1 to 5:",
    "-n", "50",
    "-ngl", "999",
    "-t", "8"
]

start = time.time()
result = subprocess.run(cmd, capture_output=True, text=True)
elapsed = time.time() - start

print("Output:", result.stdout)
print(f"\nTime: {elapsed:.2f} seconds")

if elapsed < 10:
    print("✅ Fast! GPU is working!")
else:
    print("❌ Slow! GPU might not be used")
EOF
chmod +x /moneyball/test_llama_api.py

echo
echo "=== BUILD COMPLETE ===="
echo "Test with:"
echo "  /moneyball/test_llama_simple.sh"
echo "  python3 /moneyball/test_llama_api.py"
echo
echo "Watch for GPU utilization % during the test!"