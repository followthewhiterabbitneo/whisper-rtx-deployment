#!/bin/bash
# Test Ollama now that it's running with GPU detected

echo "=== OLLAMA IS RUNNING WITH GPU! ==="
echo "GPU detected: NVIDIA A40-8Q with 7.8 GiB (6.9 GiB available)"
echo

# 1. List models
echo "1. Available models:"
ollama list

# 2. Test the model
echo
echo "2. Testing llama3 model:"
echo "One plus one equals" | ollama run llama3

# 3. If that hangs, try with explicit parameters
echo
echo "3. Testing with explicit parameters:"
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "What is 1+1?",
  "stream": false,
  "options": {
    "num_predict": 10,
    "temperature": 0.1
  }
}' | jq .

# 4. Check GPU usage during inference
echo
echo "4. GPU memory during inference:"
nvidia-smi --query-gpu=memory.used --format=csv,noheader &
NVIDIA_PID=$!
sleep 2
kill $NVIDIA_PID 2>/dev/null

# 5. Quick interactive test
echo
echo "5. Quick test with echo:"
echo "Hello" | timeout 10 ollama run llama3

# 6. If still hanging, check model format
echo
echo "6. Checking model info:"
ollama show llama3 --modelfile

echo
echo "=== GPU IS DETECTED! ==="
echo "If model still hangs, it might be:"
echo "1. Model format issue"
echo "2. Need to re-create the model"
echo "3. Try: ollama rm llama3 && ollama create llama3 -f Modelfile"