#!/usr/bin/env python3
"""
Alternative: Try Gemma 2 9B which should work with current llama-cpp-python CUDA
"""

print("Alternative models that work with current CUDA llama-cpp-python:")
print("="*60)
print()
print("1. Gemma 2 9B (excellent quality, GPU compatible)")
print("   - Download: https://huggingface.co/bartowski/gemma-2-9b-it-GGUF")
print("   - Use: gemma-2-9b-it-Q4_K_M.gguf")
print()
print("2. Llama 3.1 8B (good for summaries)")
print("   - Download: https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF")
print("   - Use: Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")
print()
print("3. Mistral 7B (fast and efficient)")
print("   - Download: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
print("   - Use: mistral-7b-instruct-v0.2.Q4_K_M.gguf")
print()
print("These models use 'llama' architecture which IS supported by your CUDA version.")
print()
print("To use Gemma 3 with GPU, we need to wait for llama-cpp-python to update.")
print("The CPU version works great though - just takes ~2 minutes per summary.")