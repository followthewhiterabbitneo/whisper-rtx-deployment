#!/bin/bash
# Download a compatible Gemma GGUF model

echo "=== Getting Compatible Gemma Model ==="

cd /moneyball/whisper-rtx-deployment/models

# Option 1: Try a different quantization
echo "1. Available GGUF models for Gemma:"
echo "   - Gemma 2B (smaller, faster)"
echo "   - Gemma 7B (medium)"
echo "   - Different quantizations (Q4_K_M, Q5_K_M, Q8_0)"

# Since we can't download, let's test the existing GGUF differently
echo ""
echo "2. Testing existing GGUF with llama.cpp directly..."

# Try to validate the GGUF
echo ""
echo "3. Checking GGUF header..."
od -c /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf | head -5

# Check model info
echo ""
echo "4. Model details:"
strings /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf | grep -E "gemma|version|arch" | head -20

# Alternative: Use the model differently
echo ""
echo "5. Alternative approach - use llama.cpp directly:"
echo ""
echo "Since Ollama crashes, you could:"
echo "a) Use the model on your RTX machine where it works"
echo "b) Try text-generation-webui which handles GGUFs well"
echo "c) Convert to a different format"

# Create a simple Python alternative
cat > /moneyball/whisper-rtx-deployment/simple_summary_no_ollama.py << 'EOF'
#!/usr/bin/env python3
"""
Simple rule-based summarizer without Gemma
"""
import re

def summarize_transcript(text):
    """Extract key information without ML"""
    summary = []
    
    # Extract names
    names = re.findall(r'(?:Mr\.|Ms\.|Mrs\.)?\s*([A-Z][a-z]+ [A-Z][a-z]+)', text)
    if names:
        summary.append(f"Participants: {', '.join(set(names[:2]))}")
    
    # Extract dates
    dates = re.findall(r'(June|July|August) \d{1,2}', text)
    if dates:
        summary.append(f"Dates mentioned: {', '.join(dates[:2])}")
    
    # Key phrases
    if 'loan modification' in text.lower():
        summary.append("Topic: Loan Modification")
    if 'application' in text.lower():
        summary.append("Status: Application under review")
    if re.search(r'\d+.{0,3}days', text):
        days = re.search(r'(\d+.{0,3}days)', text).group(1)
        summary.append(f"Timeline: {days}")
    
    return '\n'.join(summary) if summary else "No key information extracted"

# Test
test_text = """Eric Rawlins called about loan modification status. 
Application submitted June 1st. Under review, decision in 7-10 days."""

print("Rule-based Summary:")
print(summarize_transcript(test_text))
EOF

chmod +x /moneyball/whisper-rtx-deployment/simple_summary_no_ollama.py

echo ""
echo "6. Created fallback summarizer without Gemma"
echo "Run: ./simple_summary_no_ollama.py"