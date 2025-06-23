#!/bin/bash
# Find where llama.cpp builds its binaries

echo "=== FINDING LLAMA.CPP BINARIES ==="
echo

# 1. Check latest build directory
echo "1. Checking latest build directory..."
LATEST_BUILD=$(ls -dt /moneyball/llama-cuda-* 2>/dev/null | head -1)
if [ -d "$LATEST_BUILD" ]; then
    echo "Latest build: $LATEST_BUILD"
    cd "$LATEST_BUILD"
    
    echo
    echo "2. Searching for binaries..."
    find . -type f -executable -name "*llama*" -o -name "main" 2>/dev/null | grep -v ".git"
    
    echo
    echo "3. Checking common locations:"
    for dir in . build build/bin bin examples/main examples/llama-cli; do
        if [ -d "$dir" ]; then
            echo "Checking $dir:"
            ls -la "$dir" | grep -E "llama|main" | grep -v ".cpp\|.o\|.h"
        fi
    done
    
    echo
    echo "4. Checking if build actually succeeded..."
    if [ -f "build.log" ]; then
        echo "Last 20 lines of build.log:"
        tail -20 build.log
        echo
        echo "Checking for errors:"
        grep -i "error\|fail" build.log | tail -10
    fi
fi

# 2. Check what modern llama.cpp builds
echo
echo "5. Understanding modern llama.cpp structure..."
cat > /moneyball/build_llama_correct.sh << 'EOF'
#!/bin/bash
# Build llama.cpp correctly for modern versions

echo "=== BUILDING LLAMA.CPP (CORRECT METHOD) ==="

cd /moneyball
rm -rf llama-test
git clone https://github.com/ggerganov/llama.cpp llama-test
cd llama-test

echo "1. Checking build system..."
if [ -f "CMakeLists.txt" ]; then
    echo "This version uses CMake"
    
    # CMake build
    mkdir build
    cd build
    cmake .. -DGGML_CUDA=ON -DLLAMA_CURL=OFF
    make -j$(nproc)
    
    echo
    echo "CMake build output:"
    find . -type f -executable | head -20
else
    echo "This version uses Make"
    
    # Make build  
    GGML_CUDA=1 make -j$(nproc)
    
    echo
    echo "Make build output:"
    ls -la | grep -v ".cpp\|.o\|.h"
fi

echo
echo "Finding executables:"
find . -type f -executable -size +1M | grep -v ".so\|.a"
EOF
chmod +x /moneyball/build_llama_correct.sh

# 3. Quick check of working binary
echo
echo "6. Checking previous working binary..."
if [ -f "/moneyball/llama-cuda/main" ]; then
    echo "Previous working binary exists: /moneyball/llama-cuda/main"
    echo "Size: $(ls -lh /moneyball/llama-cuda/main | awk '{print $5}')"
    echo "CUDA linked: $(ldd /moneyball/llama-cuda/main | grep -c cuda) CUDA libraries"
fi

echo
echo "=== NEXT STEPS ==="
echo "1. Run: /moneyball/build_llama_correct.sh"
echo "2. This will show exactly what gets built"
echo "3. Modern llama.cpp might require CMake instead of make"