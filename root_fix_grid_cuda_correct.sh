#!/bin/bash
# Fix NVIDIA GRID CUDA for Ollama - RUN AS ROOT (corrected paths)

echo "=== FIXING NVIDIA GRID CUDA (ROOT) ==="
echo "This script should be run as root"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root: sudo $0"
    exit 1
fi

# 1. Find GRID RPM with correct path
echo "1. Looking for GRID driver RPM..."
# Check both possible paths
for path in "/opt/gpu_driver/Guest_Drivers" "/opt/gpu_driver/Guest_drivers"; do
    if [ -d "$path" ]; then
        echo "Checking: $path"
        GRID_RPM=$(find "$path" -name "*nvidia*grid*.rpm" -o -name "*nvidia*linux*.rpm" 2>/dev/null | head -1)
        if [ -n "$GRID_RPM" ]; then
            echo "Found: $GRID_RPM"
            break
        fi
    fi
done

if [ -z "$GRID_RPM" ]; then
    echo "Searching more broadly in /opt/gpu_driver..."
    GRID_RPM=$(find /opt/gpu_driver -name "*.rpm" 2>/dev/null | grep -i nvidia | head -1)
fi

if [ -n "$GRID_RPM" ]; then
    echo "Found RPM: $GRID_RPM"
    ls -lh "$GRID_RPM"
    
    # Check if already installed
    RPM_NAME=$(rpm -qp "$GRID_RPM" 2>/dev/null | head -1)
    if rpm -qa | grep -q "$RPM_NAME" 2>/dev/null; then
        echo "Driver already installed: $RPM_NAME"
    else
        echo "Installing GRID driver..."
        rpm -ivh "$GRID_RPM" --nodeps 2>&1 | head -20
    fi
else
    echo "No NVIDIA RPM found"
    echo "Contents of /opt/gpu_driver:"
    ls -la /opt/gpu_driver/
fi

# 2. Find where NVIDIA libraries were installed
echo
echo "2. Finding NVIDIA libraries..."
for search_path in /usr/lib64 /usr/lib /opt/nvidia /usr/lib64/nvidia /usr/lib/x86_64-linux-gnu; do
    if [ -d "$search_path" ]; then
        echo "Searching $search_path..."
        find "$search_path" -name "libcuda*.so*" -o -name "libnvidia*.so*" 2>/dev/null | head -5
    fi
done

# 3. Update library cache
echo
echo "3. Updating library cache..."
ldconfig
ldconfig -p | grep -E "cuda|nvidia" | head -10

# 4. Create symlinks for CUDA libraries
echo
echo "4. Creating CUDA library symlinks..."
# Find actual CUDA libraries
CUDA_LIBS=$(find /usr -name "libcuda.so*" -type f 2>/dev/null | grep -v "/proc" | head -5)
CUBLAS_LIBS=$(find /usr -name "libcublas.so*" -type f 2>/dev/null | grep -v "/proc" | head -5)

if [ -n "$CUDA_LIBS" ]; then
    echo "Found CUDA libraries:"
    echo "$CUDA_LIBS"
    # Create symlinks in /usr/lib64
    for lib in $CUDA_LIBS; do
        libname=$(basename "$lib")
        ln -sf "$lib" "/usr/lib64/$libname" 2>/dev/null && echo "Linked: /usr/lib64/$libname"
    done
fi

if [ -n "$CUBLAS_LIBS" ]; then
    echo "Found CUBLAS libraries:"
    echo "$CUBLAS_LIBS"
    for lib in $CUBLAS_LIBS; do
        libname=$(basename "$lib")
        ln -sf "$lib" "/usr/lib64/$libname" 2>/dev/null && echo "Linked: /usr/lib64/$libname"
    done
fi

# 5. Set up environment
echo
echo "5. Setting up system-wide CUDA environment..."
cat > /etc/profile.d/cuda-grid.sh << 'EOF'
# NVIDIA GRID CUDA environment
if [ -d /usr/lib64/nvidia ]; then
    export LD_LIBRARY_PATH=/usr/lib64/nvidia:$LD_LIBRARY_PATH
fi
export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0
EOF
chmod 644 /etc/profile.d/cuda-grid.sh

# 6. Create Ollama environment file
echo
echo "6. Creating Ollama environment configuration..."
mkdir -p /etc/sysconfig
cat > /etc/sysconfig/ollama << 'EOF'
# Ollama environment configuration
LD_LIBRARY_PATH=/usr/lib64/nvidia:/usr/lib64:/usr/local/cuda/lib64
CUDA_VISIBLE_DEVICES=0
OLLAMA_NUM_GPU=1
EOF

# 7. Test setup
echo
echo "7. Testing CUDA setup..."
cat > /tmp/test_cuda.c << 'EOF'
#include <stdio.h>
#include <dlfcn.h>

int main() {
    void *cuda = dlopen("libcuda.so", RTLD_LAZY);
    void *cublas = dlopen("libcublas.so", RTLD_LAZY);
    
    printf("libcuda.so: %s\n", cuda ? "FOUND" : "NOT FOUND");
    printf("libcublas.so: %s\n", cublas ? "FOUND" : "NOT FOUND");
    
    if (cuda) dlclose(cuda);
    if (cublas) dlclose(cublas);
    return 0;
}
EOF

gcc /tmp/test_cuda.c -o /tmp/test_cuda -ldl 2>/dev/null && /tmp/test_cuda

echo
echo "=== ROOT SETUP COMPLETE ==="
echo "Next steps:"
echo "1. Exit root"
echo "2. Source environment: source /etc/profile.d/cuda-grid.sh"
echo "3. Restart Ollama: ollama serve"
echo "4. Test GPU inference"