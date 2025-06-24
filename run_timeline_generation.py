#!/usr/bin/env python3
"""
Run comprehensive timeline generation for specific loans
"""

import sys
sys.path.append('whisper-rtx-deployment')

from smart_loan_network_finder import create_comprehensive_timeline

# The loan numbers we found earlier
loan_numbers = ["1225381964", "1225344762"]

print("GENERATING COMPREHENSIVE TIMELINES")
print("="*80)

for loan_number in loan_numbers:
    create_comprehensive_timeline(loan_number)
    print("\n" + "="*80 + "\n")

print("✅ Timeline generation complete!")