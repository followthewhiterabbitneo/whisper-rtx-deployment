#!/bin/bash
# Setup transformers and torch for RHEL8

echo "=== Installing Transformers and PyTorch ==="

# Make sure we're in the venv
if [[ "$VIRTUAL_ENV" != *"gemma-env"* ]]; then
    echo "ERROR: Please activate gemma-env first:"
    echo "source /moneyball/gemma-env/bin/activate"
    exit 1
fi

echo "Current environment: $VIRTUAL_ENV"
echo "Python version: $(python --version)"

echo ""
echo "Installing packages (this may take a few minutes)..."

# Install PyTorch for CUDA (if available) or CPU
echo "1. Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo ""
echo "2. Installing transformers and dependencies..."
pip install transformers accelerate sentencepiece protobuf

echo ""
echo "3. Verifying installation..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import transformers; print(f'Transformers version: {transformers.__version__}')"

echo ""
echo "Done! Now you can run: python test_gemma2_transformers_rhel8.py"