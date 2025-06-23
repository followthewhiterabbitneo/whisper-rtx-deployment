#!/bin/bash
# Find the working CUDA-enabled llama.cpp binary

echo "=== FINDING WORKING LLAMA.CPP BINARY ==="
echo

# 1. Search for all llama.cpp binaries
echo "1. Searching for llama.cpp binaries in /moneyball..."
find /moneyball -type f \( -name "main" -o -name "llama-cli" \) -executable 2>/dev/null | while read binary; do
    echo
    echo "Found: $binary"
    echo "Size: $(ls -lh "$binary" | awk '{print $5}')"
    echo "Modified: $(ls -lh "$binary" | awk '{print $6,$7,$8}')"
    
    # Check if it has CUDA
    if ldd "$binary" 2>/dev/null | grep -q "libcuda"; then
        echo "✅ HAS CUDA SUPPORT"
        echo "CUDA libs:"
        ldd "$binary" 2>/dev/null | grep -E "cuda|cublas" | head -3
    else
        echo "❌ No CUDA support"
    fi
done

# 2. Check specific directories
echo
echo "2. Checking specific directories..."
for dir in llama-simple llama-cuda llama-cuda-arch llama.cpp llama-old; do
    if [ -d "/moneyball/$dir" ]; then
        echo
        echo "Checking /moneyball/$dir:"
        ls -la "/moneyball/$dir/main" 2>/dev/null || ls -la "/moneyball/$dir/llama-cli" 2>/dev/null || echo "  No binary found"
    fi
done

# 3. Check for symlinks
echo
echo "3. Checking for symlinks..."
ls -la /moneyball/llama* 2>/dev/null | grep -E "^l|main|llama-cli"

# 4. Check build directories by date
echo
echo "4. Recent build directories:"
ls -dt /moneyball/llama-* 2>/dev/null | head -5

# 5. Memory check - if model is loaded, binary is in use
echo
echo "5. Current GPU memory usage:"
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
echo "MB (if >1000, a model might be loaded)"

# 6. Create script to use any found CUDA binary
echo
echo "6. Creating script to use first CUDA-enabled binary found..."
cat > /moneyball/use_any_cuda_binary.sh << 'EOF'
#!/bin/bash
# Use any CUDA-enabled llama.cpp binary

echo "Finding CUDA-enabled binary..."
CUDA_BINARY=""

for binary in $(find /moneyball -type f \( -name "main" -o -name "llama-cli" \) -executable 2>/dev/null); do
    if ldd "$binary" 2>/dev/null | grep -q "libcuda"; then
        CUDA_BINARY="$binary"
        echo "Found CUDA binary: $binary"
        break
    fi
done

if [ -z "$CUDA_BINARY" ]; then
    echo "❌ No CUDA-enabled binary found!"
    echo "You may need to rebuild with: LLAMA_CUDA=1 make"
    exit 1
fi

echo "Using: $CUDA_BINARY"
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

# Test it
nvidia-smi dmon -s um -d 1 -c 10 &
MON=$!
sleep 1

$CUDA_BINARY -m "$MODEL" -p "test" -n 10 --gpu-layers 35

kill $MON 2>/dev/null
EOF
chmod +x /moneyball/use_any_cuda_binary.sh

echo
echo "=== NEXT STEPS ==="
echo "1. Look at the output above to find CUDA-enabled binaries"
echo "2. Run: /moneyball/use_any_cuda_binary.sh"
echo "3. Or tell me which binary path has CUDA support"