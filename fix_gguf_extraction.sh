#!/bin/bash
# Fix the GGUF extraction issue

echo "=== Fixing GGUF Extraction ==="

cd /moneyball/whisper-rtx-deployment/models

# Check file sizes
echo "1. File sizes:"
ls -lh *.tar.gz 2>/dev/null
ls -lh *.gguf 2>/dev/null

# Check if GGUF is actually compressed
echo ""
echo "2. Checking GGUF file type:"
file gemma-2-9b-it-Q5_K_M.gguf

# If it's gzip/compressed, it needs extraction
if file gemma-2-9b-it-Q5_K_M.gguf | grep -E "gzip|compressed|tar"; then
    echo ""
    echo "3. GGUF is still compressed! Fixing..."
    
    # Backup the fake GGUF
    mv gemma-2-9b-it-Q5_K_M.gguf gemma-2-9b-it-Q5_K_M.gguf.fake
    
    # Extract from tar.gz
    echo "Extracting from tar.gz..."
    tar -xzf gemma-2-9b-it-q5_k_m.gguf-gguf-downloaded-jun-huggingingface-v1.tar.gz
    
    # List what was extracted
    echo ""
    echo "4. Extracted files:"
    ls -lh *.gguf
    
    # Find the real GGUF
    REAL_GGUF=$(find . -name "*.gguf" -size +1G | head -1)
    if [ -n "$REAL_GGUF" ]; then
        echo "Found real GGUF: $REAL_GGUF"
        
        # Create correct Modelfile
        cat > /moneyball/ollama/GemmaModelfile << EOF
FROM /moneyball/whisper-rtx-deployment/models/$REAL_GGUF

PARAMETER temperature 0.7
PARAMETER num_ctx 2048
EOF
        echo ""
        echo "5. Created Modelfile with correct path"
        echo "Now try: /moneyball/ollama/bin/ollama create gemma2-legal -f /moneyball/ollama/GemmaModelfile"
    fi
else
    echo "GGUF appears to be properly extracted"
    # Verify it's a real GGUF
    if head -c 4 gemma-2-9b-it-Q5_K_M.gguf | grep -q "GGUF"; then
        echo "✓ Valid GGUF file"
    else
        echo "✗ Not a valid GGUF file!"
    fi
fi

# Alternative: list tar contents
echo ""
echo "6. Contents of tar.gz:"
tar -tzf gemma-2-9b-it-q5_k_m.gguf-gguf-downloaded-jun-huggingingface-v1.tar.gz | head -10