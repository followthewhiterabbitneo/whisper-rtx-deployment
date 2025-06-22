#!/bin/bash
# Start Ollama with STRICT /moneyball-only configuration

echo "=== Starting Ollama (MONEYBALL ONLY) ==="

# Kill any running Ollama
pkill -f ollama 2>/dev/null

# Set STRICT environment to force /moneyball
export OLLAMA_HOME="/moneyball/ollama/data"
export OLLAMA_MODELS="/moneyball/ollama/models"
export OLLAMA_TMPDIR="/moneyball/ollama/tmp"
export TMPDIR="/moneyball/ollama/tmp"
export HOME="/moneyball/ollama/home"  # Override HOME for Ollama

# Create all directories
mkdir -p /moneyball/ollama/data
mkdir -p /moneyball/ollama/models  
mkdir -p /moneyball/ollama/tmp
mkdir -p /moneyball/ollama/home
mkdir -p /moneyball/ollama/logs

# Start Ollama
echo "Starting Ollama with strict /moneyball paths..."
cd /moneyball/ollama  # Change to moneyball before starting

/moneyball/ollama/bin/ollama serve \
    --host 127.0.0.1:11434 \
    > /moneyball/ollama/logs/ollama_strict.log 2>&1 &

OLLAMA_PID=$!
sleep 5

# Verify it started
if ps -p $OLLAMA_PID > /dev/null; then
    echo "✓ Ollama started (PID: $OLLAMA_PID)"
    echo "Log: /moneyball/ollama/logs/ollama_strict.log"
else
    echo "✗ Failed to start"
    tail /moneyball/ollama/logs/ollama_strict.log
    exit 1
fi

# Create simple test script
cat > /moneyball/ollama/test_gemma.sh << 'EOF'
#!/bin/bash
export OLLAMA_HOME="/moneyball/ollama/data"
export OLLAMA_MODELS="/moneyball/ollama/models"
/moneyball/ollama/bin/ollama list
EOF
chmod +x /moneyball/ollama/test_gemma.sh

echo ""
echo "=== Ready ==="
echo "Everything will stay in /moneyball/ollama/"
echo ""
echo "Next steps:"
echo "1. Create model: See /moneyball/ollama/GemmaModelfile"
echo "2. Test: /moneyball/ollama/test_gemma.sh"
echo ""
echo "NO HOME DIRECTORY WILL BE USED!"