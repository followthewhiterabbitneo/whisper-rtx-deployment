#!/usr/bin/env python3
"""
USE THE EXISTING LLAMA MODEL - NO PULLING!
"""
import subprocess
import os

# Set environment to use /moneyball
os.environ['OLLAMA_MODELS'] = '/moneyball/ollama/models'

print("=== USING EXISTING MODELS - NO PULLING! ===")
print()

# 1. Show what models we ALREADY HAVE
print("1. Models already installed:")
result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
print(result.stdout)

if not result.stdout.strip():
    print("No models shown by 'ollama list'")
    print("\nChecking file system for models...")
    
    # Check common locations
    locations = [
        "/moneyball/ollama/models",
        "/usr/share/ollama/models",
        "/var/lib/ollama/models",
        "~/.ollama/models",
        "/root/.ollama/models"
    ]
    
    for loc in locations:
        expanded = os.path.expanduser(loc)
        if os.path.exists(expanded):
            print(f"\nFound models directory: {expanded}")
            result = subprocess.run(f"ls -la {expanded}", shell=True, capture_output=True, text=True)
            print(result.stdout)

# 2. Parse available models
available_models = []
if result.stdout:
    lines = result.stdout.strip().split('\n')[1:]  # Skip header
    for line in lines:
        if line:
            model_name = line.split()[0]
            available_models.append(model_name)
            print(f"\nFound: {model_name}")

# 3. Find llama3 model
llama_model = None
for model in available_models:
    if 'llama' in model.lower() and '3' in model:
        llama_model = model
        break
    elif 'llama' in model.lower():
        llama_model = model  # Fallback to any llama

if llama_model:
    print(f"\n✅ FOUND EXISTING LLAMA MODEL: {llama_model}")
    print("NO NEED TO PULL ANYTHING!")
    
    # Use it directly
    print(f"\nTesting existing model: {llama_model}")
    result = subprocess.run(
        ["ollama", "run", llama_model, "Say 'Hello' and nothing else"],
        capture_output=True,
        text=True
    )
    print(f"Response: {result.stdout.strip()}")
    
    # Create a simple wrapper
    with open("/moneyball/use_existing_llama.sh", "w") as f:
        f.write(f"""#!/bin/bash
# Use existing Llama model - NO PULLING!
export OLLAMA_MODELS=/moneyball/ollama/models
ollama run {llama_model} "$@"
""")
    subprocess.run(["chmod", "+x", "/moneyball/use_existing_llama.sh"])
    
    print(f"\nCreated wrapper: /moneyball/use_existing_llama.sh")
    print(f"Use: /moneyball/use_existing_llama.sh 'your prompt'")
    
else:
    print("\n⚠️  No Llama model found in 'ollama list'")
    print("But that doesn't mean it's not there!")
    print("The model files might be present but not registered")

print("\n=== DO NOT PULL ANY MODELS! ===")
print("We already have them!")
print("If Ollama can't see them, we need to fix the registry, not download again!"

# 4. Show disk usage
print("\nDisk usage:")
subprocess.run("df -h / /moneyball | grep -v Filesystem", shell=True)

print("\nTo use existing model directly:")
print("  ollama run llama3:8b 'your prompt'")
print("  ollama run llama3 'your prompt'")
print("  ollama run llama 'your prompt'")
print("\nTry different variations until one works!")