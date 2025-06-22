#!/bin/bash
# Reinstall llama-cpp-python cleanly on RHEL8

echo "=== Reinstalling llama-cpp-python ==="

# Make sure we're in the venv
if [[ "$VIRTUAL_ENV" != *"gemma-env"* ]]; then
    echo "ERROR: Please activate gemma-env first:"
    echo "source /moneyball/gemma-env/bin/activate"
    exit 1
fi

echo "1. Uninstalling old packages..."
pip uninstall -y magic modular mojo llama-cpp-python 2>/dev/null

echo "2. Cleaning directories..."
rm -rf ~/.modular ~/.magic 2>/dev/null

echo "3. Clearing pip cache..."
pip cache purge

echo "4. Installing llama-cpp-python (CPU version for compatibility)..."
pip install llama-cpp-python==0.2.11 --force-reinstall --no-cache-dir

echo "5. Verifying installation..."
python -c "import llama_cpp; print(f'llama-cpp-python version: {llama_cpp.__version__ if hasattr(llama_cpp, \"__version__\") else \"Unknown\"}')"

echo "6. Checking model file..."
if [ -f "/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf" ]; then
    file /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf
    ls -lh /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf
else
    echo "Model file not found!"
fi

echo ""
echo "Done! Now try running: python test_gemma2_simple_rhel8.py"