#!/usr/bin/env python3
"""
RTX 4090 Environment Reconnaissance Script
Run this on your RTX 4090 to gather system information
"""

import os
import sys
import json
import subprocess
import platform
from datetime import datetime

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Exception: {str(e)}"

def check_gpu():
    """Check GPU information"""
    gpu_info = {}
    
    # Check if nvidia-smi is available
    nvidia_smi = run_command("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader")
    gpu_info['nvidia_smi'] = nvidia_smi
    
    # Check CUDA version
    cuda_version = run_command("nvcc --version | grep 'release' | awk '{print $6}'")
    gpu_info['cuda_version'] = cuda_version
    
    # Check if torch can see GPU
    try:
        import torch
        gpu_info['torch_cuda_available'] = torch.cuda.is_available()
        gpu_info['torch_cuda_device_count'] = torch.cuda.device_count()
        if torch.cuda.is_available():
            gpu_info['torch_cuda_device_name'] = torch.cuda.get_device_name(0)
    except ImportError:
        gpu_info['torch'] = "Not installed"
    
    return gpu_info

def check_whisper_installations():
    """Check for Whisper-related installations"""
    whisper_info = {}
    
    # Check for OpenAI Whisper
    try:
        import whisper
        whisper_info['openai_whisper'] = {
            'installed': True,
            'version': whisper.__version__ if hasattr(whisper, '__version__') else 'Unknown',
            'available_models': whisper.available_models() if hasattr(whisper, 'available_models') else []
        }
    except ImportError:
        whisper_info['openai_whisper'] = {'installed': False}
    
    # Check for faster-whisper
    try:
        import faster_whisper
        whisper_info['faster_whisper'] = {
            'installed': True,
            'version': faster_whisper.__version__ if hasattr(faster_whisper, '__version__') else 'Unknown'
        }
        
        # Try to list downloaded models
        models_dir = os.path.expanduser("~/.cache/huggingface/hub")
        if os.path.exists(models_dir):
            model_dirs = [d for d in os.listdir(models_dir) if 'whisper' in d.lower()]
            whisper_info['faster_whisper']['cached_models'] = model_dirs
    except ImportError:
        whisper_info['faster_whisper'] = {'installed': False}
    
    # Check for whisperx
    try:
        import whisperx
        whisper_info['whisperx'] = {
            'installed': True,
            'version': whisperx.__version__ if hasattr(whisperx, '__version__') else 'Unknown'
        }
    except ImportError:
        whisper_info['whisperx'] = {'installed': False}
    
    return whisper_info

def check_python_packages():
    """Check installed Python packages"""
    packages = {}
    
    # Key packages to check
    check_packages = [
        'numpy', 'torch', 'torchaudio', 'transformers', 
        'fastapi', 'uvicorn', 'requests', 'psycopg2',
        'ffmpeg-python', 'pydub'
    ]
    
    for package in check_packages:
        try:
            module = __import__(package.replace('-', '_'))
            version = getattr(module, '__version__', 'Unknown')
            packages[package] = version
        except ImportError:
            packages[package] = "Not installed"
    
    return packages

def check_system_info():
    """Check system information"""
    return {
        'platform': platform.platform(),
        'python_version': sys.version,
        'hostname': platform.node(),
        'cpu_count': os.cpu_count(),
        'current_directory': os.getcwd(),
        'user': os.environ.get('USER', 'Unknown'),
        'path': os.environ.get('PATH', '').split(os.pathsep)[:5]  # First 5 PATH entries
    }

def check_file_access():
    """Check file system access"""
    access_info = {}
    
    # Check common directories
    test_paths = [
        '/mnt',
        '/nfs',
        '/data',
        os.path.expanduser('~'),
        'C:\\' if platform.system() == 'Windows' else '/'
    ]
    
    for path in test_paths:
        if os.path.exists(path):
            access_info[path] = {
                'exists': True,
                'readable': os.access(path, os.R_OK),
                'writable': os.access(path, os.W_OK)
            }
        else:
            access_info[path] = {'exists': False}
    
    return access_info

def check_network():
    """Basic network connectivity check"""
    network_info = {}
    
    # Check if we can reach common hosts
    hosts = ['github.com', 'google.com', '8.8.8.8']
    
    for host in hosts:
        result = run_command(f"ping -c 1 -W 2 {host} > /dev/null 2>&1 && echo 'OK' || echo 'Failed'")
        network_info[host] = result
    
    return network_info

def main():
    """Run all checks and save results"""
    print("Starting RTX 4090 Environment Reconnaissance...")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'system': check_system_info(),
        'gpu': check_gpu(),
        'whisper': check_whisper_installations(),
        'packages': check_python_packages(),
        'file_access': check_file_access(),
        'network': check_network()
    }
    
    # Save results
    output_file = 'rtx_4090_recon_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print("\nSummary:")
    print(f"- Platform: {results['system']['platform']}")
    print(f"- Python: {results['system']['python_version'].split()[0]}")
    print(f"- GPU: {results['gpu'].get('nvidia_smi', 'No GPU info')}")
    print(f"- Faster-Whisper: {results['whisper']['faster_whisper']['installed']}")
    print("\nPlease commit and push the results file to GitHub!")

if __name__ == "__main__":
    main()