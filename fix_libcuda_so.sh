#!/bin/bash
# Fix libcuda.so.1 not found error

echo "=== FIXING libcuda.so.1 ERROR ==="
echo

# 1. Find where libcuda.so actually is
echo "1. Searching for libcuda.so files..."
find /usr -name "libcuda.so*" 2>/dev/null | grep -v "/proc"
find /opt -name "libcuda.so*" 2>/dev/null

# 2. Check current library paths
echo
echo "2. Current LD_LIBRARY_PATH:"
echo $LD_LIBRARY_PATH | tr ':' '\n'

# 3. Create symlinks (run as root)
echo
echo "3. Creating fix script (run as root)..."
cat > /tmp/fix_libcuda_root.sh << 'EOF'
#!/bin/bash
# Run as root to fix libcuda.so.1

echo "Fixing libcuda.so.1 symlinks..."

# Find libcuda.so
LIBCUDA=$(find /usr -name "libcuda.so*" -type f 2>/dev/null | grep -v "/proc" | head -1)

if [ -n "$LIBCUDA" ]; then
    echo "Found: $LIBCUDA"
    LIBDIR=$(dirname "$LIBCUDA")
    
    # Create symlinks
    cd "$LIBDIR"
    if [ -f "libcuda.so" ] && [ ! -f "libcuda.so.1" ]; then
        ln -s libcuda.so libcuda.so.1
        echo "Created symlink: libcuda.so.1 -> libcuda.so"
    fi
    
    # Add to standard library path
    if [ -f "libcuda.so.1" ]; then
        ln -sf "$LIBDIR/libcuda.so.1" /usr/lib64/libcuda.so.1
        echo "Created symlink in /usr/lib64/"
    fi
    
    # Update library cache
    ldconfig
    echo "Updated library cache"
else
    echo "libcuda.so not found!"
fi

# Check NVIDIA driver
echo
echo "NVIDIA driver files:"
ls -la /usr/lib64/nvidia* 2>/dev/null | head -10
EOF
chmod +x /tmp/fix_libcuda_root.sh

echo "To fix, run as root: sudo bash /tmp/fix_libcuda_root.sh"

# 4. Workaround without root
echo
echo "4. Creating non-root workaround..."
cat > /moneyball/run_with_cuda_libs.sh << 'EOF'
#!/bin/bash
# Run commands with proper CUDA library paths

# Find libcuda.so
CUDA_PATHS=(
    "/usr/lib64"
    "/usr/lib64/nvidia"
    "/usr/lib/x86_64-linux-gnu"
    "/opt/nvidia/lib64"
    "/usr/local/cuda/lib64/stubs"
)

for path in "${CUDA_PATHS[@]}"; do
    if [ -f "$path/libcuda.so" ] || [ -f "$path/libcuda.so.1" ]; then
        export LD_LIBRARY_PATH="$path:$LD_LIBRARY_PATH"
        echo "Added to LD_LIBRARY_PATH: $path"
    fi
done

# Also try LD_PRELOAD
if [ -f "/usr/lib64/libcuda.so" ]; then
    export LD_PRELOAD="/usr/lib64/libcuda.so:$LD_PRELOAD"
elif [ -f "/usr/lib64/nvidia/libcuda.so" ]; then
    export LD_PRELOAD="/usr/lib64/nvidia/libcuda.so:$LD_PRELOAD"
fi

echo "Running with fixed library paths..."
exec "$@"
EOF
chmod +x /moneyball/run_with_cuda_libs.sh

# 5. Test if the library loads
echo
echo "5. Testing library loading..."
cat > /tmp/test_cuda_load.c << 'EOF'
#include <stdio.h>
#include <dlfcn.h>

int main() {
    void *handle = dlopen("libcuda.so.1", RTLD_LAZY);
    if (!handle) {
        printf("Failed: %s\n", dlerror());
        // Try alternative
        handle = dlopen("libcuda.so", RTLD_LAZY);
        if (!handle) {
            printf("Also failed: %s\n", dlerror());
        } else {
            printf("Success with libcuda.so\n");
        }
    } else {
        printf("Success with libcuda.so.1\n");
    }
    return 0;
}
EOF
gcc /tmp/test_cuda_load.c -o /tmp/test_cuda_load -ldl
/tmp/test_cuda_load

echo
echo "=== SOLUTIONS ==="
echo "1. Run as root: sudo bash /tmp/fix_libcuda_root.sh"
echo "2. Use wrapper: /moneyball/run_with_cuda_libs.sh ./test_llamacpp_vgpu.sh"
echo "3. Set LD_LIBRARY_PATH manually based on where libcuda.so was found above"