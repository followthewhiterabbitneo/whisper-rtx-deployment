#!/bin/bash
# Wrapper to FORCE Ollama to use /moneyball only

# Override HOME to prevent any ~/.ollama creation
export REAL_HOME="$HOME"
export HOME="/moneyball/ollama/home"
export OLLAMA_HOME="/moneyball/ollama/data"
export OLLAMA_MODELS="/moneyball/ollama/models"

# Create fake home
mkdir -p /moneyball/ollama/home/.ollama

# Move any existing keys
if [ -d "$REAL_HOME/.ollama" ]; then
    echo "Moving existing .ollama to /moneyball..."
    mv "$REAL_HOME/.ollama"/* /moneyball/ollama/home/.ollama/ 2>/dev/null
    rm -rf "$REAL_HOME/.ollama"
fi

# Run Ollama with forced paths
/moneyball/ollama/bin/ollama "$@"

# Restore real HOME after
export HOME="$REAL_HOME"