#!/bin/bash
# Aggressive cleanup of /moneyball - remove Gemma and unnecessary files

echo "=== AGGRESSIVE CLEANUP OF /moneyball ==="
echo "This will DELETE Gemma models and tar files!"
echo
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo
echo "Before cleanup:"
df -h /moneyball
echo

# 1. Remove Gemma directories
echo "1. Removing Gemma directories..."
rm -rf /moneyball/gemma*
rm -rf /moneyball/*gemma*
rm -rf /moneyball/*/gemma*

# 2. Remove Gemma files
echo "2. Removing Gemma files..."
find /moneyball -name "*gemma*" -type f -delete

# 3. Remove tar/gz files
echo "3. Removing tar archives..."
find /moneyball -name "*.tar.gz" -type f -delete
find /moneyball -name "*.tar" -type f -delete
find /moneyball -name "*.tgz" -type f -delete

# 4. Remove GGUF files (old models)
echo "4. Removing old GGUF models..."
find /moneyball -name "*.gguf" -type f -delete

# 5. Remove Ollama models directory if it exists
echo "5. Cleaning Ollama models..."
if [ -d "/moneyball/ollama/models" ]; then
    echo "Found Ollama models directory"
    du -sh /moneyball/ollama/models
    rm -rf /moneyball/ollama/models/*
fi

# 6. Remove old Python environments
echo "6. Removing old Python environments..."
rm -rf /moneyball/gemma-env
rm -rf /moneyball/llama-env  # Keep llama-env-py39

# 7. Clean pip cache
echo "7. Cleaning pip cache..."
rm -rf /moneyball/.cache/pip

# 8. Remove old downloads
echo "8. Removing old downloads..."
rm -rf /moneyball/downloads
rm -rf /moneyball/Download*

# 9. Final check
echo
echo "After cleanup:"
df -h /moneyball
echo
echo "Space freed:"
echo "Check root filesystem too:"
df -h /

echo
echo "✓ Cleanup complete!"
echo "✓ Kept: llama-env-py39 and essential files"
echo "✓ Removed: All Gemma files, tarballs, old models"