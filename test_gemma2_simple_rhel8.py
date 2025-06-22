#!/usr/bin/env python3
"""
Simple test script for Gemma 2 9B on RHEL8 - compatible with older llama-cpp-python
"""
import os
import sys
from pathlib import Path

# Try to import and test llama-cpp-python
try:
    from llama_cpp import Llama
    print("✓ llama-cpp-python imported successfully")
except ImportError as e:
    print(f"ERROR: Could not import llama-cpp-python: {e}")
    print("Install with: pip install llama-cpp-python")
    sys.exit(1)

def test_gemma2():
    """Test Gemma 2 9B model with basic parameters"""
    print("=== Testing Gemma 2 9B (Simple) ===")
    
    # Model path
    model_path = Path("/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf")
    if not model_path.exists():
        print(f"ERROR: Model not found at {model_path}")
        return
    
    print(f"Loading model: {model_path}")
    
    try:
        # Try with minimal parameters that should work with older versions
        model = Llama(
            model_path=str(model_path),
            n_ctx=2048,  # Context length
            verbose=False
        )
        print("✓ Model loaded successfully!")
        
    except Exception as e:
        print(f"ERROR loading model: {e}")
        print("\nTrying with even simpler parameters...")
        try:
            # Absolute minimum parameters
            model = Llama(str(model_path))
            print("✓ Model loaded with minimal parameters!")
        except Exception as e2:
            print(f"ERROR: Could not load model at all: {e2}")
            print("\nDebug info:")
            print(f"Python version: {sys.version}")
            print(f"Working directory: {os.getcwd()}")
            
            # Try to check llama-cpp-python version
            try:
                import llama_cpp
                if hasattr(llama_cpp, '__version__'):
                    print(f"llama-cpp-python version: {llama_cpp.__version__}")
                else:
                    print("llama-cpp-python version: Unknown (old version)")
            except:
                pass
            return
    
    # Test the model
    print("\n=== Testing Model ===")
    test_prompt = "Summarize this in one sentence: The quick brown fox jumps over the lazy dog."
    
    try:
        print(f"Prompt: {test_prompt}")
        print("Generating response...")
        
        # Generate response
        response = model(
            test_prompt,
            max_tokens=50,
            temperature=0.7,
            echo=False
        )
        
        if response and 'choices' in response and len(response['choices']) > 0:
            text = response['choices'][0]['text']
            print(f"\nResponse: {text.strip()}")
            print("\n✓ Model test successful!")
        else:
            print("ERROR: No response generated")
            
    except Exception as e:
        print(f"ERROR during generation: {e}")
        print(f"Error type: {type(e).__name__}")
    
    # Memory cleanup
    try:
        del model
        print("\n✓ Model unloaded")
    except:
        pass

def check_environment():
    """Check the environment setup"""
    print("=== Environment Check ===")
    print(f"Python: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    # Check for GPU
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "-L"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if result.returncode == 0:
            print(f"GPU: {result.stdout.strip()}")
        else:
            print("GPU: Not detected")
    except:
        print("GPU: nvidia-smi not available")
    
    print()

if __name__ == "__main__":
    check_environment()
    test_gemma2()