#!/usr/bin/env python3
"""Test if the downloaded UWM model works"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

print("Testing UWM Gemma 2 model...")

# Load model
model_path = "./uwm-gemma2-2b"
print(f"Loading from: {model_path}")

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)

print(f"Model loaded! Type: {type(model)}")
print(f"Model size: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B parameters")

# Test generation
prompt = "What is the minimum credit score for a mortgage?"
device = next(model.parameters()).device
inputs = tokenizer(prompt, return_tensors="pt").to(device)

print(f"\nPrompt: {prompt}")
print("Generating response...")

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_length=100,
        temperature=0.7,
        do_sample=True
    )

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"\nResponse: {response}")

print("\n✅ Model works correctly!")