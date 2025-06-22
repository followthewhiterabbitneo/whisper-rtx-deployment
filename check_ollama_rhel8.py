#!/usr/bin/env python3
"""
Check if Ollama is available and use it for Gemma
Ollama handles GGUF files natively
"""
import os
import sys
import subprocess
from pathlib import Path

def check_ollama():
    """Check if Ollama is installed"""
    print("=== Checking for Ollama ===")
    
    # Check if ollama command exists
    result = subprocess.run(
        ["which", "ollama"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    if result.returncode == 0:
        print(f"✓ Ollama found at: {result.stdout.strip()}")
        
        # Check version
        result = subprocess.run(
            ["ollama", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if result.returncode == 0:
            print(f"Version: {result.stdout.strip()}")
        
        # Check if running
        result = subprocess.run(
            ["ollama", "list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if result.returncode == 0:
            print("\nInstalled models:")
            print(result.stdout)
        else:
            print("\nOllama service might not be running")
            print("Start with: ollama serve")
        
        return True
    else:
        print("✗ Ollama not found")
        return False

def setup_gemma_with_ollama():
    """Set up Gemma model with Ollama"""
    print("\n=== Setting up Gemma with Ollama ===")
    
    model_path = "/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"
    
    if not Path(model_path).exists():
        print(f"ERROR: Model not found at {model_path}")
        return
    
    print("\nTo use your GGUF file with Ollama:")
    print("1. Create a Modelfile:")
    print(f"   echo 'FROM {model_path}' > Modelfile")
    print("\n2. Create the model:")
    print("   ollama create gemma2-local -f Modelfile")
    print("\n3. Test it:")
    print("   ollama run gemma2-local 'Summarize: The quick brown fox jumps over the lazy dog.'")
    
    # Create a simple Python wrapper
    print("\n=== Creating Python wrapper ===")
    
    wrapper_content = f'''#!/usr/bin/env python3
"""Simple Ollama wrapper for Gemma"""
import subprocess
import json

def query_gemma(prompt):
    """Query Gemma using Ollama CLI"""
    cmd = ["ollama", "run", "gemma2-local", prompt]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        return f"Error: {{result.stderr}}"

if __name__ == "__main__":
    # Test
    response = query_gemma("Summarize in one sentence: The quick brown fox jumps over the lazy dog.")
    print(f"Response: {{response}}")
'''
    
    with open("test_ollama_gemma.py", "w") as f:
        f.write(wrapper_content)
    
    print("Created test_ollama_gemma.py")

def suggest_alternatives():
    """Suggest other approaches"""
    print("\n=== Alternative Approaches ===")
    
    print("\n1. Install Ollama (if not available):")
    print("   curl -fsSL https://ollama.ai/install.sh | sh")
    
    print("\n2. Use Python HTTP API approach:")
    print("   Start a simple HTTP server that loads the model")
    
    print("\n3. Convert GGUF to SafeTensors format:")
    print("   Use gguf-to-safetensors converter")
    
    print("\n4. Use the transcription from your Whisper setup:")
    print("   Since you already have the Eric Rawlins transcript,")
    print("   we could create a simple summarizer using the existing")
    print("   transformers library with a smaller model that works")

def main():
    if check_ollama():
        setup_gemma_with_ollama()
    else:
        suggest_alternatives()
    
    print("\n=== Quick Solution ===")
    print("Since Gemma setup is complex on RHEL8 with Python 3.6,")
    print("let's create a simple legal summarizer using your existing")
    print("transformers installation with a model that works!")

if __name__ == "__main__":
    main()