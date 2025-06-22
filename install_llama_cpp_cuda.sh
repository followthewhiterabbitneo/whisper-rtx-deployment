#!/bin/bash
# Install llama.cpp with CUDA as alternative to slow Ollama

echo "=== INSTALLING LLAMA.CPP WITH CUDA ==="
echo "Direct GPU inference without Ollama overhead"
echo

cd /moneyball

# 1. Clone llama.cpp
echo "1. Cloning llama.cpp:"
if [ -d "llama.cpp" ]; then
    echo "Already exists, updating..."
    cd llama.cpp
    git pull
else
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp
fi

# 2. Build with CUDA
echo
echo "2. Building with CUDA support:"
make clean
LLAMA_CUDA=1 make -j8

# 3. Test GPU detection
echo
echo "3. Testing GPU detection:"
./main --help | grep -i gpu

# 4. Run inference test
echo
echo "4. Testing direct GPU inference:"
time ./main \
    -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
    -p "What is 2+2?" \
    -n 20 \
    --gpu-layers 999 \
    --threads 8

# 5. Create wrapper script
echo
echo "5. Creating wrapper script:"
cat > /moneyball/llama_gpu.sh << 'EOF'
#!/bin/bash
# Direct GPU inference with llama.cpp
/moneyball/llama.cpp/main \
    -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
    --gpu-layers 999 \
    --threads 8 \
    --ctx-size 4096 \
    --temp 0.7 \
    --top-p 0.9 \
    -p "$*" \
    -n 500
EOF
chmod +x /moneyball/llama_gpu.sh

echo
echo "=== LLAMA.CPP READY ==="
echo "If this is fast, use llama.cpp instead of Ollama!"
echo "Usage: /moneyball/llama_gpu.sh 'your prompt'"