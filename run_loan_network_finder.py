#!/usr/bin/env python3
"""
Simple wrapper to run the smart loan network finder
and save results for further processing
"""

import sys
import os

# Add the whisper-rtx-deployment directory to path
sys.path.append('whisper-rtx-deployment')

from smart_loan_network_finder import find_loan_officer_networks, create_comprehensive_timeline
import json
from datetime import datetime

def main():
    print("="*80)
    print("RUNNING SMART LOAN NETWORK FINDER")
    print("="*80)
    
    # Run the network finder
    loan_officers, to_transcribe = find_loan_officer_networks()
    
    # Save results
    results = {
        'generated_at': datetime.now().isoformat(),
        'loan_officers': loan_officers,
        'total_to_transcribe': len(to_transcribe),
        'recordings_to_transcribe': to_transcribe[:100]  # First 100
    }
    
    with open('loan_network_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to loan_network_results.json")
    print(f"\nNext steps:")
    print(f"1. Run: python process_loan_networks.py")
    print(f"2. Or transcribe specific recordings from the JSON file")
    
    # Test timeline for a specific loan if we found any
    if to_transcribe and 'loan_numbers' in to_transcribe[0]:
        print(f"\n3. To see a loan timeline, run:")
        print(f"   python -c \"from smart_loan_network_finder import create_comprehensive_timeline; create_comprehensive_timeline('12345678')\"")

if __name__ == "__main__":
    main()