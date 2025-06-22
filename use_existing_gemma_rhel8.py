#!/usr/bin/env python3
"""
Use the existing Gemma GGUF file with ctransformers
This is a simpler alternative to llama-cpp-python
"""
import os
import sys
from pathlib import Path

def test_with_ctransformers():
    """Try using ctransformers library which handles GGUF files well"""
    print("=== Testing Gemma with ctransformers ===")
    
    try:
        from ctransformers import AutoModelForCausalLM
        print("✓ ctransformers available")
    except ImportError:
        print("Installing ctransformers...")
        os.system("pip install ctransformers")
        try:
            from ctransformers import AutoModelForCausalLM
            print("✓ ctransformers installed")
        except:
            print("ERROR: Could not install ctransformers")
            return False
    
    model_path = "/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"
    
    print(f"\nLoading model: {model_path}")
    print("This may take a moment...")
    
    try:
        # Load model with ctransformers
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            model_type="gemma",
            gpu_layers=0,  # Start with CPU only
            context_length=2048
        )
        print("✓ Model loaded successfully!")
        
        # Test generation
        prompt = "Summarize in one sentence: The quick brown fox jumps over the lazy dog."
        print(f"\nTest prompt: {prompt}")
        print("Generating...")
        
        response = model(prompt, max_new_tokens=50)
        print(f"\nResponse: {response}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_with_llama_python():
    """One more try with specific llama-python version"""
    print("\n=== Alternative: Testing with specific llama-cpp-python version ===")
    
    print("Installing llama-cpp-python 0.1.78 (known stable version)...")
    os.system("pip uninstall -y llama-cpp-python")
    os.system("pip install llama-cpp-python==0.1.78")
    
    try:
        from llama_cpp import Llama
        
        model_path = "/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"
        print(f"\nLoading model: {model_path}")
        
        model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4
        )
        print("✓ Model loaded!")
        
        prompt = "Summarize: The quick brown fox jumps over the lazy dog."
        output = model(prompt, max_tokens=50)
        
        if output and 'choices' in output:
            print(f"\nResponse: {output['choices'][0]['text']}")
            return True
            
    except Exception as e:
        print(f"ERROR: {e}")
        
    return False

def main():
    print("=== Using Existing Gemma GGUF File ===")
    print(f"Python: {sys.version}")
    
    # Try ctransformers first
    if test_with_ctransformers():
        print("\n✓ Success with ctransformers!")
        print("\nNext: Create legal summary script")
        return
    
    # If that fails, try specific llama-cpp-python version
    if test_with_llama_python():
        print("\n✓ Success with llama-cpp-python!")
        print("\nNext: Create legal summary script")
        return
    
    print("\n=== Alternative Options ===")
    print("1. Use Ollama (if available on system)")
    print("2. Convert GGUF to HuggingFace format")
    print("3. Use a different model format")
    print("4. Run on a different system with newer Python")

if __name__ == "__main__":
    main()