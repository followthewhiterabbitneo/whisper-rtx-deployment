#!/bin/bash
# Set up Ollama correctly to use /moneyball

echo "=== SETTING UP OLLAMA CORRECTLY ==="
echo "Root filesystem: $(df -h / | tail -1 | awk '{print $5}') used"
echo "Moneyball: $(df -h /moneyball | tail -1 | awk '{print $5}') used"
echo

# 1. Create proper Ollama directories in /moneyball
echo "1. Creating Ollama directories in /moneyball..."
mkdir -p /moneyball/ollama/models
mkdir -p /moneyball/ollama/data
mkdir -p /moneyball/ollama/tmp

# 2. Set environment variables
echo
echo "2. Setting environment variables..."
cat > /moneyball/ollama_env.sh << 'EOF'
# Ollama environment - ALWAYS source this before using Ollama!
export OLLAMA_MODELS=/moneyball/ollama/models
export OLLAMA_DATA_DIR=/moneyball/ollama/data
export OLLAMA_TMPDIR=/moneyball/ollama/tmp
export OLLAMA_HOST=0.0.0.0:11434

echo "Ollama configured to use /moneyball:"
echo "  Models: $OLLAMA_MODELS"
echo "  Data: $OLLAMA_DATA_DIR"
echo "  Temp: $OLLAMA_TMPDIR"
EOF

# 3. Create systemd override (if using systemd)
echo
echo "3. Creating systemd override..."
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf << EOF
[Service]
Environment="OLLAMA_MODELS=/moneyball/ollama/models"
Environment="OLLAMA_DATA_DIR=/moneyball/ollama/data"
Environment="OLLAMA_TMPDIR=/moneyball/ollama/tmp"
EOF

# 4. Create safe ollama wrapper
echo
echo "4. Creating safe ollama wrapper..."
cat > /moneyball/ollama_safe << 'EOF'
#!/bin/bash
# Safe Ollama wrapper - ALWAYS uses /moneyball

# Source environment
source /moneyball/ollama_env.sh

# Check disk space first
ROOT_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $ROOT_USAGE -gt 80 ]; then
    echo "ERROR: Root filesystem is ${ROOT_USAGE}% full!"
    echo "Not starting Ollama for safety."
    exit 1
fi

# Run ollama with proper environment
exec /usr/bin/ollama "$@"
EOF
chmod +x /moneyball/ollama_safe

# 5. Create aliases
echo
echo "5. Adding to your bashrc..."
cat >> ~/.bashrc << 'EOF'

# Ollama safety aliases
alias ollama='/moneyball/ollama_safe'
source /moneyball/ollama_env.sh
EOF

echo
echo "=== SETUP COMPLETE ==="
echo
echo "IMPORTANT: From now on:"
echo "1. ALWAYS use: /moneyball/ollama_safe"
echo "2. Or source first: source /moneyball/ollama_env.sh"
echo "3. Models will go to: /moneyball/ollama/models"
echo
echo "To start Ollama safely:"
echo "  source /moneyball/ollama_env.sh"
echo "  ollama serve &"
echo
echo "Your disk is safe now!"