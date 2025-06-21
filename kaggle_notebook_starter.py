# Kaggle Notebook Starter - RTX 4090 Whisper Deployment
# 
# To use this in Kaggle:
# 1. Create new notebook at https://www.kaggle.com/code
# 2. Add your GitHub repo as a data source:
#    - Click "Add data" 
#    - Search for "followthewhiterabbitneo/whisper-rtx-deployment"
#    - Or use GitHub import option
# 3. Copy this code into the notebook

import os
import sys
import subprocess

# Clone the GitHub repo (if not already available as dataset)
if not os.path.exists('/kaggle/input/whisper-rtx-deployment'):
    !git clone https://github.com/followthewhiterabbitneo/whisper-rtx-deployment.git
    sys.path.append('./whisper-rtx-deployment')
else:
    sys.path.append('/kaggle/input/whisper-rtx-deployment')

# Import and run the recon script
from rtx_4090_recon import main

# Run reconnaissance
print("Running RTX 4090 environment reconnaissance...")
print("Note: This will show Kaggle's environment, not your actual RTX 4090")
print("To run on your RTX 4090, clone the repo locally instead")

# Check Kaggle GPU
!nvidia-smi

# Run the recon
main()

# Upload results as Kaggle dataset output
print("\nResults saved! You can:")
print("1. Download rtx_4090_recon_results.json from notebook output")
print("2. Save this notebook with output to create a versioned dataset")
print("3. Run this locally on your RTX 4090 for accurate results")