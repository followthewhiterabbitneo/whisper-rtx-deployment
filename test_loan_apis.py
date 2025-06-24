#!/usr/bin/env python3
"""
Test the loan search and timeline APIs with discovered loan numbers
"""

import requests
import json

# API endpoints (adjust port if needed)
SEARCH_API = "http://localhost:8000"
TIMELINE_API = "http://localhost:8001"  # If timeline runs on different port

# Loan numbers we discovered
test_loans = ["1225381964", "1225344762"]

def test_loan_search_api():
    """Test the loan search API"""
    print("="*60)
    print("TESTING LOAN SEARCH API")
    print("="*60)
    
    for loan in test_loans:
        print(f"\n📍 Searching for loan: {loan}")
        
        try:
            # Test the search endpoint
            response = requests.get(f"{SEARCH_API}/api/search/loan/{loan}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {len(data.get('results', []))} results")
                
                # Show first result
                if data.get('results'):
                    first = data['results'][0]
                    print(f"   First call: {first.get('orkuid')}")
                    print(f"   Date: {first.get('timestamp')}")
                    print(f"   Duration: {first.get('duration')}s")
                    print(f"   Parties: {first.get('localParty')} ↔ {first.get('remoteParty')}")
            else:
                print(f"❌ Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to API. Is it running?")
            print("   Start it with: python loan_search_api.py")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_loan_timeline_api():
    """Test the loan timeline API"""
    print("\n\n" + "="*60)
    print("TESTING LOAN TIMELINE API")
    print("="*60)
    
    for loan in test_loans:
        print(f"\n📍 Getting timeline for loan: {loan}")
        
        try:
            # Test the timeline endpoint
            response = requests.get(f"{TIMELINE_API}/api/timeline/loan/{loan}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Timeline retrieved")
                print(f"   Total calls: {data.get('total_calls', 0)}")
                print(f"   Date range: {data.get('first_call')} to {data.get('last_call')}")
                print(f"   Total duration: {data.get('total_duration', 0)}s")
                
                # Show events
                events = data.get('events', [])
                if events:
                    print(f"   Timeline events: {len(events)}")
                    for i, event in enumerate(events[:3]):  # First 3 events
                        print(f"     {i+1}. {event.get('timestamp')} - {event.get('type')}")
            else:
                print(f"❌ Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Timeline API. Is it running?")
            print("   Start it with: python loan_timeline_api.py")
        except Exception as e:
            print(f"❌ Error: {e}")

def check_api_health():
    """Check if APIs are running"""
    print("CHECKING API STATUS")
    print("="*60)
    
    # Check search API
    try:
        response = requests.get(f"{SEARCH_API}/")
        print(f"✅ Loan Search API is running on {SEARCH_API}")
    except:
        print(f"❌ Loan Search API is NOT running on {SEARCH_API}")
        print("   Start it with: python loan_search_api.py")
    
    # Check timeline API (if different port)
    if TIMELINE_API != SEARCH_API:
        try:
            response = requests.get(f"{TIMELINE_API}/")
            print(f"✅ Loan Timeline API is running on {TIMELINE_API}")
        except:
            print(f"❌ Loan Timeline API is NOT running on {TIMELINE_API}")
            print("   Start it with: python loan_timeline_api.py")

if __name__ == "__main__":
    # First check if APIs are running
    check_api_health()
    
    print("\n")
    
    # Test search API
    test_loan_search_api()
    
    # Test timeline API
    test_loan_timeline_api()
    
    print("\n\n✅ API tests complete!")
    print("\nTo use in browser:")
    print(f"  Search: {SEARCH_API}/api/search/loan/1225381964")
    print(f"  Timeline: {TIMELINE_API}/api/timeline/loan/1225381964")