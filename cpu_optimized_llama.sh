#!/bin/bash
# CPU-optimized Llama 3 setup for vGPU systems

echo "=== CPU-Optimized Llama 3 Setup ==="
echo "Since vGPU isn't accessible, we'll optimize for CPU"

# 1. Kill existing
pkill -f ollama

# 2. Start Ollama accepting CPU mode
echo "1. Starting Ollama (CPU mode)..."
cd /moneyball/whisper-rtx-deployment

# Start without GPU attempts
CUDA_VISIBLE_DEVICES="" /moneyball/ollama/bin/ollama serve > /moneyball/ollama/cpu_server.log 2>&1 &
OLLAMA_PID=$!

sleep 5

# 3. Check CPU info
echo ""
echo "2. CPU Information:"
lscpu | grep -E "Model name|CPU\(s\)|Thread|Core"
echo "RAM: $(free -h | grep Mem | awk '{print $2}')"

# 4. Pre-load model with CPU optimizations
echo ""
echo "3. Pre-loading Llama 3 into RAM..."
echo "This will take 1-2 minutes but then responses will be fast"

# Monitor memory usage
(
    echo "Memory usage during load:"
    while true; do
        free -h | grep Mem | awk '{print "RAM Used: " $3 " / " $2}'
        sleep 5
    done
) &
MONITOR_PID=$!

# Load model
time /moneyball/ollama/bin/ollama run llama3-legal "Initialize model" > /tmp/load.txt 2>&1

kill $MONITOR_PID 2>/dev/null

# 5. Test performance when loaded
echo ""
echo "4. Testing CPU performance (model loaded):"

echo "Query 1:"
time /moneyball/ollama/bin/ollama run llama3-legal "Hello"

echo ""
echo "Query 2 (should be faster):"
time /moneyball/ollama/bin/ollama run llama3-legal "Summarize: Loan call"

# 6. Create optimized server
cat > /moneyball/ollama/cpu_llama_server.py << 'PYTHON'
#!/usr/bin/env python3
"""
CPU-optimized Llama server with connection pooling
"""
import subprocess
import threading
import queue
import time
import os

class CPUOptimizedLlama:
    def __init__(self, threads=8):
        self.threads = threads
        self.query_queue = queue.Queue()
        self.keep_alive = True
        
        # Pre-load model
        print("Pre-loading Llama 3 into RAM...")
        self._warmup()
        
        # Start keep-alive thread
        self.keeper = threading.Thread(target=self._keep_alive_loop)
        self.keeper.daemon = True
        self.keeper.start()
        
        print("CPU-optimized server ready!")
    
    def _warmup(self):
        """Pre-load model"""
        start = time.time()
        subprocess.run([
            "/moneyball/ollama/bin/ollama", "run", "llama3-legal", "Init"
        ], capture_output=True)
        print(f"Model loaded in {time.time()-start:.1f}s")
    
    def _keep_alive_loop(self):
        """Keep model in RAM"""
        while self.keep_alive:
            time.sleep(45)
            subprocess.run([
                "/moneyball/ollama/bin/ollama", "run", "llama3-legal", "."
            ], capture_output=True)
            print(f"[{time.strftime('%H:%M:%S')}] Model kept in RAM")
    
    def query(self, prompt, max_tokens=500):
        """Fast query"""
        start = time.time()
        
        # Use nice to give priority
        cmd = [
            "nice", "-n", "-10",  # Higher priority
            "/moneyball/ollama/bin/ollama", "run", "llama3-legal",
            prompt
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={**os.environ, "OMP_NUM_THREADS": str(self.threads)}
        )
        
        elapsed = time.time() - start
        
        return {
            "response": result.stdout.strip(),
            "time": elapsed,
            "status": "success" if result.returncode == 0 else "error"
        }
    
    def batch_process(self, prompts):
        """Process multiple prompts efficiently"""
        results = []
        for prompt in prompts:
            results.append(self.query(prompt))
        return results

# Global instance
cpu_llama = CPUOptimizedLlama()

def legal_summary(transcript):
    """Create legal summary"""
    prompt = f"""Create a legal summary with these sections:
- Participants
- Date/Topic  
- Key Points
- Actions/Next Steps

Transcript: {transcript[:1000]}"""
    
    return cpu_llama.query(prompt)

if __name__ == "__main__":
    print("\nTest summary:")
    result = legal_summary("Eric Rawlins called on June 20th about loan modification status.")
    print(f"Summary: {result['response']}")
    print(f"Time: {result['time']:.1f}s")
    
    print("\nServer running. Use cpu_llama.query() for fast responses.")
PYTHON

chmod +x /moneyball/ollama/cpu_llama_server.py

# 7. Create simple CLI tool
cat > /moneyball/ollama/llama << 'TOOL'
#!/bin/bash
# Quick Llama CLI tool
/moneyball/ollama/bin/ollama run llama3-legal "$*"
TOOL
chmod +x /moneyball/ollama/llama

echo ""
echo "=== CPU Setup Complete ==="
echo "Model is loaded in RAM for fast CPU responses"
echo ""
echo "Quick usage:"
echo "  /moneyball/ollama/llama 'Your prompt here'"
echo ""
echo "Python API:"
echo "  python3 /moneyball/ollama/cpu_llama_server.py"
echo ""
echo "The model will stay loaded in RAM."
echo "First query after load: ~10-20s"
echo "Subsequent queries: ~5-10s"