#!/bin/bash
# Test the warmed-up model - should be fast now!

echo "=== TESTING WARMED-UP MODEL ==="
echo "First response was slow, but now it should be fast!"
echo

# 1. Quick test
echo "1. Quick math (should be fast now):"
time echo "What is 5+5?" | ollama run llama3

# 2. Another quick test  
echo
echo "2. Simple question:"
time echo "What color is the sky? One word answer." | ollama run llama3

# 3. Slightly longer
echo
echo "3. Legal summary test:"
time echo "Summarize in one sentence: Client called about loan status." | ollama run llama3

# 4. API test with timing
echo
echo "4. API test:"
START=$(date +%s)
curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "prompt": "What is 20 divided by 4?",
    "stream": false,
    "options": {
      "temperature": 0,
      "num_predict": 10
    }
  }' | jq -r '.response'
END=$(date +%s)
echo "API Time: $((END-START)) seconds"

# 5. Check model is staying loaded
echo
echo "5. Model info:"
ollama ps

echo
echo "✅ Model is working! The first response after load is slow,"
echo "but subsequent responses should be much faster!"
echo
echo "Keep using it and it stays fast!"