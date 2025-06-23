#!/usr/bin/env python3
"""
Check Python files for common f-string errors BEFORE running them
Helps prevent the frustrating syntax errors we keep hitting
"""

import sys
import re

def check_file(filename):
    """Check a Python file for common f-string errors"""
    
    print(f"\nChecking {filename} for f-string issues...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    errors_found = False
    
    for i, line in enumerate(lines, 1):
        # Check for f-strings with backslashes in expressions
        # Pattern: f"...{...\.}.."
        if re.search(r'f["\'].*\{[^}]*\\[^}]*\}', line):
            print(f"❌ Line {i}: f-string expression contains backslash")
            print(f"   {line.strip()}")
            errors_found = True
        
        # Check for nested quotes issues
        if re.search(r'f""".*\{.*["\'].*["\'].*\}.*"""', line):
            # Check if quotes might conflict
            if '"""' in line and "'" not in line:
                print(f"⚠️  Line {i}: Complex f-string - check quote nesting")
                print(f"   {line.strip()}")
        
        # Check for .replace() with backslashes in f-strings
        if re.search(r'f["\'].*\{.*\.replace\([^)]*\\[^)]*\).*\}', line):
            print(f"❌ Line {i}: .replace() with backslash in f-string expression")
            print(f"   {line.strip()}")
            errors_found = True
    
    if not errors_found:
        print("✅ No f-string errors found!")
    else:
        print("\n💡 Fix: Move expressions with backslashes outside the f-string")
        print("Example: formatted = text.replace('\\n', '<br>')")
        print("         f'Result: {formatted}'")
    
    return not errors_found

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        check_file(filename)
    else:
        # Check all our recent files
        files = [
            'extract_loan_facts.py',
            'unleash_loan_kraken.py',
            'generate_legal_loan_summary.py'
        ]
        
        print("Checking recent files for f-string errors...")
        all_good = True
        for f in files:
            try:
                if not check_file(f):
                    all_good = False
            except FileNotFoundError:
                print(f"⚠️  {f} not found")
        
        if all_good:
            print("\n✅ All files are clean!")
        else:
            print("\n❌ Fix the errors above before running!")