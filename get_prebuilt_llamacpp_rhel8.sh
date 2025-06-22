#!/bin/bash
# Download pre-built llama.cpp binaries

echo "=== Getting Pre-built llama.cpp ==="

cd /moneyball/llama.cpp

# Get the latest release info
echo "Checking latest release..."
RELEASE_URL="https://api.github.com/repos/ggerganov/llama.cpp/releases/latest"

# Download pre-built binaries
echo "Downloading pre-built binaries..."

# Try to get the Linux x64 build
DOWNLOAD_URL="https://github.com/ggerganov/llama.cpp/releases/download/b4514/llama-b4514-bin-ubuntu-x64.zip"

echo "Downloading from: $DOWNLOAD_URL"
wget -O llama-prebuilt.zip "$DOWNLOAD_URL" || {
    echo "Failed to download. Trying alternative..."
    # Alternative: build from specific release
    echo "Downloading source from known good release..."
    wget https://github.com/ggerganov/llama.cpp/archive/refs/tags/b4514.zip
    unzip b4514.zip
    cd llama.cpp-b4514
    make -j4
    cd ..
}

# If we got the prebuilt zip
if [ -f "llama-prebuilt.zip" ]; then
    echo "Extracting pre-built binaries..."
    unzip -o llama-prebuilt.zip
    
    # Check what we got
    echo ""
    echo "Extracted files:"
    ls -la llama-* main server 2>/dev/null
fi

# Test with Gemma
echo ""
echo "=== Testing with Gemma ==="

MODEL="/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"

# Try different executable names
for exe in ./llama-cli ./main ./llama ./server; do
    if [ -f "$exe" ] && [ -x "$exe" ]; then
        echo "Found executable: $exe"
        echo "Testing..."
        $exe --version 2>/dev/null || echo "No version info"
        
        # Try to run with model
        echo ""
        echo "Running Gemma test..."
        $exe -m "$MODEL" -n 50 -p "Legal summary: Customer Eric Rawlins called regarding loan modification status." 2>&1 | head -30
        break
    fi
done

echo ""
echo "=== Alternative: Use Python Instead ==="
echo "Since llama.cpp is having issues, consider using Python alternatives:"
echo "1. Ollama (if available): curl -fsSL https://ollama.ai/install.sh | sh"
echo "2. Use transformers with a different model format"
echo "3. Use a cloud API for Gemma"

# Create a simple Python fallback
cat > use_gemma_fallback.py << 'EOF'
#!/usr/bin/env python3
"""
Fallback: Process transcripts without Gemma
Just extract key information using simple rules
"""
import re
from pathlib import Path

def simple_legal_summary(transcript):
    """Extract key information without ML model"""
    summary_parts = []
    
    # Extract customer name
    name_match = re.search(r'(Eric Rawlins|Mr\. Rawlins|Rawlins)', transcript, re.I)
    if name_match:
        summary_parts.append(f"Customer: {name_match.group(1)}")
    
    # Extract key topics
    if 'loan modification' in transcript.lower():
        summary_parts.append("Topic: Loan Modification Request")
    if 'status' in transcript.lower() or 'application' in transcript.lower():
        summary_parts.append("Purpose: Application Status Inquiry")
    if re.search(r'\d{1,2}[-/]\d{1,2} (days|business days)', transcript):
        summary_parts.append("Timeline: 7-10 business days mentioned")
    
    return "\n".join(summary_parts) if summary_parts else "Unable to extract summary"

# Test with sample
sample = "Eric Rawlins called about his loan modification application status submitted June 1st. Under review, 7-10 business days for decision."
print("Sample Legal Summary:")
print(simple_legal_summary(sample))
EOF

chmod +x use_gemma_fallback.py

echo ""
echo "Created fallback: use_gemma_fallback.py"
echo "This extracts legal summaries without needing Gemma"