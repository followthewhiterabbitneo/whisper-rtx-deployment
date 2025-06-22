#!/bin/bash
# Use the loaded Llama model

echo "=== USING LOADED LLAMA MODEL ==="
echo "Model is ready in GPU memory!"
echo

# 1. Quick test
echo "1. Quick math test:"
time echo "What is 2+2? Answer in one word." | ollama run llama3

# 2. Test the API
echo
echo "2. API test:"
time curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "prompt": "What is the capital of France? Answer in one word.",
    "stream": false,
    "options": {
      "temperature": 0,
      "num_predict": 10
    }
  }' | jq -r '.response'

# 3. Legal summary test
echo
echo "3. Legal summary test:"
time curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "prompt": "Create a brief legal summary:\nClient: Eric Rawlins\nDate: June 20\nIssue: Loan modification inquiry\nAction: Application status confirmed\n\nLegal Summary:",
    "stream": false,
    "options": {
      "temperature": 0.3,
      "num_predict": 200
    }
  }' | jq -r '.response' | head -20

echo
echo "✅ Model is working! Response times should be fast since it's already loaded!"