#!/usr/bin/env python3
from llama_cpp import Llama
import sys

# Path to your GGUF model
model_path = "/mnt/c/Users/ecsti/Downloads/googlegemma-3-1b-it-qat-q4_0-gguf/gemma-3-1b-it-q4_0.gguf"

print(f"Loading Gemma 3.1B GGUF model from: {model_path}")
print("This may take a moment...")

try:
    # Initialize the model with CPU settings
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,  # Context window
        n_threads=8,  # Number of CPU threads to use
        n_gpu_layers=0,  # Force CPU usage (0 layers on GPU)
        verbose=False
    )
    
    print("Model loaded successfully!")
    
    # Test with a simple prompt
    prompt = "Hello! Can you explain what Python is in one sentence?"
    
    print(f"\nPrompt: {prompt}")
    print("Generating response...")
    
    # Generate response
    output = llm(
        prompt,
        max_tokens=100,
        temperature=0.7,
        top_p=0.95,
        echo=False
    )
    
    response = output['choices'][0]['text']
    print(f"\nResponse: {response.strip()}")
    
    # Print some stats
    print(f"\nTokens used: {output['usage']['total_tokens']}")
    print(f"Generation time: {output['usage']['completion_tokens']/output['usage']['total_tokens']:.2f} seconds per token (approx)")
    
except FileNotFoundError:
    print(f"\nError: Model file not found at {model_path}")
    print("Please check the path and make sure the file exists.")
    sys.exit(1)
except Exception as e:
    print(f"\nError loading or running model: {type(e).__name__}: {str(e)}")
    sys.exit(1)

print("\nGemma GGUF model is working properly on CPU!")