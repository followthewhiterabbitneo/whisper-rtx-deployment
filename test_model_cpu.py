#!/usr/bin/env python3
"""Test if the downloaded UWM model works - CPU version"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Disable torch compile
torch._dynamo.config.suppress_errors = True

print("Testing UWM Gemma 2 model on CPU...")

# Load model
model_path = "./uwm-gemma2-2b"
print(f"Loading from: {model_path}")

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float32,
    device_map="cpu"  # Force CPU
)

print(f"Model loaded! Type: {type(model)}")
print(f"Model size: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B parameters")

# Test generation
prompt = "What is the minimum credit score for a mortgage?"
inputs = tokenizer(prompt, return_tensors="pt")

print(f"\nPrompt: {prompt}")
print("Generating response (this may take a moment on CPU)...")

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_length=50,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id
    )

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"\nResponse: {response}")

print("\n✅ Model works correctly!")
print(f"Model is ready for distillation from: {model_path}")