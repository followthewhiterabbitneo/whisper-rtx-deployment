#!/bin/bash
# Fix NVIDIA GRID CUDA for Ollama - RUN AS ROOT

echo "=== FIXING NVIDIA GRID CUDA (ROOT) ==="
echo "This script should be run as root"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root: sudo $0"
    exit 1
fi

# 1. Find and install GRID RPM
echo "1. Looking for GRID driver RPM..."
GRID_RPM=$(find /opt/gpu_driver -name "*nvidia*grid*.rpm" 2>/dev/null | head -1)
if [ -n "$GRID_RPM" ]; then
    echo "Found: $GRID_RPM"
    
    # Check if already installed
    if rpm -qa | grep -i nvidia-grid; then
        echo "GRID driver already installed"
    else
        echo "Installing GRID driver..."
        rpm -ivh "$GRID_RPM" || echo "Installation failed - may already be installed"
    fi
fi

# 2. Update library cache
echo
echo "2. Updating library cache..."
ldconfig -v 2>/dev/null | grep -E "cuda|nvidia" | head -10

# 3. Create CUDA library symlinks
echo
echo "3. Creating CUDA library symlinks..."
# Common locations where GRID installs libraries
GRID_LIB_PATHS=(
    "/usr/lib64/nvidia"
    "/usr/lib/x86_64-linux-gnu/nvidia"
    "/opt/nvidia/lib64"
)

for path in "${GRID_LIB_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "Found NVIDIA libraries at: $path"
        # Create symlinks in standard location
        for lib in "$path"/libcuda*.so* "$path"/libcublas*.so*; do
            if [ -f "$lib" ]; then
                libname=$(basename "$lib")
                ln -sf "$lib" "/usr/lib64/$libname" 2>/dev/null && echo "Linked: $libname"
            fi
        done
    fi
done

# 4. Set up environment for all users
echo
echo "4. Setting up system-wide CUDA environment..."
cat > /etc/profile.d/cuda-grid.sh << 'EOF'
# NVIDIA GRID CUDA environment
export CUDA_VISIBLE_DEVICES=0
export LD_LIBRARY_PATH=/usr/lib64/nvidia:/usr/lib64:$LD_LIBRARY_PATH
EOF
chmod 644 /etc/profile.d/cuda-grid.sh

# 5. Configure Ollama systemd service (if exists)
echo
echo "5. Configuring Ollama service..."
if [ -f /etc/systemd/system/ollama.service ] || [ -f /usr/lib/systemd/system/ollama.service ]; then
    mkdir -p /etc/systemd/system/ollama.service.d
    cat > /etc/systemd/system/ollama.service.d/cuda.conf << EOF
[Service]
Environment="LD_LIBRARY_PATH=/usr/lib64/nvidia:/usr/lib64"
Environment="CUDA_VISIBLE_DEVICES=0"
EOF
    systemctl daemon-reload
    systemctl restart ollama
    echo "Ollama service restarted with CUDA environment"
else
    echo "No Ollama systemd service found"
fi

# 6. Test CUDA libraries
echo
echo "6. Testing CUDA library availability..."
ldconfig -p | grep -E "libcuda|libcublas" | head -10

# 7. Create test script
echo
echo "7. Creating test script..."
cat > /moneyball/test_grid_cuda_root.sh << 'EOF'
#!/bin/bash
# Test GRID CUDA setup

echo "Testing NVIDIA GRID CUDA setup..."

# Source environment
source /etc/profile.d/cuda-grid.sh

# Check libraries
echo "CUDA libraries:"
ldconfig -p | grep cuda | head -5

# Start Ollama
pkill -f ollama
ollama serve &
OLLAMA_PID=$!
sleep 5

# Test with GPU monitor
echo
echo "Testing GPU inference..."
nvidia-smi dmon -s u -d 1 -c 20 &
MONITOR=$!
sleep 2

ollama run llama3:8b "What is 2+2?"

kill $MONITOR 2>/dev/null
kill $OLLAMA_PID 2>/dev/null
EOF
chmod +x /moneyball/test_grid_cuda_root.sh

echo
echo "=== ROOT SETUP COMPLETE ==="
echo "1. GRID driver checked/installed"
echo "2. CUDA libraries linked to standard locations"
echo "3. System environment configured"
echo
echo "Test with: /moneyball/test_grid_cuda_root.sh"
echo "Then switch back to normal user and test Ollama"