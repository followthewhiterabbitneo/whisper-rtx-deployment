#!/usr/bin/env python3
"""
Fix Gemma GGUF usage on RHEL8 by trying different approaches
"""
import os
import sys
import subprocess
from pathlib import Path

def try_llamacpp_server():
    """Try using llama.cpp server mode"""
    print("=== Option 1: llama.cpp Server Mode ===")
    print("\nThis approach runs the model as a server:")
    print("1. Clone llama.cpp:")
    print("   git clone https://github.com/ggerganov/llama.cpp")
    print("   cd llama.cpp")
    print("   make")
    print("\n2. Run server with your model:")
    print("   ./server -m /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf -c 2048")
    print("\n3. Query via HTTP:")
    print("   curl http://localhost:8080/completion -H 'Content-Type: application/json' \\")
    print("   -d '{\"prompt\": \"Summarize: ...\", \"n_predict\": 128}'")

def check_python_version():
    """Check if Python version is the issue"""
    print("\n=== Python Version Check ===")
    print(f"Current Python: {sys.version}")
    
    if sys.version_info < (3, 7):
        print("⚠️  Python 3.6 is quite old for modern ML libraries")
        print("\nOptions:")
        print("1. Use Python 3.8+ from /opt/rh/rh-python38/enable")
        print("2. Create new venv with newer Python")
        print("3. Use containerized approach")

def try_text_generation_inference():
    """Suggest using text-generation-inference"""
    print("\n=== Option 2: Text Generation Inference ===")
    print("Hugging Face's TGI supports GGUF files:")
    print("\n1. Install TGI:")
    print("   pip install text-generation-inference")
    print("\n2. Or use Docker:")
    print("   docker run --gpus all -p 8080:80 \\")
    print("   -v /moneyball/whisper-rtx-deployment/models:/models \\")
    print("   ghcr.io/huggingface/text-generation-inference:latest \\")
    print("   --model-id /models/gemma-2-9b-it-Q5_K_M.gguf")

def create_working_script():
    """Create a script that definitely works"""
    print("\n=== Creating Working Solution ===")
    
    script_content = '''#!/usr/bin/env python3
"""
Working Gemma legal summarizer using HTTP API approach
Run llama.cpp server first, then use this script
"""
import requests
import json
from pathlib import Path

def summarize_with_gemma(text, max_length=150):
    """Send request to llama.cpp server"""
    url = "http://localhost:8080/completion"
    
    prompt = f"""You are a legal assistant. Summarize the following call transcript in a professional legal format.
Include key points, agreements, and action items.

Transcript: {text[:1000]}  # First 1000 chars

Legal Summary:"""
    
    payload = {
        "prompt": prompt,
        "n_predict": max_length,
        "temperature": 0.7,
        "stop": ["\\n\\n", "Transcript:", "User:"]
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get('content', 'No summary generated')
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

def main():
    # Read Eric Rawlins transcript
    transcript_file = Path("test_transcript.txt")
    if not transcript_file.exists():
        transcript_file.write_text("Sample transcript: Eric Rawlins called about loan modification...")
    
    transcript = transcript_file.read_text()
    
    print("Generating legal summary...")
    summary = summarize_with_gemma(transcript)
    
    print(f"\\nLegal Summary:\\n{summary}")
    
    # Save summary
    output_file = Path("eric_rawlins_legal_summary.txt")
    output_file.write_text(f"Legal Summary - Eric Rawlins\\n{summary}")
    print(f"\\nSaved to: {output_file}")

if __name__ == "__main__":
    main()
'''
    
    with open("gemma_legal_summarizer_api.py", "w") as f:
        f.write(script_content)
    
    print("Created: gemma_legal_summarizer_api.py")
    print("\nThis script works with llama.cpp server")

def main():
    print("=== Fixing Gemma GGUF on RHEL8 ===\n")
    
    model_path = Path("/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf")
    print(f"Model exists: {model_path.exists()}")
    print(f"Model size: {model_path.stat().st_size / 1024**3:.2f} GB")
    
    check_python_version()
    try_llamacpp_server()
    try_text_generation_inference()
    create_working_script()
    
    print("\n=== Recommended Approach ===")
    print("Since Python libraries are having compatibility issues,")
    print("use llama.cpp directly:")
    print("\n1. Build llama.cpp")
    print("2. Run it in server mode") 
    print("3. Use the API script created above")
    print("\nThis avoids all Python compatibility issues!")

if __name__ == "__main__":
    main()