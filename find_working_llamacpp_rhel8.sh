#!/bin/bash
# Find any working llama.cpp executables

echo "=== Finding Working llama.cpp Executables ==="

# Check in llama.cpp directory
echo "Checking /moneyball/llama.cpp..."
cd /moneyball/llama.cpp 2>/dev/null || { echo "Directory not found"; exit 1; }

echo "Current directory: $(pwd)"
echo ""

# Find all potential executables
echo "Looking for executables..."
find . -type f -executable -name "*main*" -o -name "*server*" -o -name "*llama*" 2>/dev/null | grep -v ".git" | sort

echo ""
echo "Checking specific locations..."

# Check common executable names and locations
EXECUTABLES=(
    "./main"
    "./server"
    "./llama-cli"
    "./llama-server"
    "./build/bin/main"
    "./build/bin/server"
    "./build/bin/llama-cli"
    "./build/bin/llama-server"
    "./build/main"
    "./build/server"
    "./examples/main/main"
    "./examples/server/server"
)

FOUND_MAIN=""
FOUND_SERVER=""

for exe in "${EXECUTABLES[@]}"; do
    if [ -f "$exe" ] && [ -x "$exe" ]; then
        echo "✓ Found: $exe"
        if [[ "$exe" == *"main"* ]] || [[ "$exe" == *"cli"* ]]; then
            FOUND_MAIN="$exe"
        fi
        if [[ "$exe" == *"server"* ]]; then
            FOUND_SERVER="$exe"
        fi
    fi
done

echo ""
echo "=== Testing Found Executables ==="

MODEL="/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"

if [ -n "$FOUND_MAIN" ]; then
    echo "Testing with: $FOUND_MAIN"
    echo "Command: $FOUND_MAIN -m \"$MODEL\" -n 30 -p \"Summary:\""
    echo ""
    $FOUND_MAIN -m "$MODEL" -n 30 -p "Summary: Customer called about loan." 2>&1 | head -20
else
    echo "No main/cli executable found"
fi

echo ""
echo "=== Alternative: Use Pre-built Binary ==="
echo "Download pre-built llama.cpp:"
echo "wget https://github.com/ggerganov/llama.cpp/releases/latest/download/llama-linux-x64.zip"
echo "unzip llama-linux-x64.zip"

echo ""
echo "=== Create Simple Test Script ==="

cat > test_gemma_simple.sh << 'EOF'
#!/bin/bash
# Simple Gemma test
MODEL="/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"

# Find any working executable
for exe in ./main ./llama-cli ./build/bin/llama-cli ./build/bin/main; do
    if [ -f "$exe" ] && [ -x "$exe" ]; then
        echo "Using: $exe"
        $exe -m "$MODEL" -n 50 -p "Summarize: Eric Rawlins called about his loan modification application status."
        exit 0
    fi
done

echo "No executable found!"
EOF

chmod +x test_gemma_simple.sh

echo ""
echo "Created: test_gemma_simple.sh"
echo "Try: ./test_gemma_simple.sh"