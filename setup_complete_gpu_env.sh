#!/bin/bash
# Complete GPU environment setup - run this first!

echo "=== Complete GPU Environment Setup ==="
echo "This script sets up everything needed for GPU access"
echo

# 1. Set up CUDA environment variables
echo "1. Setting up CUDA environment..."

# Find CUDA
CUDA_LOCATIONS=(
    "/usr/local/cuda"
    "/opt/cuda"
    "/usr/lib/cuda"
)

CUDA_HOME=""
for loc in "${CUDA_LOCATIONS[@]}"; do
    if [ -d "$loc" ]; then
        CUDA_HOME="$loc"
        break
    fi
done

if [ -z "$CUDA_HOME" ]; then
    echo "⚠️  CUDA not found in standard locations"
    echo "Checking for CUDA libraries..."
    if [ -f "/usr/lib64/libcuda.so" ]; then
        echo "Found CUDA libraries in /usr/lib64"
        export LD_LIBRARY_PATH="/usr/lib64:/usr/lib64/nvidia:$LD_LIBRARY_PATH"
    fi
else
    echo "Found CUDA at: $CUDA_HOME"
    export CUDA_HOME="$CUDA_HOME"
    export CUDA_PATH="$CUDA_HOME"
    export PATH="$CUDA_HOME/bin:$PATH"
    export LD_LIBRARY_PATH="$CUDA_HOME/lib64:$LD_LIBRARY_PATH"
fi

# Always set CUDA_VISIBLE_DEVICES
export CUDA_VISIBLE_DEVICES="0"

# 2. Find and activate Python environment
echo
echo "2. Finding Python virtual environment..."

VENVS=(
    "/moneyball/llama-env-py39"
    "/moneyball/gemma-env"
    "/moneyball/llama-env-py38"
)

ACTIVATED=false
for venv in "${VENVS[@]}"; do
    if [ -d "$venv" ] && [ -f "$venv/bin/activate" ]; then
        echo "Found: $venv"
        
        # Get Python version
        if [ -f "$venv/bin/python" ]; then
            PY_VERSION=$($venv/bin/python --version 2>&1)
            echo "  Python: $PY_VERSION"
            
            # Prefer Python 3.9
            if [[ "$PY_VERSION" == *"3.9"* ]] || [ "$ACTIVATED" == false ]; then
                echo "  ✓ Activating this environment"
                source "$venv/bin/activate"
                ACTIVATED=true
                SELECTED_VENV="$venv"
                
                # Export for subshells
                export VIRTUAL_ENV="$venv"
                export PATH="$venv/bin:$PATH"
                
                # Show activation
                echo "  Activated: $VIRTUAL_ENV"
                echo "  Python: $(which python)"
                echo "  Pip: $(which pip)"
                
                if [[ "$PY_VERSION" == *"3.9"* ]]; then
                    break  # Stop if we found Python 3.9
                fi
            fi
        fi
    fi
done

if [ "$ACTIVATED" == false ]; then
    echo "❌ No virtual environment found!"
    exit 1
fi

# 3. Show current environment
echo
echo "3. Current environment:"
echo "  CUDA_HOME: ${CUDA_HOME:-not set}"
echo "  CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
echo "  Virtual env: $VIRTUAL_ENV"
echo "  Python: $(python --version)"
echo "  Working directory: $(pwd)"

# 4. Create activation script for future use
echo
echo "4. Creating persistent activation script..."

cat > /moneyball/activate_gpu_env.sh << EOF
#!/bin/bash
# GPU Environment Activation Script
# Generated on $(date)

# CUDA environment
export CUDA_HOME="${CUDA_HOME}"
export CUDA_PATH="${CUDA_HOME}"
export PATH="${CUDA_HOME}/bin:\$PATH"
export LD_LIBRARY_PATH="${CUDA_HOME}/lib64:/usr/lib64:/usr/lib64/nvidia:\$LD_LIBRARY_PATH"
export CUDA_VISIBLE_DEVICES="0"

# Python environment
source "$SELECTED_VENV/bin/activate"

echo "GPU environment activated:"
echo "  CUDA_HOME: \$CUDA_HOME"
echo "  CUDA_VISIBLE_DEVICES: \$CUDA_VISIBLE_DEVICES"
echo "  Python: \$(which python)"
echo "  Virtual env: \$VIRTUAL_ENV"

# Quick GPU test
echo
echo "Quick GPU check:"
nvidia-smi -L 2>/dev/null || echo "nvidia-smi not accessible"
python -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}')" 2>/dev/null || echo "PyTorch not installed or CUDA not available"
EOF

chmod +x /moneyball/activate_gpu_env.sh

# 5. Test current setup
echo
echo "5. Testing current setup:"

# Check nvidia-smi
echo "  nvidia-smi:"
nvidia-smi -L 2>/dev/null || echo "  nvidia-smi not accessible"

# Check PyTorch
echo
echo "  PyTorch:"
python -c "import torch; print(f'  Version: {torch.__version__}'); print(f'  CUDA: {torch.cuda.is_available()}')" 2>/dev/null || echo "  PyTorch not installed"

# 6. Create test script
cat > /moneyball/test_gpu_env.py << 'EOF'
#!/usr/bin/env python
import os
import sys

print("=== GPU Environment Test ===")
print(f"Python: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Virtual env: {os.environ.get('VIRTUAL_ENV', 'not set')}")
print()

print("CUDA Environment:")
for var in ['CUDA_HOME', 'CUDA_PATH', 'CUDA_VISIBLE_DEVICES', 'LD_LIBRARY_PATH']:
    value = os.environ.get(var, 'not set')
    if var == 'LD_LIBRARY_PATH' and len(value) > 100:
        value = value[:100] + "..."
    print(f"  {var}: {value}")
print()

try:
    import torch
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if hasattr(torch.version, 'cuda'):
        print(f"PyTorch built with CUDA: {torch.version.cuda}")
except ImportError:
    print("PyTorch not installed")
EOF

chmod +x /moneyball/test_gpu_env.py

# 7. Final instructions
echo
echo "=== SETUP COMPLETE ==="
echo
echo "Environment is now configured!"
echo
echo "Your environment:"
echo "  Virtual env: $VIRTUAL_ENV"
echo "  Python: $(which python)"
echo "  CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
echo
echo "Next steps:"
echo "1. To install PyTorch with GPU:"
echo "   ./install_pytorch_gpu.sh"
echo
echo "2. To reactivate this environment later:"
echo "   source /moneyball/activate_gpu_env.sh"
echo
echo "3. To test GPU environment:"
echo "   python /moneyball/test_gpu_env.py"
echo
echo "NOTE: You're now in the activated environment!"
echo "The prompt should show (llama-env-py39) or similar"