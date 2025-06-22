#!/bin/bash
# Try a smaller, pre-built model instead of the GGUF

echo "=== Using Pre-built Gemma Model ==="

# Make sure Ollama is running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "Starting Ollama..."
    /moneyball/ollama/bin/ollama serve > /moneyball/ollama/logs/serve.log 2>&1 &
    sleep 5
fi

# Pull a working model from Ollama library
echo "1. Pulling Gemma 2B model (smaller, more stable)..."
/moneyball/ollama/bin/ollama pull gemma:2b

# List models
echo ""
echo "2. Available models:"
/moneyball/ollama/bin/ollama list

# Test it
echo ""
echo "3. Testing Gemma 2B..."
time /moneyball/ollama/bin/ollama run gemma:2b "Summarize: Eric Rawlins called about loan modification status."

# If that works, try the 7B
echo ""
echo "4. If 2B works, try larger model:"
echo "/moneyball/ollama/bin/ollama pull gemma:7b"

echo ""
echo "=== Alternative: Convert GGUF ==="
echo "The GGUF file might be incompatible with this Ollama version."
echo "Options:"
echo "1. Use pre-built models (gemma:2b, gemma:7b)"
echo "2. Download a different GGUF version"
echo "3. Use the model on your RTX machine instead"