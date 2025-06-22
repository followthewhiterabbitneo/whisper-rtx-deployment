#!/bin/bash
# Diagnose why Ollama model creation isn't working

echo "=== Ollama Diagnostic Script ==="
echo "Finding out why model creation fails..."
echo ""

# 1. Check Ollama process
echo "1. Ollama Process Status:"
if pgrep -f "ollama serve" > /dev/null; then
    echo "✓ Ollama is running"
    ps aux | grep "ollama serve" | grep -v grep
else
    echo "✗ Ollama is NOT running!"
    echo "Starting Ollama..."
    /moneyball/ollama/bin/ollama serve > /moneyball/ollama/diagnostic.log 2>&1 &
    sleep 5
fi

# 2. Find all log files
echo ""
echo "2. Log Files:"
find /moneyball -name "*.log" -path "*/ollama/*" 2>/dev/null | head -10
find /tmp -name "*ollama*" 2>/dev/null | head -5
find /moneyball/scream/tmp -name "*ollama*" 2>/dev/null | head -5

# 3. Check Ollama directories
echo ""
echo "3. Ollama Directory Structure:"
echo "Data dir:"
ls -la /moneyball/ollama/data/ 2>/dev/null || echo "  No data directory"
echo ""
echo "Models dir:"
ls -la /moneyball/ollama/models/ 2>/dev/null || echo "  No models directory"
mkdir -p /moneyball/ollama/data /moneyball/ollama/models

# 4. Test Ollama connectivity
echo ""
echo "4. Testing Ollama API:"
curl -s http://localhost:11434/api/tags || echo "  API not responding on 11434"
curl -s http://localhost:11435/api/tags || echo "  API not responding on 11435"

# 5. Check Modelfile
echo ""
echo "5. Modelfile Contents:"
if [ -f "/moneyball/ollama/GemmaModelfile" ]; then
    cat /moneyball/ollama/GemmaModelfile
    echo ""
    # Extract path from Modelfile
    MODEL_PATH=$(grep "^FROM" /moneyball/ollama/GemmaModelfile | cut -d' ' -f2)
    echo "Model path: $MODEL_PATH"
    if [ -f "$MODEL_PATH" ]; then
        echo "✓ Model file exists"
        ls -lh "$MODEL_PATH"
        file "$MODEL_PATH" | head -1
    else
        echo "✗ Model file NOT FOUND at $MODEL_PATH"
    fi
else
    echo "✗ No Modelfile found"
fi

# 6. Try model creation with debug
echo ""
echo "6. Attempting Model Creation with Debug:"
export OLLAMA_DEBUG=1
/moneyball/ollama/bin/ollama create gemma2-test -f /moneyball/ollama/GemmaModelfile 2>&1 | tee /moneyball/ollama/create_debug.log

# 7. Check result
echo ""
echo "7. Checking Results:"
/moneyball/ollama/bin/ollama list

# 8. Alternative approach
echo ""
echo "8. Alternative Test:"
echo "Trying with inline modelfile..."
/moneyball/ollama/bin/ollama create gemma2-inline --file - <<EOF
FROM /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf
PARAMETER temperature 0.7
EOF

# 9. Final diagnostics
echo ""
echo "9. System Resources:"
echo "Disk space:"
df -h /moneyball | grep -v Filesystem
echo ""
echo "Memory:"
free -h | head -2

echo ""
echo "=== Diagnostic Complete ==="
echo "Check /moneyball/ollama/create_debug.log for details"
echo ""
echo "Common issues:"
echo "- Wrong GGUF path"
echo "- Corrupted GGUF file"
echo "- Insufficient disk space"
echo "- Ollama can't write to models directory"