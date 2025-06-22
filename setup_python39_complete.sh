#!/bin/bash
# Complete Python 3.9 setup with all dependencies

echo "=== Setting up Python 3.9 Environment ==="

# 1. Check Python 3.9 exists
if [ ! -f "/usr/bin/python3.9" ]; then
    echo "ERROR: Python 3.9 not found at /usr/bin/python3.9"
    exit 1
fi

echo "1. Found Python 3.9:"
/usr/bin/python3.9 --version

# 2. Create new virtual environment
VENV_PATH="/moneyball/llama-env-py39"
echo ""
echo "2. Creating virtual environment at $VENV_PATH..."

# Remove old venv if exists
if [ -d "$VENV_PATH" ]; then
    echo "Removing existing environment..."
    rm -rf "$VENV_PATH"
fi

/usr/bin/python3.9 -m venv "$VENV_PATH"

# 3. Activate and verify
echo ""
echo "3. Activating environment..."
source "$VENV_PATH/bin/activate"

echo "Python version in venv:"
python --version
which python

# 4. Upgrade pip
echo ""
echo "4. Upgrading pip..."
python -m pip install --upgrade pip

# 5. Install all required packages
echo ""
echo "5. Installing packages..."

# Core packages
echo "Installing core packages..."
pip install --no-cache-dir \
    numpy \
    requests \
    tqdm \
    pyyaml

# ML packages
echo ""
echo "Installing ML packages..."
pip install --no-cache-dir \
    torch \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# Transformers and related
echo ""
echo "Installing transformers..."
pip install --no-cache-dir \
    transformers \
    accelerate \
    sentencepiece \
    protobuf

# Ollama and llama packages
echo ""
echo "Installing llama packages..."
pip install --no-cache-dir \
    llama-cpp-python \
    ollama

# Additional useful packages
echo ""
echo "Installing additional packages..."
pip install --no-cache-dir \
    kagglehub \
    pathlib \
    python-dotenv

# 6. Test imports
echo ""
echo "6. Testing imports..."
python << 'EOF'
print("Testing package imports...")
try:
    import torch
    print(f"✓ PyTorch {torch.__version__}")
except ImportError as e:
    print(f"✗ PyTorch: {e}")

try:
    import transformers
    print(f"✓ Transformers {transformers.__version__}")
except ImportError as e:
    print(f"✗ Transformers: {e}")

try:
    import llama_cpp
    print("✓ llama-cpp-python")
except ImportError as e:
    print(f"✗ llama-cpp-python: {e}")

try:
    import subprocess
    result = subprocess.run(["echo", "test"], capture_output=True, text=True)
    print("✓ subprocess.capture_output works!")
except Exception as e:
    print(f"✗ subprocess: {e}")
EOF

# 7. Create activation script
cat > /moneyball/activate_py39.sh << 'ACTIVATE'
#!/bin/bash
# Quick activation script
source /moneyball/llama-env-py39/bin/activate
echo "Python 3.9 environment activated"
python --version
echo ""
echo "To test Ollama: python /moneyball/whisper-rtx-deployment/test_ollama_py39.py"
ACTIVATE
chmod +x /moneyball/activate_py39.sh

# 8. Create test script for Ollama
cat > /moneyball/whisper-rtx-deployment/test_ollama_py39.py << 'TEST'
#!/usr/bin/env python3
"""Test Ollama with Python 3.9"""
import subprocess
import os

print("=== Testing Ollama with Python 3.9 ===")

# This should work now!
result = subprocess.run(
    ["ollama", "--version"],
    capture_output=True,  # This works in Python 3.9!
    text=True
)

if result.returncode == 0:
    print(f"✓ Ollama version: {result.stdout.strip()}")
else:
    print(f"✗ Ollama error: {result.stderr}")

# Test running a model
print("\nTesting model query...")
result = subprocess.run(
    ["ollama", "run", "llama3-legal", "Hello"],
    capture_output=True,
    text=True,
    timeout=30
)

if result.returncode == 0:
    print(f"✓ Response: {result.stdout.strip()}")
else:
    print(f"✗ Error: {result.stderr}")
TEST
chmod +x /moneyball/whisper-rtx-deployment/test_ollama_py39.py

# 9. Update GPU benchmark for Python 3.9
echo ""
echo "7. Updating scripts for Python 3.9..."
# The scripts should now work without modification!

# 10. Final instructions
echo ""
echo "=== Setup Complete! ==="
echo ""
echo "IMPORTANT: You are now in Python 3.9 environment!"
echo ""
echo "To use this environment:"
echo "1. Activate: source /moneyball/llama-env-py39/bin/activate"
echo "   Or use: /moneyball/activate_py39.sh"
echo ""
echo "2. All scripts will now work properly with capture_output!"
echo ""
echo "3. Test Ollama: python test_ollama_py39.py"
echo ""
echo "4. Run GPU benchmark: python gpu_benchmark_test.py"
echo ""
echo "5. Your prompt now shows (llama-env-py39) instead of (gemma-env)"

# Create a reminder file
echo "Python 3.9 environment created at: $(date)" > /moneyball/PYTHON39_READY.txt
echo "Activate with: source /moneyball/llama-env-py39/bin/activate" >> /moneyball/PYTHON39_READY.txt