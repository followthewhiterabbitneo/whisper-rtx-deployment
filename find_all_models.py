#!/usr/bin/env python3
"""
Find all AI models (GGUF files) on the system
This will help us identify the exact paths to use
"""

import os
from pathlib import Path

def find_gguf_models(search_dirs=None):
    """Find all GGUF model files"""
    
    if search_dirs is None:
        search_dirs = [
            "models",
            ".",
            "C:\\Users\\estillmane\\.aria\\whisper-rtx-deployment\\models",
            "C:\\models",
            os.path.expanduser("~\\models"),
            "downloads"
        ]
    
    print("🔍 Searching for AI models (GGUF files)...\n")
    
    found_models = []
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            print(f"Searching in: {search_dir}")
            try:
                for root, dirs, files in os.walk(search_dir):
                    # Skip hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for file in files:
                        if file.endswith('.gguf'):
                            full_path = os.path.join(root, file)
                            size_mb = os.path.getsize(full_path) / (1024 * 1024)
                            
                            model_info = {
                                'path': full_path,
                                'name': file,
                                'size_mb': size_mb,
                                'relative_path': os.path.relpath(full_path, '.').replace('\\', '/')
                            }
                            found_models.append(model_info)
                            
                            print(f"  ✓ Found: {file} ({size_mb:.1f} MB)")
            except Exception as e:
                print(f"  ⚠️  Error searching {search_dir}: {e}")
    
    print(f"\n📊 Summary: Found {len(found_models)} model files\n")
    
    # Group by model type
    gemma_models = []
    llama_models = []
    other_models = []
    
    for model in found_models:
        name_lower = model['name'].lower()
        if 'gemma' in name_lower:
            gemma_models.append(model)
        elif 'llama' in name_lower:
            llama_models.append(model)
        else:
            other_models.append(model)
    
    # Print organized results
    if gemma_models:
        print("🟢 GEMMA MODELS:")
        for m in sorted(gemma_models, key=lambda x: x['size_mb'], reverse=True):
            print(f"  {m['relative_path']} ({m['size_mb']:.1f} MB)")
    
    if llama_models:
        print("\n🟣 LLAMA MODELS:")
        for m in sorted(llama_models, key=lambda x: x['size_mb'], reverse=True):
            print(f"  {m['relative_path']} ({m['size_mb']:.1f} MB)")
    
    if other_models:
        print("\n⚪ OTHER MODELS:")
        for m in sorted(other_models, key=lambda x: x['size_mb'], reverse=True):
            print(f"  {m['relative_path']} ({m['size_mb']:.1f} MB)")
    
    # Create updated model list for scripts
    print("\n📝 COPY THESE PATHS TO YOUR SCRIPTS:")
    print("-" * 60)
    
    all_paths = []
    for model in found_models:
        # Use forward slashes for compatibility
        clean_path = model['relative_path'].replace('\\', '/')
        all_paths.append(f'    "{clean_path}",')
    
    print("model_paths = [")
    for path in sorted(all_paths):
        print(path)
    print("]")
    
    # Save to file for reference
    with open("found_models.txt", "w") as f:
        f.write("AI Models Found on System\n")
        f.write("=" * 60 + "\n\n")
        
        for model in sorted(found_models, key=lambda x: x['size_mb'], reverse=True):
            f.write(f"Name: {model['name']}\n")
            f.write(f"Path: {model['path']}\n")
            f.write(f"Size: {model['size_mb']:.1f} MB\n")
            f.write(f"Relative: {model['relative_path']}\n")
            f.write("-" * 40 + "\n")
    
    print(f"\n✅ Model list saved to: found_models.txt")
    
    return found_models

if __name__ == "__main__":
    models = find_gguf_models()
    
    if not models:
        print("\n❌ No GGUF models found!")
        print("\nTo download models:")
        print("1. Check your Kaggle downloads")
        print("2. Look for .gguf files in your downloads folder")
        print("3. Move them to the models/ directory")