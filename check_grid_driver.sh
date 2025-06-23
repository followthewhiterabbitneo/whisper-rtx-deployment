#!/bin/bash
# Check NVIDIA GRID driver and extract CUDA libraries

echo "=== CHECKING NVIDIA GRID DRIVER ==="
echo

# 1. Find the exact RPM file
echo "1. Looking for GRID driver RPM..."
GRID_RPM=$(find /opt/gpu_driver -name "*nvidia*grid*.rpm" 2>/dev/null | head -1)
if [ -n "$GRID_RPM" ]; then
    echo "Found: $GRID_RPM"
    ls -lh "$GRID_RPM"
else
    echo "No GRID RPM found"
fi

# 2. Check if already installed
echo
echo "2. Checking if NVIDIA GRID driver is installed..."
rpm -qa | grep -i nvidia | grep -i grid || echo "GRID driver not installed via RPM"

# 3. Check current NVIDIA driver
echo
echo "3. Current NVIDIA driver:"
nvidia-smi --query-gpu=driver_version --format=csv,noheader

# 4. Extract RPM contents without installing
echo
echo "4. Extracting RPM contents to check libraries..."
if [ -n "$GRID_RPM" ]; then
    # Create temp directory
    TEMP_DIR="/tmp/grid_extract_$$"
    mkdir -p "$TEMP_DIR"
    
    # Extract RPM
    cd "$TEMP_DIR"
    rpm2cpio "$GRID_RPM" | cpio -idmv 2>/dev/null | grep -E "\.so|cuda" | head -20
    
    # Look for CUDA libraries
    echo
    echo "5. CUDA libraries in RPM:"
    find "$TEMP_DIR" -name "libcuda*.so*" -o -name "libcublas*.so*" 2>/dev/null | head -10
    
    # Clean up
    cd /
    rm -rf "$TEMP_DIR"
fi

# 6. Check for other driver files
echo
echo "6. Other files in Guest_driver directory:"
ls -la /opt/gpu_driver/Guest_driver/ | head -20

# 7. Look for already extracted libraries
echo
echo "7. Looking for extracted CUDA libraries..."
find /opt/gpu_driver -name "*.so*" -type f | grep -E "cuda|cublas" | head -10

# 8. Create script to use GRID libraries
echo
echo "8. Creating GRID library usage script..."
cat > /moneyball/use_grid_cuda.sh << 'EOF'
#!/bin/bash
# Use NVIDIA GRID CUDA libraries

echo "=== USING NVIDIA GRID CUDA LIBRARIES ==="

# Common GRID library locations
GRID_PATHS=(
    "/usr/lib64/nvidia"
    "/usr/lib/nvidia"
    "/opt/nvidia/lib64"
    "/opt/gpu_driver/lib64"
)

# Find CUDA libraries
FOUND_LIBS=false
for path in "${GRID_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "Checking: $path"
        if ls "$path"/libcuda*.so* 2>/dev/null; then
            export LD_LIBRARY_PATH="$path:$LD_LIBRARY_PATH"
            FOUND_LIBS=true
            echo "Added to LD_LIBRARY_PATH"
        fi
    fi
done

if [ "$FOUND_LIBS" = true ]; then
    echo
    echo "Restarting Ollama with GRID libraries..."
    pkill -f ollama
    ollama serve &
    sleep 5
    
    # Test
    echo "Testing GPU inference..."
    nvidia-smi dmon -s u -d 1 -c 15 &
    MONITOR=$!
    sleep 1
    
    ollama run llama3:8b "Test"
    
    kill $MONITOR 2>/dev/null
else
    echo "No GRID CUDA libraries found in standard locations"
    echo
    echo "You may need to:"
    echo "1. Install the GRID RPM: sudo rpm -ivh /opt/gpu_driver/Guest_driver/*grid*.rpm"
    echo "2. Or extract manually: rpm2cpio *grid*.rpm | cpio -idmv"
fi
EOF
chmod +x /moneyball/use_grid_cuda.sh

echo
echo "=== NVIDIA GRID INFO ==="
echo "GRID drivers are for vGPU (Virtual GPU) support"
echo "Your system appears to be using virtualized GPU"
echo
echo "Next steps:"
echo "1. Run: /moneyball/use_grid_cuda.sh"
echo "2. If that fails, might need to install the RPM"