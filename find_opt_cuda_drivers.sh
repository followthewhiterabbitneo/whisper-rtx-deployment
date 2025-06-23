#!/bin/bash
# Find CUDA/GPU drivers in /opt

echo "=== SEARCHING FOR GPU DRIVERS IN /opt ==="
echo

# 1. List what's in /opt
echo "1. Contents of /opt:"
ls -la /opt/ | grep -E "nvidia|cuda|gpu|driver" -i

# 2. Search for CUDA libraries
echo
echo "2. Searching for CUDA libraries in /opt..."
find /opt -name "libcuda*.so*" -o -name "libcublas*.so*" 2>/dev/null | head -20

# 3. Search for NVIDIA directories
echo
echo "3. NVIDIA/CUDA directories in /opt:"
find /opt -type d -name "*nvidia*" -o -name "*cuda*" 2>/dev/null | head -10

# 4. Check for driver installations
echo
echo "4. Checking common driver locations..."
for dir in /opt/nvidia /opt/cuda /opt/gpu-driver /opt/NVIDIA; do
    if [ -d "$dir" ]; then
        echo "Found: $dir"
        ls -la "$dir" | head -10
        echo "---"
    fi
done

# 5. Look for the actual runtime libraries we need
echo
echo "5. Looking for required libraries..."
echo "Need: libcudart.so (CUDA runtime)"
find /opt -name "libcudart.so*" 2>/dev/null
echo
echo "Need: libcublas.so (CUDA BLAS)"
find /opt -name "libcublas.so*" 2>/dev/null

# 6. Create script to use /opt libraries
echo
echo "6. Creating script to use /opt CUDA libraries..."
cat > /moneyball/use_opt_cuda.sh << 'EOF'
#!/bin/bash
# Use CUDA libraries from /opt

# Find CUDA libraries in /opt
OPT_CUDA=$(find /opt -name "libcudart.so*" -type f 2>/dev/null | head -1 | xargs dirname)

if [ -n "$OPT_CUDA" ]; then
    echo "Found CUDA libraries in: $OPT_CUDA"
    export LD_LIBRARY_PATH=$OPT_CUDA:$LD_LIBRARY_PATH
    
    # Check what we're using
    echo "LD_LIBRARY_PATH now includes:"
    echo $LD_LIBRARY_PATH | tr ':' '\n' | grep -E "opt|cuda"
    
    # Restart Ollama
    pkill -f ollama
    ollama serve &
    sleep 5
    
    # Test
    echo "Testing with /opt CUDA libraries..."
    nvidia-smi dmon -s u -d 1 -c 15 &
    MONITOR=$!
    sleep 1
    
    ollama run llama3:8b "Hi"
    
    kill $MONITOR 2>/dev/null
else
    echo "No CUDA libraries found in /opt"
    echo "Directories in /opt:"
    ls /opt/
fi
EOF
chmod +x /moneyball/use_opt_cuda.sh

echo
echo "=== RESULTS ==="
echo "Run: /moneyball/use_opt_cuda.sh"
echo "This will use any CUDA libraries found in /opt"