#!/usr/bin/env python3
"""
Upload RTX 4090 recon results to Kaggle dataset
"""

import os
import json
import subprocess
from datetime import datetime

def upload_to_kaggle(results_file="rtx_4090_recon_results.json"):
    """Upload recon results to Kaggle dataset"""
    
    # Check if results file exists
    if not os.path.exists(results_file):
        print(f"Error: {results_file} not found. Run the recon script first!")
        return
    
    # Create dataset metadata
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dataset_name = f"rtx-4090-recon-{timestamp}"
    
    # Create a temporary directory for the dataset
    os.makedirs("kaggle_upload", exist_ok=True)
    
    # Copy results file
    subprocess.run(f"cp {results_file} kaggle_upload/", shell=True)
    
    # Create dataset-metadata.json
    metadata = {
        "title": f"RTX 4090 Recon Results {timestamp}",
        "id": f"followthewhiterabbitneo/{dataset_name}",
        "licenses": [{"name": "CC0-1.0"}],
        "resources": [
            {
                "path": results_file,
                "description": "RTX 4090 environment reconnaissance results"
            }
        ]
    }
    
    with open("kaggle_upload/dataset-metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Creating Kaggle dataset: {dataset_name}")
    print("\nTo upload to Kaggle:")
    print("1. Make sure you have kaggle CLI installed and configured")
    print("2. Run these commands:")
    print(f"   cd kaggle_upload")
    print(f"   kaggle datasets create -p .")
    print("\nOr use the Kaggle web interface:")
    print("1. Go to https://www.kaggle.com/datasets")
    print("2. Click 'New Dataset'")
    print(f"3. Upload the file: {results_file}")
    print(f"4. Name it: {dataset_name}")
    
    # Also save instructions to a file
    with open("kaggle_upload/UPLOAD_INSTRUCTIONS.txt", "w") as f:
        f.write(f"RTX 4090 Recon Upload Instructions\n")
        f.write(f"==================================\n\n")
        f.write(f"Dataset Name: {dataset_name}\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write(f"Option 1 - Command Line:\n")
        f.write(f"cd kaggle_upload\n")
        f.write(f"kaggle datasets create -p .\n\n")
        f.write(f"Option 2 - Web Interface:\n")
        f.write(f"1. Go to https://www.kaggle.com/datasets\n")
        f.write(f"2. Click 'New Dataset'\n")
        f.write(f"3. Upload: {results_file}\n")
        f.write(f"4. Name it: {dataset_name}\n")

if __name__ == "__main__":
    upload_to_kaggle()