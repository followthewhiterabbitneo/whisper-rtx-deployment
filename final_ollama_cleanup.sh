#!/bin/bash
# Final cleanup - get ONE working Ollama with Gemma

echo "=== FINAL OLLAMA CLEANUP ==="
echo "This will clean up everything and give you ONE working setup"
echo "Press Ctrl+C to cancel..."
sleep 3

# 1. Kill ALL Ollama processes
echo ""
echo "1. Killing ALL Ollama processes..."
pkill -f ollama 2>/dev/null
sleep 2
# Double check
pgrep -f ollama && echo "Some processes still running" || echo "✓ All Ollama stopped"

# 2. Clean up ports
echo ""
echo "2. Checking ports..."
lsof -i :11434 2>/dev/null && echo "Port 11434 in use"
lsof -i :11435 2>/dev/null && echo "Port 11435 in use"

# 3. Set up clean environment
echo ""
echo "3. Setting up clean environment..."
export OLLAMA_HOST="localhost:11434"
export OLLAMA_HOME="/moneyball/ollama/data"
export OLLAMA_MODELS="/moneyball/ollama/models"
export CUDA_VISIBLE_DEVICES=0
export PATH="/moneyball/ollama/bin:$PATH"

# 4. Start fresh Ollama
echo ""
echo "4. Starting fresh Ollama on port 11434..."
cd /moneyball/whisper-rtx-deployment
nohup /moneyball/ollama/bin/ollama serve > /moneyball/ollama/final_clean.log 2>&1 &
OLLAMA_PID=$!

sleep 5

# 5. Check if started
if ps -p $OLLAMA_PID > /dev/null; then
    echo "✓ Ollama started (PID: $OLLAMA_PID)"
else
    echo "Failed to start on 11434, trying 11435..."
    export OLLAMA_HOST="localhost:11435"
    nohup /moneyball/ollama/bin/ollama serve > /moneyball/ollama/final_clean.log 2>&1 &
    OLLAMA_PID=$!
    sleep 5
fi

# 6. Load Gemma model
echo ""
echo "5. Loading Gemma model..."

# Check if model exists
/moneyball/ollama/bin/ollama list

# Create modelfile
cat > /moneyball/ollama/GemmaModelfile << 'EOF'
FROM /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf

PARAMETER temperature 0.7
PARAMETER num_ctx 2048
EOF

# Create model
echo "Creating gemma2-legal model..."
/moneyball/ollama/bin/ollama create gemma2-legal -f /moneyball/ollama/GemmaModelfile

# 7. Test
echo ""
echo "6. Testing..."
time /moneyball/ollama/bin/ollama run gemma2-legal "Hello world" || echo "Model test failed"

# 8. Create final working script
cat > /moneyball/whisper-rtx-deployment/run_legal_summary.sh << 'SCRIPT'
#!/bin/bash
# Run legal summary with working Ollama

export OLLAMA_HOST="${OLLAMA_HOST:-localhost:11434}"
export OLLAMA_HOME="/moneyball/ollama/data"
export OLLAMA_MODELS="/moneyball/ollama/models"

echo "Using Ollama at: $OLLAMA_HOST"

# Simple summary test
TRANSCRIPT="Eric Rawlins called about loan modification. Application from June 1st. Under review, decision in 7-10 days."

echo "Creating legal summary..."
/moneyball/ollama/bin/ollama run gemma2-legal "Create a legal summary: $TRANSCRIPT"
SCRIPT

chmod +x /moneyball/whisper-rtx-deployment/run_legal_summary.sh

echo ""
echo "=== CLEANUP COMPLETE ==="
echo ""
echo "Ollama PID: $OLLAMA_PID"
echo "Port: ${OLLAMA_HOST}"
echo "Logs: /moneyball/ollama/final_clean.log"
echo ""
echo "Test with: ./run_legal_summary.sh"
echo ""
echo "Everything is in /moneyball/ollama/"
echo "NO system directories, NO home directory!"