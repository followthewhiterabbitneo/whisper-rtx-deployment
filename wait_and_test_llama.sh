#!/bin/bash
# Wait for model to load and test

echo "=== MODEL IS LOADING ON GPU! ==="
echo "Llama 3 8B Instruct - 4.58 GiB"
echo "All 33 layers on GPU"
echo

# 1. Wait for model to be ready
echo "1. Waiting for model to finish loading..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags | grep -q "llama3"; then
        echo "✓ Model ready!"
        break
    fi
    echo -n "."
    sleep 2
done
echo

# 2. Check GPU memory after loading
echo
echo "2. GPU memory with model loaded:"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv

# 3. Test the model
echo
echo "3. Testing model (should be fast now):"
time curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "prompt": "What is 2+2?",
    "stream": false,
    "options": {
      "temperature": 0,
      "num_predict": 20
    }
  }' | jq -r '.response'

# 4. Test with ollama run
echo
echo "4. Testing with ollama run:"
echo "Hi" | timeout 30 ollama run llama3

# 5. Interactive test
echo
echo "5. Quick math test:"
echo "What is 10 times 5?" | ollama run llama3

# 6. Legal summary test
echo
echo "6. Legal summary test:"
cat << EOF | ollama run llama3
Create a brief legal summary:
Customer Eric Rawlins called about loan modification. Agent confirmed receipt of application.
EOF

echo
echo "=== MODEL LOADED ON GPU! ==="
echo "The model should be responding quickly now"