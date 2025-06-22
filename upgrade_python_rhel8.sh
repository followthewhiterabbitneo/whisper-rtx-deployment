#!/bin/bash
# Upgrade Python on RHEL8

echo "=== Python Upgrade Options on RHEL8 ==="

# 1. Check current Python
echo "1. Current Python:"
python3 --version
which python3

# 2. Check available Python versions
echo ""
echo "2. Available Python versions in system:"
ls -la /usr/bin/python* | grep -v ".gz"
ls -la /opt/rh/*/root/usr/bin/python* 2>/dev/null | grep -v ".gz"

# 3. Check if newer Python already installed
echo ""
echo "3. Checking for Python 3.8/3.9:"
if [ -f "/usr/bin/python3.8" ]; then
    echo "✓ Python 3.8 found!"
    /usr/bin/python3.8 --version
fi

if [ -f "/usr/bin/python3.9" ]; then
    echo "✓ Python 3.9 found!"
    /usr/bin/python3.9 --version
fi

# 4. Check Software Collections
echo ""
echo "4. Checking Red Hat Software Collections:"
scl -l 2>/dev/null | grep python

# 5. Create new venv with better Python
echo ""
echo "5. Options to use newer Python:"

# Option A: Use system Python 3.8/3.9 if available
if [ -f "/usr/bin/python3.8" ]; then
    echo ""
    echo "Option A: Create new venv with Python 3.8:"
    echo "python3.8 -m venv /moneyball/llama-env-py38"
    echo "source /moneyball/llama-env-py38/bin/activate"
elif [ -f "/usr/bin/python3.9" ]; then
    echo ""
    echo "Option A: Create new venv with Python 3.9:"
    echo "python3.9 -m venv /moneyball/llama-env-py39"
    echo "source /moneyball/llama-env-py39/bin/activate"
fi

# Option B: Use Software Collections
echo ""
echo "Option B: Use Red Hat Software Collections (if available):"
echo "scl enable rh-python38 bash"
echo "python3 -m venv /moneyball/llama-env-scl"

# Option C: Install from source
echo ""
echo "Option C: Build Python from source (takes 15-30 mins):"
echo "cd /moneyball"
echo "wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz"
echo "tar -xzf Python-3.9.18.tgz"
echo "cd Python-3.9.18"
echo "./configure --prefix=/moneyball/python39 --enable-optimizations"
echo "make -j8"
echo "make install"
echo "/moneyball/python39/bin/python3.9 -m venv /moneyball/llama-env-py39"

# 6. Quick setup script
cat > /moneyball/setup_new_python_env.sh << 'SETUP'
#!/bin/bash
# Quick setup with newer Python

echo "Setting up new Python environment..."

# Find best Python
if [ -f "/usr/bin/python3.9" ]; then
    PYTHON="/usr/bin/python3.9"
    VENV_NAME="llama-env-py39"
elif [ -f "/usr/bin/python3.8" ]; then
    PYTHON="/usr/bin/python3.8"
    VENV_NAME="llama-env-py38"
else
    echo "No Python 3.8+ found. Using default."
    PYTHON="python3"
    VENV_NAME="llama-env-new"
fi

echo "Using Python: $PYTHON"
$PYTHON --version

# Create new venv
echo "Creating virtual environment..."
$PYTHON -m venv /moneyball/$VENV_NAME

# Activate and install
source /moneyball/$VENV_NAME/bin/activate
python --version

# Install packages
pip install --upgrade pip
pip install ollama transformers torch numpy

echo ""
echo "New environment ready!"
echo "Activate with: source /moneyball/$VENV_NAME/bin/activate"
SETUP

chmod +x /moneyball/setup_new_python_env.sh

echo ""
echo "=== RECOMMENDATION ==="
echo "Python 3.6 is causing all these issues!"
echo ""
echo "Quick fix:"
echo "1. Check if you have Python 3.8+: ls -la /usr/bin/python3.*"
echo "2. If yes, run: /moneyball/setup_new_python_env.sh"
echo "3. This will create a new venv with modern Python"
echo ""
echo "Then Ollama and all scripts will work properly!"