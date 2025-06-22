#!/bin/bash
# Fixed GPU setup for Llama 3

echo "=== Llama 3 GPU Setup (Fixed) ==="

# 1. Kill existing Ollama
pkill -f ollama
sleep 2

# 2. Check GPU
echo "1. GPU Status:"
nvidia-smi -L

# 3. Start Ollama with GPU environment
echo ""
echo "2. Starting Ollama with GPU settings..."
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOME="/moneyball/ollama/data"
export OLLAMA_MODELS="/moneyball/ollama/models"

cd /moneyball/whisper-rtx-deployment
/moneyball/ollama/bin/ollama serve > /moneyball/ollama/gpu_fixed.log 2>&1 &
OLLAMA_PID=$!

sleep 5

# 4. Check if llama3-legal exists
echo ""
echo "3. Checking existing models..."
/moneyball/ollama/bin/ollama list

# 5. Pre-load the existing model
echo ""
echo "4. Loading llama3-legal into memory..."
echo "Watch GPU memory usage:"

# Start monitoring GPU in background
(
    for i in {1..10}; do
        echo -n "GPU Memory: "
        nvidia-smi --query-gpu=memory.used --format=csv,noheader
        sleep 3
    done
) &
MONITOR_PID=$!

# Load model
echo ""
echo "Loading model (this takes 30-60 seconds)..."
time /moneyball/ollama/bin/ollama run llama3-legal "Hello world" > /tmp/llama_load.txt 2>&1

# Stop monitor
kill $MONITOR_PID 2>/dev/null

# 6. Test performance
echo ""
echo "5. Testing loaded model performance:"
echo "First query (should be fast now):"
time /moneyball/ollama/bin/ollama run llama3-legal "Summarize: Customer called."

echo ""
echo "Second query (should be even faster):"
time /moneyball/ollama/bin/ollama run llama3-legal "Legal summary: Loan application."

# 7. Create keep-alive script
cat > /moneyball/ollama/keep_llama_loaded.sh << 'SCRIPT'
#!/bin/bash
# Keep Llama 3 loaded in memory

echo "Keeping Llama 3 loaded in memory..."
echo "Press Ctrl+C to stop"

while true; do
    # Ping model every 60 seconds
    /moneyball/ollama/bin/ollama run llama3-legal "." > /dev/null 2>&1
    echo "$(date): Pinged model to keep loaded"
    sleep 60
done
SCRIPT
chmod +x /moneyball/ollama/keep_llama_loaded.sh

# 8. Create fast API wrapper
cat > /moneyball/ollama/fast_llama_api.py << 'PYTHON'
#!/usr/bin/env python3
"""
Fast API for pre-loaded Llama 3
"""
import subprocess
import time
import os

class FastLlama:
    def __init__(self):
        print("Initializing Fast Llama API...")
        # Ensure model is loaded
        self.load_model()
        
    def load_model(self):
        """Pre-load model"""
        print("Pre-loading model into memory...")
        start = time.time()
        
        result = subprocess.run([
            "/moneyball/ollama/bin/ollama",
            "run",
            "llama3-legal",
            "Initialize"
        ], capture_output=True, text=True)
        
        elapsed = time.time() - start
        print(f"Model loaded in {elapsed:.1f} seconds")
        
    def query(self, prompt, timeout=30):
        """Fast query to pre-loaded model"""
        start = time.time()
        
        try:
            result = subprocess.run([
                "/moneyball/ollama/bin/ollama",
                "run", 
                "llama3-legal",
                prompt
            ], capture_output=True, text=True, timeout=timeout)
            
            elapsed = time.time() - start
            
            if result.returncode == 0:
                return {
                    "response": result.stdout.strip(),
                    "time": elapsed,
                    "status": "success"
                }
            else:
                return {
                    "response": f"Error: {result.stderr}",
                    "time": elapsed,
                    "status": "error"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "response": "Timeout",
                "time": timeout,
                "status": "timeout"
            }
    
    def legal_summary(self, transcript):
        """Create legal summary"""
        prompt = f"""Create a concise legal summary:
        
{transcript[:1500]}

Legal Summary:"""
        
        return self.query(prompt, timeout=60)

# Test
if __name__ == "__main__":
    llama = FastLlama()
    
    print("\nTest 1 - Simple query:")
    result = llama.query("Hello")
    print(f"Response: {result['response']}")
    print(f"Time: {result['time']:.1f}s")
    
    print("\nTest 2 - Legal summary:")
    result = llama.legal_summary("Eric Rawlins called about loan modification on June 20th.")
    print(f"Summary: {result['response']}")
    print(f"Time: {result['time']:.1f}s")
PYTHON
chmod +x /moneyball/ollama/fast_llama_api.py

# 9. Check final status
echo ""
echo "6. Final GPU check:"
nvidia-smi | grep -E "MiB|ollama"

echo ""
echo "=== Setup Complete ==="
echo "Ollama PID: $OLLAMA_PID"
echo ""
echo "To keep model loaded:"
echo "/moneyball/ollama/keep_llama_loaded.sh &"
echo ""
echo "For fast queries:"
echo "python3 /moneyball/ollama/fast_llama_api.py"
echo ""
echo "Check GPU usage:"
echo "watch -n 1 nvidia-smi"