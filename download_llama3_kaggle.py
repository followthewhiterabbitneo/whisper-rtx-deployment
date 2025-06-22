#!/usr/bin/env python3
"""
Download Llama 3 8B GGUF from Kaggle
This might work better than the Gemma GGUF
"""
import os
import sys
import subprocess
from pathlib import Path

# Set Kaggle cache to /moneyball
os.environ['KAGGLE_USERNAME'] = os.environ.get('KAGGLE_USERNAME', '')
os.environ['KAGGLE_KEY'] = os.environ.get('KAGGLE_KEY', '')
os.environ['KAGGLE_CONFIG_DIR'] = '/moneyball/kaggle'

def download_llama3():
    """Download Llama 3 8B GGUF from Kaggle"""
    print("=== Downloading Llama 3 8B GGUF ===")
    
    try:
        import kagglehub
    except ImportError:
        print("Installing kagglehub...")
        subprocess.run([sys.executable, "-m", "pip", "install", "kagglehub"])
        import kagglehub
    
    # Download to /moneyball
    print("\nDownloading Llama 3 8B Instruct GGUF...")
    print("This may take a while...")
    
    # Set download directory
    os.environ['KAGGLEHUB_CACHE_DIR'] = '/moneyball/kaggle/cache'
    
    try:
        path = kagglehub.dataset_download("rikstillman/llama-3-8b-instruct-gguf")
        print(f"\n✓ Downloaded to: {path}")
        
        # List downloaded files
        print("\nDownloaded files:")
        for file in Path(path).rglob("*.gguf"):
            print(f"  - {file.name} ({file.stat().st_size / 1024**3:.2f} GB)")
            
            # Copy to models directory
            target = Path("/moneyball/whisper-rtx-deployment/models") / file.name
            print(f"  Copying to: {target}")
            subprocess.run(["cp", str(file), str(target)])
            
            # Create Ollama Modelfile for Llama 3
            modelfile_content = f"""FROM {target}

PARAMETER temperature 0.7
PARAMETER num_ctx 4096
PARAMETER num_gpu 999

TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a helpful legal assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>
{{{{ .Prompt }}}}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
"""
            
            modelfile_path = Path("/moneyball/ollama/Llama3Modelfile")
            modelfile_path.write_text(modelfile_content)
            print(f"\n✓ Created Modelfile: {modelfile_path}")
            
            print("\nTo use Llama 3:")
            print(f"1. /moneyball/ollama/bin/ollama create llama3-legal -f {modelfile_path}")
            print("2. /moneyball/ollama/bin/ollama run llama3-legal 'Your prompt'")
            
            return True
            
    except Exception as e:
        print(f"Error downloading: {e}")
        
        # Alternative datasets
        print("\n=== Alternative Models on Kaggle ===")
        print("Try these commands:")
        print('kagglehub.dataset_download("xzuyn/llama-2-7b-gguf")')
        print('kagglehub.dataset_download("matthewdeutsch/llama-7b-gguf")')
        
        return False

def test_llama3():
    """Test if Llama 3 works with Ollama"""
    print("\n=== Testing Llama 3 with Ollama ===")
    
    # Make sure Ollama is running
    if not subprocess.run(["pgrep", "-f", "ollama"], capture_output=True).returncode == 0:
        print("Starting Ollama...")
        subprocess.Popen(["/moneyball/ollama/bin/ollama", "serve"])
        import time
        time.sleep(5)
    
    # Create model
    print("Creating llama3-legal model...")
    result = subprocess.run([
        "/moneyball/ollama/bin/ollama", 
        "create", 
        "llama3-legal", 
        "-f", 
        "/moneyball/ollama/Llama3Modelfile"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Model created successfully!")
        
        # Test it
        print("\nTesting summary...")
        test_prompt = "Summarize: Eric Rawlins called about loan modification status. Application submitted June 1st."
        
        result = subprocess.run([
            "/moneyball/ollama/bin/ollama",
            "run",
            "llama3-legal",
            test_prompt
        ], capture_output=True, text=True)
        
        print(f"Response: {result.stdout}")
    else:
        print(f"Error creating model: {result.stderr}")

if __name__ == "__main__":
    if download_llama3():
        test_llama3()
    else:
        print("\nFailed to download. Check your Kaggle credentials:")
        print("export KAGGLE_USERNAME='your_username'")
        print("export KAGGLE_KEY='your_api_key'")