#!/usr/bin/env python3
"""
Test Gemma 2 using transformers library instead of llama-cpp-python
This avoids GGUF format issues
"""
import os
import sys
import torch
from pathlib import Path

def test_transformers_gemma():
    """Test using transformers library"""
    print("=== Testing Gemma 2 with Transformers ===")
    
    # Check for transformers
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        print("✓ transformers library available")
    except ImportError:
        print("ERROR: transformers not installed")
        print("Install with: pip install transformers torch")
        return
    
    # Check torch and GPU
    print(f"\nPyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    
    # For now, let's use a smaller model that works on CPU
    # We can switch to Gemma 2 9B once we confirm this approach works
    model_name = "google/gemma-2b-it"  # Start with 2B for testing
    
    print(f"\nLoading model: {model_name}")
    print("This may take a few minutes on first run...")
    
    try:
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        print("✓ Model loaded successfully!")
        
        # Test generation
        test_prompt = "Summarize in one sentence: The quick brown fox jumps over the lazy dog."
        
        print(f"\nTest prompt: {test_prompt}")
        
        # Tokenize
        inputs = tokenizer(test_prompt, return_tensors="pt")
        
        # Generate
        print("Generating response...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True
            )
        
        # Decode
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the prompt from response
        response = response.replace(test_prompt, "").strip()
        
        print(f"\nResponse: {response}")
        print("\n✓ Test successful!")
        
        # Cleanup
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # If it's a login error, provide instructions
        if "login" in str(e).lower() or "token" in str(e).lower():
            print("\nNOTE: Some models require Hugging Face login.")
            print("To login: huggingface-cli login")
            print("Or set: export HF_TOKEN=your_token_here")

def main():
    print("=== Gemma 2 Transformers Test ===")
    print(f"Python: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    test_transformers_gemma()
    
    print("\n=== Next Steps ===")
    print("If this works, we can:")
    print("1. Use the full Gemma 2 9B model")
    print("2. Create a legal summary script")
    print("3. Process the Eric Rawlins transcript")

if __name__ == "__main__":
    main()