#!/bin/bash
# Check the /opt/gpu_driver folder

echo "=== CHECKING /opt/gpu_driver ==="
echo

# 1. List contents
echo "1. Contents of /opt/gpu_driver:"
ls -la /opt/gpu_driver/ | head -20

# 2. Search for CUDA libraries
echo
echo "2. Looking for CUDA libraries..."
find /opt/gpu_driver -name "*.so*" | grep -E "cuda|cublas|cudnn|cudart" | head -20

# 3. Check for subdirectories
echo
echo "3. Subdirectories:"
find /opt/gpu_driver -maxdepth 2 -type d | head -20

# 4. Look for version info
echo
echo "4. Version information:"
find /opt/gpu_driver -name "version*" -o -name "VERSION*" -o -name "*version.txt" 2>/dev/null | head -5 | xargs cat 2>/dev/null

# 5. Check for lib directories
echo
echo "5. Library directories:"
find /opt/gpu_driver -type d -name "lib*" | head -10

# 6. Create script to use these libraries
echo
echo "6. Creating script to use /opt/gpu_driver libraries..."
cat > /moneyball/use_gpu_driver_libs.sh << 'EOF'
#!/bin/bash
# Use libraries from /opt/gpu_driver

echo "=== USING /opt/gpu_driver LIBRARIES ==="

# Find all library directories
LIB_DIRS=$(find /opt/gpu_driver -type d -name "lib*" | tr '\n' ':')

if [ -n "$LIB_DIRS" ]; then
    echo "Found library directories:"
    echo $LIB_DIRS | tr ':' '\n'
    
    # Set library path
    export LD_LIBRARY_PATH=$LIB_DIRS:$LD_LIBRARY_PATH
    export CUDA_VISIBLE_DEVICES=0
    
    # Kill and restart Ollama
    pkill -f ollama
    sleep 2
    
    echo
    echo "Starting Ollama with /opt/gpu_driver libraries..."
    ollama serve &
    OLLAMA_PID=$!
    echo "Ollama PID: $OLLAMA_PID"
    sleep 5
    
    # Test with GPU monitoring
    echo
    echo "Testing GPU inference..."
    nvidia-smi dmon -s u -d 1 -c 20 &
    MONITOR=$!
    sleep 2
    
    time ollama run llama3:8b "What is 2+2?" 2>&1
    
    kill $MONITOR 2>/dev/null
    
    echo
    echo "Check if GPU utilization went above 0%"
else
    echo "No library directories found in /opt/gpu_driver"
fi

# Also check specific files
echo
echo "Looking for specific CUDA libraries:"
for lib in libcudart.so libcublas.so libcudnn.so; do
    found=$(find /opt/gpu_driver -name "$lib*" 2>/dev/null | head -1)
    if [ -n "$found" ]; then
        echo "✓ Found: $found"
    else
        echo "✗ Missing: $lib"
    fi
done
EOF
chmod +x /moneyball/use_gpu_driver_libs.sh

echo
echo "=== NEXT STEPS ==="
echo "1. Check what's in the folder above"
echo "2. Run: /moneyball/use_gpu_driver_libs.sh"
echo "3. Watch GPU utilization during the test"