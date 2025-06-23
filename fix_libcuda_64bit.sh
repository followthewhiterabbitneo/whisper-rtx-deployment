#!/bin/bash
# Fix wrong ELF class (32-bit vs 64-bit) libcuda.so error

echo "=== FIXING LIBCUDA.SO 32/64-BIT ERROR ==="
echo "Error: wrong ELF class means 32-bit library found instead of 64-bit"
echo

# 1. Find all libcuda.so files and check if they're 64-bit
echo "1. Finding 64-bit libcuda.so files..."
for lib in $(find /usr /opt -name "libcuda.so*" 2>/dev/null | grep -v "/proc"); do
    if file "$lib" | grep -q "64-bit"; then
        echo "✓ 64-bit: $lib"
    else
        echo "✗ 32-bit: $lib"
    fi
done

# 2. Find the correct 64-bit library
echo
echo "2. Locating correct 64-bit CUDA library..."
LIBCUDA_64=""
for path in \
    /usr/lib64/libcuda.so \
    /usr/lib64/nvidia/libcuda.so \
    /usr/lib/x86_64-linux-gnu/libcuda.so \
    /opt/nvidia/lib64/libcuda.so \
    /usr/local/cuda/lib64/stubs/libcuda.so; do
    if [ -f "$path" ] && file "$path" | grep -q "64-bit"; then
        LIBCUDA_64="$path"
        echo "Found 64-bit libcuda.so: $path"
        break
    fi
done

# 3. Create proper fix script
echo
echo "3. Creating 64-bit library fix..."
if [ -n "$LIBCUDA_64" ]; then
    LIBDIR_64=$(dirname "$LIBCUDA_64")
    
    cat > /moneyball/use_cuda_64bit.sh << EOF
#!/bin/bash
# Use correct 64-bit CUDA libraries

# Set 64-bit library path FIRST (before any 32-bit paths)
export LD_LIBRARY_PATH=$LIBDIR_64:\$LD_LIBRARY_PATH

# Remove any 32-bit paths
export LD_LIBRARY_PATH=\$(echo \$LD_LIBRARY_PATH | tr ':' '\n' | grep -v "lib32\|i386\|i686" | tr '\n' ':')

echo "Using 64-bit CUDA from: $LIBDIR_64"
echo "LD_LIBRARY_PATH: \$LD_LIBRARY_PATH"

# Run command
exec "\$@"
EOF
    chmod +x /moneyball/use_cuda_64bit.sh
    
    echo "Use: /moneyball/use_cuda_64bit.sh <command>"
else
    echo "❌ No 64-bit libcuda.so found!"
fi

# 4. Check system architecture
echo
echo "4. System architecture check..."
echo "Architecture: $(uname -m)"
echo "Should be: x86_64"

# 5. Create root fix for 64-bit
echo
echo "5. Creating root fix script..."
cat > /tmp/fix_libcuda_64bit_root.sh << 'EOF'
#!/bin/bash
# Fix 64-bit libcuda.so - run as root

echo "Fixing 64-bit libcuda.so..."

# Find 64-bit libcuda.so
LIBCUDA_64=$(find /usr -name "libcuda.so*" -type f 2>/dev/null | while read lib; do
    if file "$lib" | grep -q "64-bit"; then
        echo "$lib"
        break
    fi
done)

if [ -n "$LIBCUDA_64" ]; then
    echo "Found 64-bit: $LIBCUDA_64"
    
    # Create symlinks in /usr/lib64
    cd /usr/lib64
    ln -sf "$LIBCUDA_64" libcuda.so
    ln -sf "$LIBCUDA_64" libcuda.so.1
    
    echo "Created symlinks in /usr/lib64"
    
    # Update cache
    ldconfig
    echo "Updated library cache"
else
    echo "No 64-bit libcuda.so found!"
    echo "You may need to install 64-bit NVIDIA drivers"
fi

# Show current situation
echo
echo "64-bit libraries in /usr/lib64:"
ls -la /usr/lib64/libcuda* 2>/dev/null
EOF
chmod +x /tmp/fix_libcuda_64bit_root.sh

# 6. Test with llama.cpp using 64-bit libs
echo
echo "6. Creating test script with 64-bit libs..."
cat > /moneyball/test_llama_64bit.sh << 'EOF'
#!/bin/bash
# Test llama.cpp with correct 64-bit libraries

# Find 64-bit CUDA
for path in /usr/lib64 /usr/lib64/nvidia /usr/lib/x86_64-linux-gnu; do
    if [ -f "$path/libcuda.so" ]; then
        export LD_LIBRARY_PATH="$path:$LD_LIBRARY_PATH"
        break
    fi
done

echo "Testing with LD_LIBRARY_PATH: $LD_LIBRARY_PATH"

# Run llama.cpp test
cd /moneyball/whisper-rtx-deployment
./test_llamacpp_vgpu.sh
EOF
chmod +x /moneyball/test_llama_64bit.sh

echo
echo "=== SOLUTIONS ==="
echo "1. Use 64-bit wrapper: /moneyball/use_cuda_64bit.sh ./test_llamacpp_vgpu.sh"
echo "2. Fix as root: sudo bash /tmp/fix_libcuda_64bit_root.sh"
echo "3. Quick test: /moneyball/test_llama_64bit.sh"
echo
echo "The issue: A 32-bit libcuda.so is being loaded instead of 64-bit"