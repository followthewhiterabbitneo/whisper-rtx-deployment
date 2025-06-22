#!/bin/bash
# Fix Llama 3 modelfile to use the correct GGUF file

echo "=== Fixing Llama 3 Setup ==="

# 1. Find the actual Llama 3 file
echo "1. Finding Llama 3 GGUF files..."
cd /moneyball/whisper-rtx-deployment/models
ls -lh *llama*.gguf *Llama*.gguf 2>/dev/null

# Find the correct Llama 3 file
LLAMA3_FILE=$(find . -name "*[Ll]lama-3*.gguf" -o -name "*[Ll]lama_3*.gguf" | head -1)

if [ -z "$LLAMA3_FILE" ]; then
    echo "ERROR: No Llama 3 GGUF file found!"
    echo "Files in models directory:"
    ls -la *.gguf
    exit 1
fi

LLAMA3_PATH="/moneyball/whisper-rtx-deployment/models/$(basename "$LLAMA3_FILE")"
echo ""
echo "2. Found Llama 3 file: $LLAMA3_PATH"
file "$LLAMA3_PATH" | head -1

# 3. Delete the old incorrect model
echo ""
echo "3. Removing old incorrect model..."
/moneyball/ollama/bin/ollama rm llama3-legal 2>/dev/null || echo "No old model to remove"

# 4. Create correct Modelfile
echo ""
echo "4. Creating correct Modelfile..."
cat > /moneyball/ollama/Llama3Modelfile << EOF
FROM $LLAMA3_PATH

PARAMETER temperature 0.7
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.1
PARAMETER top_k 40
PARAMETER top_p 0.9

TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a helpful legal assistant. Create concise summaries.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{{ .Prompt }}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""
EOF

echo "Modelfile contents:"
cat /moneyball/ollama/Llama3Modelfile

# 5. Create the model correctly
echo ""
echo "5. Creating Llama 3 model in Ollama..."
/moneyball/ollama/bin/ollama create llama3-legal -f /moneyball/ollama/Llama3Modelfile

# 6. List models to verify
echo ""
echo "6. Verifying model creation..."
/moneyball/ollama/bin/ollama list

# 7. Test the model
echo ""
echo "7. Testing Llama 3..."
echo "Simple test:"
/moneyball/ollama/bin/ollama run llama3-legal "Say hello" || echo "Test failed"

echo ""
echo "Legal summary test:"
/moneyball/ollama/bin/ollama run llama3-legal "Create a brief legal summary: Customer Eric Rawlins called regarding loan modification application submitted June 1st. Status is under review, decision expected in 7-10 business days." || echo "Summary test failed"

# 8. Create working summary script
cat > /moneyball/whisper-rtx-deployment/llama3_legal_summary.py << 'PYTHON'
#!/usr/bin/env python3
"""
Legal summaries using Llama 3
"""
import subprocess
import os
from pathlib import Path

# Force /moneyball paths
os.environ['OLLAMA_HOME'] = '/moneyball/ollama/data'
os.environ['OLLAMA_MODELS'] = '/moneyball/ollama/models'

def create_legal_summary(transcript_text):
    """Create legal summary using Llama 3"""
    
    prompt = f"""Create a professional legal summary for this call transcript. Include:
- Participants
- Date/Time
- Main topic
- Key points discussed
- Action items
- Next steps

Transcript:
{transcript_text[:2000]}  # Limit for context

Legal Summary:"""
    
    cmd = ["/moneyball/ollama/bin/ollama", "run", "llama3-legal", prompt]
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return "Error: Request timed out (60s)"
    except Exception as e:
        return f"Error: {str(e)}"

# Test
if __name__ == "__main__":
    test_transcript = """
    Date: June 20, 2025
    Call with Eric Rawlins regarding loan modification.
    Mr. Rawlins submitted application on June 1st.
    Application is currently under review by underwriting department.
    Decision expected within 7-10 business days.
    Customer expressed concern about upcoming payment.
    Offered forbearance options during review period.
    Reference number: SR-2025-0620-3847
    """
    
    print("Generating legal summary...")
    summary = create_legal_summary(test_transcript)
    print("\nLegal Summary:")
    print(summary)
    
    # Save to file
    output_file = Path("/moneyball/whisper-rtx-deployment/llama3_test_summary.txt")
    output_file.write_text(f"LEGAL SUMMARY (Llama 3)\n{'='*50}\n{summary}")
    print(f"\nSaved to: {output_file}")
PYTHON

chmod +x /moneyball/whisper-rtx-deployment/llama3_legal_summary.py

echo ""
echo "=== Fix Complete ==="
echo "If Llama 3 works now, use:"
echo "./llama3_legal_summary.py"