#!/bin/bash
# Run Llama 3 on GPU with persistent server

echo "=== Llama 3 GPU Server Setup ==="

# Kill existing Ollama
pkill -f ollama

# 1. Check GPU availability
echo "1. GPU Status:"
nvidia-smi -L
echo ""

# 2. Set GPU environment
echo "2. Configuring for GPU..."
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOME="/moneyball/ollama/data"
export OLLAMA_MODELS="/moneyball/ollama/models"
# Force GPU layers
export OLLAMA_NUM_GPU=999
export OLLAMA_GPU_LAYERS=999

# 3. Update Modelfile for GPU
echo "3. Creating GPU-optimized Modelfile..."
cat > /moneyball/ollama/Llama3GPU_Modelfile << 'EOF'
FROM /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf

PARAMETER temperature 0.7
PARAMETER num_ctx 4096
PARAMETER num_gpu 999
PARAMETER gpu_layers 999
PARAMETER num_thread 8
PARAMETER main_gpu 0

TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a legal assistant. Be concise.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{{ .Prompt }}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""
EOF

# 4. Start Ollama with GPU debugging
echo ""
echo "4. Starting Ollama with GPU support..."
cd /moneyball/whisper-rtx-deployment

# Start with verbose GPU logging
OLLAMA_DEBUG=1 /moneyball/ollama/bin/ollama serve > /moneyball/ollama/gpu_server.log 2>&1 &
OLLAMA_PID=$!

sleep 10

# 5. Create GPU model
echo ""
echo "5. Creating GPU-enabled model..."
/moneyball/ollama/bin/ollama rm llama3-gpu 2>/dev/null
/moneyball/ollama/bin/ollama create llama3-gpu -f /moneyball/ollama/Llama3GPU_Modelfile

# 6. Load model into memory
echo ""
echo "6. Pre-loading model into GPU memory..."
echo "This will take 30-60 seconds..."

# Warm up the model
/moneyball/ollama/bin/ollama run llama3-gpu "Hello" &
WARMUP_PID=$!

# Monitor GPU while loading
echo ""
echo "Monitoring GPU usage during load:"
for i in {1..6}; do
    sleep 5
    nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
done

wait $WARMUP_PID

# 7. Test performance
echo ""
echo "7. Testing GPU performance..."
echo "Timing a simple query:"
time /moneyball/ollama/bin/ollama run llama3-gpu "Summarize in 5 words: Customer called about loan."

# 8. Keep model loaded - create server wrapper
cat > /moneyball/ollama/llama3_persistent_server.py << 'PYTHON'
#!/usr/bin/env python3
"""
Keep Llama 3 loaded in GPU memory
"""
import subprocess
import time
import threading
import os

os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['OLLAMA_NUM_GPU'] = '999'

class PersistentLlama:
    def __init__(self):
        self.last_query = time.time()
        self.keep_alive_thread = threading.Thread(target=self._keep_alive)
        self.keep_alive_thread.daemon = True
        self.keep_alive_thread.start()
    
    def _keep_alive(self):
        """Keep model in memory by pinging it"""
        while True:
            time.sleep(30)  # Every 30 seconds
            if time.time() - self.last_query > 60:
                # Ping to keep loaded
                subprocess.run([
                    "/moneyball/ollama/bin/ollama", 
                    "run", 
                    "llama3-gpu", 
                    "Hi"
                ], capture_output=True)
                print("Kept model alive in GPU memory")
    
    def query(self, prompt):
        """Query the model"""
        self.last_query = time.time()
        
        result = subprocess.run([
            "/moneyball/ollama/bin/ollama",
            "run",
            "llama3-gpu",
            prompt
        ], capture_output=True, text=True)
        
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

# Create global instance
llama = PersistentLlama()

def legal_summary(text):
    """Create legal summary"""
    prompt = f"Create a legal summary:\n{text[:1500]}"
    return llama.query(prompt)

if __name__ == "__main__":
    print("Llama 3 Persistent Server Started")
    print("Model will stay loaded in GPU memory")
    
    # Test
    print("\nTest summary:")
    result = legal_summary("Eric Rawlins called about loan modification status.")
    print(result)
    
    # Keep running
    print("\nServer running. Model stays in GPU memory.")
    while True:
        time.sleep(60)
PYTHON

chmod +x /moneyball/ollama/llama3_persistent_server.py

# 9. Check GPU usage
echo ""
echo "8. Final GPU check:"
nvidia-smi

echo ""
echo "=== GPU Server Setup Complete ==="
echo "Ollama PID: $OLLAMA_PID"
echo "Log: /moneyball/ollama/gpu_server.log"
echo ""
echo "To check if using GPU:"
echo "tail /moneyball/ollama/gpu_server.log | grep -i gpu"
echo ""
echo "For persistent server:"
echo "python3 /moneyball/ollama/llama3_persistent_server.py"