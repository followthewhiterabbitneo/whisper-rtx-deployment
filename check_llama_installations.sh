#!/bin/bash
# Check all llama.cpp installations and find working binary

echo "=== CHECKING LLAMA.CPP INSTALLATIONS ==="
echo

echo "1. Looking for llama directories..."
find /moneyball -maxdepth 2 -type d -name "*llama*" 2>/dev/null | sort

echo
echo "2. Looking for llama binaries..."
find /moneyball -maxdepth 4 -name "main" -type f -executable 2>/dev/null | head -10
find /moneyball -maxdepth 4 -name "llama-cli" -type f -executable 2>/dev/null | head -10

echo
echo "3. Testing each binary..."
for binary in $(find /moneyball -maxdepth 4 \( -name "main" -o -name "llama-cli" \) -type f -executable 2>/dev/null | head -10); do
    echo
    echo "Testing: $binary"
    $binary --version 2>&1 | head -1 || echo "Failed"
done

echo
echo "4. Looking for GGUF models..."
find /moneyball -name "*.gguf" -type f 2>/dev/null | grep -i llama | head -5

echo
echo "5. Creating unified test script..."
cat > /moneyball/test_all_llamas.sh << 'EOF'
#!/bin/bash
# Test all llama installations

# Find a model
MODEL=$(find /moneyball -name "*.gguf" -type f 2>/dev/null | grep -i llama | head -1)
if [ -z "$MODEL" ]; then
    echo "No Llama GGUF model found!"
    exit 1
fi

echo "Using model: $MODEL"
echo "Testing prompt: 'What is 2+2?'"
echo

# Test each binary
for binary in $(find /moneyball -maxdepth 4 \( -name "main" -o -name "llama-cli" \) -type f -executable 2>/dev/null); do
    echo "=================="
    echo "Testing: $binary"
    echo "=================="
    
    # Test with timeout
    timeout 30 $binary \
        -m "$MODEL" \
        -p "What is 2+2?" \
        -n 20 \
        --gpu-layers 33 \
        --threads 4 2>&1 | grep -v "^llama_" | head -20
    
    if [ $? -eq 0 ]; then
        echo "✅ This binary works!"
        echo "Full path: $binary"
        
        # Create symlink
        ln -sf "$binary" /moneyball/working_llama
        echo "Created symlink: /moneyball/working_llama"
        break
    else
        echo "❌ Failed or timed out"
    fi
    echo
done
EOF
chmod +x /moneyball/test_all_llamas.sh

echo
echo "=== NEXT STEPS ==="
echo "Run: /moneyball/test_all_llamas.sh"
echo "This will test each binary and create a symlink to the working one"