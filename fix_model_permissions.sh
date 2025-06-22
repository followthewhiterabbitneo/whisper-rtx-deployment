#!/bin/bash
# Fix model permissions and verify GGUF file

echo "=== Fixing Model Permissions and Checking GGUF ==="

# 1. Fix permissions (may need sudo)
echo "1. Fixing permissions..."
if [ -w "/moneyball/whisper-rtx-deployment/models" ]; then
    echo "Have write access, fixing as user..."
    chmod -R u+rw /moneyball/whisper-rtx-deployment/models/
else
    echo "Need sudo to fix permissions..."
    sudo chmod -R 755 /moneyball/whisper-rtx-deployment/models/
    sudo chown -R estillmane:"domain users" /moneyball/whisper-rtx-deployment/models/
fi

# 2. List files
echo ""
echo "2. Model files:"
ls -la /moneyball/whisper-rtx-deployment/models/

# 3. Check file types
echo ""
echo "3. Checking file types..."
for file in /moneyball/whisper-rtx-deployment/models/*.gguf; do
    if [ -f "$file" ]; then
        echo ""
        echo "File: $(basename "$file")"
        echo "Size: $(ls -lh "$file" | awk '{print $5}')"
        echo "Type: $(file "$file" | cut -d: -f2-)"
        
        # Check if it's actually compressed
        if file "$file" | grep -q "gzip\|compressed\|tar"; then
            echo "⚠️  This file is still compressed!"
            echo "Need to extract it properly"
        elif head -c 4 "$file" | grep -q "GGUF"; then
            echo "✓ Valid GGUF file"
        else
            echo "? Unknown format"
        fi
    fi
done

# 4. Compare sizes
echo ""
echo "4. Size comparison:"
echo "TAR.GZ files:"
ls -lh /moneyball/whisper-rtx-deployment/models/*.tar.gz 2>/dev/null || echo "No tar.gz files"
echo ""
echo "GGUF files:"
ls -lh /moneyball/whisper-rtx-deployment/models/*.gguf 2>/dev/null || echo "No gguf files"

# 5. Fix if needed
echo ""
echo "5. Checking if extraction needed..."
GGUF_FILE="/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"
TAR_FILE="/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-q5_k_m.gguf-gguf-downloaded-jun-huggingingface-v1.tar.gz"

if [ -f "$TAR_FILE" ] && file "$GGUF_FILE" 2>/dev/null | grep -q "gzip"; then
    echo "GGUF file is actually compressed. Re-extracting..."
    cd /moneyball/whisper-rtx-deployment/models/
    
    # Backup the bad file
    mv "$GGUF_FILE" "${GGUF_FILE}.compressed.bak" 2>/dev/null
    
    # Extract properly
    echo "Extracting from tar.gz..."
    tar -xzvf "$TAR_FILE"
    
    echo "Extraction complete. New files:"
    ls -la *.gguf
fi

# 6. Find correct GGUF path
echo ""
echo "6. Finding valid GGUF file..."
VALID_GGUF=""
for file in /moneyball/whisper-rtx-deployment/models/*.gguf; do
    if [ -f "$file" ] && head -c 4 "$file" 2>/dev/null | grep -q "GGUF"; then
        VALID_GGUF="$file"
        echo "✓ Found valid GGUF: $VALID_GGUF"
        break
    fi
done

# 7. Create working Modelfile
if [ -n "$VALID_GGUF" ]; then
    echo ""
    echo "7. Creating Modelfile with correct path..."
    cat > /moneyball/ollama/GemmaModelfile << EOF
FROM $VALID_GGUF

PARAMETER temperature 0.7
PARAMETER num_ctx 2048
EOF
    
    echo "Modelfile created with path: $VALID_GGUF"
    echo ""
    echo "Now run:"
    echo "/moneyball/ollama/bin/ollama create gemma2-legal -f /moneyball/ollama/GemmaModelfile"
else
    echo ""
    echo "ERROR: No valid GGUF file found!"
    echo "You may need to download or extract the model properly"
fi