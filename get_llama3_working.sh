#!/bin/bash
# Find or download Llama 3 and get it working

echo "=== Getting Llama 3 8B Working ==="

# Set up Kaggle credentials
export KAGGLE_USERNAME="rikstillman"
export KAGGLE_KEY="00088fcaf41ece72a135fc980ddc6179"

# 1. Search for existing Llama 3 files
echo "1. Searching for existing Llama 3 files..."
FOUND_LLAMA=""

# Search common locations
for dir in /moneyball ~/.cache /tmp /var/tmp /moneyball/kaggle; do
    echo "Searching $dir..."
    FOUND=$(find "$dir" -name "*llama*3*.gguf" -o -name "*llama-3*.gguf" 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        echo "✓ Found: $FOUND"
        FOUND_LLAMA="$FOUND"
        break
    fi
done

# Also check for zip files
if [ -z "$FOUND_LLAMA" ]; then
    echo "Checking for zip files..."
    FOUND_ZIP=$(find /moneyball ~/.cache -name "*llama-3*.zip" 2>/dev/null | head -1)
    if [ -n "$FOUND_ZIP" ]; then
        echo "Found zip: $FOUND_ZIP"
        echo "Extracting..."
        cd /moneyball/whisper-rtx-deployment/models
        unzip -o "$FOUND_ZIP"
        FOUND_LLAMA=$(find . -name "*.gguf" | head -1)
    fi
fi

# 2. If not found, download it
if [ -z "$FOUND_LLAMA" ]; then
    echo ""
    echo "2. Llama 3 not found. Downloading..."
    
    cd /moneyball/whisper-rtx-deployment/models
    
    # Method 1: Using kaggle CLI
    if command -v kaggle >/dev/null 2>&1; then
        echo "Using kaggle CLI..."
        kaggle datasets download -d rikstillman/llama-3-8b-instruct-gguf
        
        # Extract
        if [ -f "llama-3-8b-instruct-gguf.zip" ]; then
            unzip -o llama-3-8b-instruct-gguf.zip
            FOUND_LLAMA=$(find . -name "*.gguf" | head -1)
        fi
    else
        # Method 2: Using curl
        echo "Using curl download..."
        curl -L -u $KAGGLE_USERNAME:$KAGGLE_KEY \
            -o llama-3-8b-instruct-gguf.zip \
            https://www.kaggle.com/api/v1/datasets/download/rikstillman/llama-3-8b-instruct-gguf
        
        if [ -f "llama-3-8b-instruct-gguf.zip" ]; then
            unzip -o llama-3-8b-instruct-gguf.zip
            FOUND_LLAMA=$(find . -name "*.gguf" | head -1)
        fi
    fi
fi

# 3. Set up the model
if [ -n "$FOUND_LLAMA" ]; then
    echo ""
    echo "3. Setting up Llama 3 model..."
    
    # Copy to models if not already there
    if [[ "$FOUND_LLAMA" != */moneyball/whisper-rtx-deployment/models/* ]]; then
        echo "Copying to models directory..."
        cp "$FOUND_LLAMA" /moneyball/whisper-rtx-deployment/models/
        FOUND_LLAMA="/moneyball/whisper-rtx-deployment/models/$(basename "$FOUND_LLAMA")"
    fi
    
    echo "Model at: $FOUND_LLAMA"
    ls -lh "$FOUND_LLAMA"
    
    # Create Modelfile
    cat > /moneyball/ollama/Llama3Modelfile << EOF
FROM $FOUND_LLAMA

PARAMETER temperature 0.7
PARAMETER num_ctx 4096
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"

TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a helpful assistant that creates concise legal summaries.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{{ .Prompt }}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""
EOF
    
    echo "✓ Created Modelfile"
    
    # Create model in Ollama
    echo ""
    echo "4. Creating Ollama model..."
    /moneyball/ollama/bin/ollama create llama3-legal -f /moneyball/ollama/Llama3Modelfile
    
    # Test
    echo ""
    echo "5. Testing Llama 3..."
    /moneyball/ollama/bin/ollama run llama3-legal "Summarize: Customer Eric Rawlins called about loan modification status."
    
else
    echo "ERROR: Could not find or download Llama 3"
    echo "Try manually downloading from: https://www.kaggle.com/datasets/rikstillman/llama-3-8b-instruct-gguf"
fi

# Create summary script for Llama 3
cat > /moneyball/whisper-rtx-deployment/summarize_with_llama3.py << 'PYTHON'
#!/usr/bin/env python3
"""Legal summaries with Llama 3"""
import subprocess
import os

os.environ['OLLAMA_HOME'] = '/moneyball/ollama/data'
os.environ['OLLAMA_MODELS'] = '/moneyball/ollama/models'

def summarize(text):
    prompt = f"Create a concise legal summary of this call transcript:\n{text}"
    
    result = subprocess.run(
        ["/moneyball/ollama/bin/ollama", "run", "llama3-legal", prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=60
    )
    
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

# Test
test = "Eric Rawlins called about loan modification. Application from June 1st. Under review for 7-10 days."
print("Summary:", summarize(test))
PYTHON

chmod +x /moneyball/whisper-rtx-deployment/summarize_with_llama3.py

echo ""
echo "=== Setup Complete ==="
echo "If Llama 3 works, use: ./summarize_with_llama3.py"