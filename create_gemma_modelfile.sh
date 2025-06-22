#!/bin/bash
# Create Modelfile and load Gemma into Ollama

echo "=== Loading Gemma 2 9B into Ollama ==="

# Create Modelfile
echo "1. Creating Modelfile..."
cat > /moneyball/whisper-rtx-deployment/Modelfile << 'EOF'
FROM /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 2048
PARAMETER num_gpu 999

TEMPLATE """<start_of_turn>user
{{ .Prompt }}<end_of_turn>
<start_of_turn>model
"""
EOF

echo "✓ Created Modelfile"
cat /moneyball/whisper-rtx-deployment/Modelfile

# Create the model in Ollama
echo ""
echo "2. Creating model in Ollama (this may take a minute)..."
cd /moneyball/whisper-rtx-deployment
~/run_gemma.sh create gemma2-legal -f Modelfile

# List models
echo ""
echo "3. Checking models..."
~/run_gemma.sh list

# Quick test
echo ""
echo "4. Testing model..."
time ~/run_gemma.sh run gemma2-legal "Say hello"

echo ""
echo "✓ Model ready! Now you can run summaries:"
echo "python3 simple_gpu_summary.py"