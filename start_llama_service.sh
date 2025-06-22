#!/bin/bash
# Start persistent Llama service

echo "=== STARTING PERSISTENT LLAMA SERVICE ==="
echo "This will keep the model loaded to avoid 101s reload time!"
echo

# 1. Make sure Ollama environment is set
export OLLAMA_MODELS=/moneyball/ollama/models
export OLLAMA_KEEP_ALIVE=24h  # Keep model loaded for 24 hours!

# 2. Start the service
echo "Starting service (initial load will take ~101 seconds)..."
nohup python /moneyball/whisper-rtx-deployment/llama_persistent_service.py > /moneyball/llama_service.log 2>&1 &
SERVICE_PID=$!

echo "Service started with PID: $SERVICE_PID"
echo "Log file: /moneyball/llama_service.log"

# 3. Monitor initial load
echo
echo "Monitoring initial load..."
tail -f /moneyball/llama_service.log &
TAIL_PID=$!

# Wait for model to load
sleep 120

# Kill tail
kill $TAIL_PID 2>/dev/null

# 4. Create convenience script
cat > /moneyball/use_llama.py << 'EOF'
#!/usr/bin/env python3
"""Quick script to use the persistent Llama service"""
import sys
sys.path.append('/moneyball/whisper-rtx-deployment')
from llama_persistent_service import get_service

# Get the service (already loaded!)
service = get_service()

# Example usage
if len(sys.argv) > 1:
    prompt = " ".join(sys.argv[1:])
    result = service.quick_response(prompt)
    print(result['response'])
else:
    print("Usage: python use_llama.py 'your prompt here'")
    print("Or import: from llama_persistent_service import get_service")
EOF

chmod +x /moneyball/use_llama.py

echo
echo "=== SERVICE READY ==="
echo "Model loaded in GPU memory!"
echo
echo "Quick usage:"
echo "  python /moneyball/use_llama.py 'What is 2+2?'"
echo
echo "From Python:"
echo "  from llama_persistent_service import get_service"
echo "  service = get_service()"
echo "  result = service.query('your prompt')"
echo
echo "The model will stay loaded - no more waiting!"