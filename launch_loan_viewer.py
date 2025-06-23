#!/usr/bin/env python3
"""
Quick launcher for the enhanced loan viewer system
"""

import os
import sys
import subprocess
import webbrowser
import time

def check_apis():
    """Check if APIs are running"""
    import requests
    
    apis = {
        'Search API (8000)': 'http://localhost:8000/docs',
        'Timeline API (8001)': 'http://localhost:8001/docs'
    }
    
    running = {}
    for name, url in apis.items():
        try:
            requests.get(url, timeout=1)
            running[name] = True
            print(f"✅ {name} is running")
        except:
            running[name] = False
            print(f"❌ {name} is NOT running")
    
    return all(running.values())

def main():
    print("""
    🚀 Loan Timeline Viewer Launcher
    ================================
    """)
    
    # Check if APIs are running
    print("Checking API status...")
    if not check_apis():
        print("\n⚠️  APIs are not running!")
        print("\nTo start the APIs, open two terminal windows and run:")
        print("  Terminal 1: python loan_search_api.py")
        print("  Terminal 2: python loan_timeline_api.py")
        print("\nOnce the APIs are running, press Enter to continue...")
        input()
    
    print("\n✅ APIs are running!\n")
    
    # Menu
    while True:
        print("""
What would you like to do?

1. Open Enhanced Loan Viewer (recommended)
2. Open Basic Loan Viewer
3. Generate Enhanced Summary for a loan
4. Create batch file to open all transcripts
5. Search for loans by user
6. Exit

        """)
        
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == '1':
            print("\n🌐 Opening Enhanced Loan Viewer...")
            webbrowser.open('enhanced_loan_viewer.html')
            print("✅ Opened in browser!")
            
        elif choice == '2':
            print("\n🌐 Opening Basic Loan Viewer...")
            webbrowser.open('view_loan_now.html')
            print("✅ Opened in browser!")
            
        elif choice == '3':
            loan = input("\nEnter loan number: ").strip()
            if loan:
                print(f"\n📊 Generating enhanced summary for loan {loan}...")
                subprocess.run([sys.executable, 'auto_generate_summary.py', loan])
            
        elif choice == '4':
            loan = input("\nEnter loan number: ").strip()
            if loan:
                print(f"\n📁 Creating transcript batch file for loan {loan}...")
                subprocess.run([sys.executable, 'open_transcripts.py', loan])
            
        elif choice == '5':
            user = input("\nEnter user name to search: ").strip()
            if user:
                print(f"\n🔍 Searching for loans by {user}...")
                try:
                    import requests
                    response = requests.get(f'http://localhost:8000/search/by-user?user={user}')
                    if response.ok:
                        loans = response.json()
                        print(f"\nFound {len(loans)} loans for {user}:")
                        for loan in loans[:10]:  # Show first 10
                            print(f"  - Loan #{loan['loan_number']}: {loan['call_count']} calls")
                        if len(loans) > 10:
                            print(f"  ... and {len(loans) - 10} more")
                except Exception as e:
                    print(f"Error: {e}")
            
        elif choice == '6':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()