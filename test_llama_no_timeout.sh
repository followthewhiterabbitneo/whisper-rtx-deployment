#!/bin/bash
# Test Llama without timeout issues

echo "=== TESTING LLAMA WITHOUT TIMEOUT ==="
echo

# 1. Test with increased timeout and minimal response
echo "1. Minimal test (1 token):"
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "prompt": "Say hi",
    "stream": false,
    "options": {
      "temperature": 0,
      "num_predict": 1,
      "stop": [".", "!", "?"]
    }
  }' \
  --max-time 30 \
  -w "\nTime: %{time_total}s\n"

# 2. Test streaming mode (no timeout issues)
echo
echo "2. Streaming test:"
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "prompt": "What is 2+2?",
    "stream": true,
    "options": {
      "temperature": 0,
      "num_predict": 10
    }
  }' \
  --no-buffer

echo
echo

# 3. Direct ollama CLI (this should definitely work)
echo "3. Direct CLI test:"
echo "Hi" | ollama run llama3 --verbose

# 4. Check if model is actually generating
echo
echo "4. Checking GPU during generation:"
echo "Testing..." &
TEST_PID=$!

# Monitor GPU
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader -l 1 &
MONITOR_PID=$!

# Quick generation
echo "5" | timeout 30 ollama run llama3 "What number did I type?"

# Stop monitoring
kill $TEST_PID $MONITOR_PID 2>/dev/null

echo
echo "=== DIAGNOSIS ==="
echo "The 5-second timeout suggests:"
echo "1. Model is generating but VERY slowly"
echo "2. GPU might not be actually computing"
echo "3. Model might be in CPU mode despite GPU load"