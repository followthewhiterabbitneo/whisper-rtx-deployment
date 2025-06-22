#!/bin/bash
# Debug why Ollama isn't receiving requests

echo "=== DEBUGGING OLLAMA CONNECTION ==="
echo

# 1. Check if Ollama is listening
echo "1. Checking if Ollama is listening on port 11434:"
netstat -tlnp 2>/dev/null | grep 11434 || ss -tlnp | grep 11434 || lsof -i :11434

# 2. Try curl directly
echo
echo "2. Testing with curl:"
curl -v http://localhost:11434/api/tags 2>&1 | head -20

# 3. Check Ollama process
echo
echo "3. Ollama processes:"
ps aux | grep ollama | grep -v grep

# 4. Test with different addresses
echo
echo "4. Testing different addresses:"
echo "  - localhost:11434"
curl -s http://localhost:11434/api/tags | jq . 2>/dev/null || echo "Failed"

echo "  - 127.0.0.1:11434"
curl -s http://127.0.0.1:11434/api/tags | jq . 2>/dev/null || echo "Failed"

echo "  - 0.0.0.0:11434"
curl -s http://0.0.0.0:11434/api/tags | jq . 2>/dev/null || echo "Failed"

# 5. Check if model is actually ready
echo
echo "5. Checking model status:"
ollama list

# 6. Try direct ollama command
echo
echo "6. Direct ollama run test:"
echo "Hello" | timeout 5 ollama run llama3 2>&1

# 7. Check environment
echo
echo "7. Environment variables:"
env | grep -i ollama

echo
echo "=== DIAGNOSIS ==="
echo "If nothing shows in logs, either:"
echo "1. Ollama is listening on different port"
echo "2. Firewall/security blocking"
echo "3. Model not actually ready despite loading"
echo "4. Need to use ollama CLI instead of API"