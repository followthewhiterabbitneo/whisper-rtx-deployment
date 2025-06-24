#!/usr/bin/env python3
"""
First principles test for loan search functionality
Tests the basic loan search on sample loan numbers
"""

import pymysql
import json
from datetime import datetime

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def test_loan_search():
    """Test loan search with first principles approach"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("="*80)
    print("FIRST PRINCIPLES LOAN SEARCH TEST")
    print("="*80)
    
    # Step 1: Get some recent loan numbers to test
    print("\n1. Finding recent loan numbers...")
    cursor.execute("""
        SELECT DISTINCT loan_numbers
        FROM call_transcripts_v2
        WHERE loan_numbers != '[]'
        AND created_at >= '2025-06-01'
        ORDER BY created_at DESC
        LIMIT 5
    """)
    
    test_loans = []
    for row in cursor.fetchall():
        loans = json.loads(row['loan_numbers'])
        test_loans.extend(loans)
    
    # Get unique loan numbers
    test_loans = list(set(test_loans))[:3]  # Test first 3
    
    print(f"   Testing with loans: {test_loans}")
    
    # Step 2: Test each loan number
    for loan_number in test_loans:
        print(f"\n{'='*60}")
        print(f"TESTING LOAN: {loan_number}")
        print(f"{'='*60}")
        
        # Find all calls mentioning this loan
        cursor.execute("""
            SELECT 
                ct.orkuid,
                ct.loan_numbers,
                ct.transcript_path,
                t.timestamp,
                t.duration,
                t.localParty,
                t.remoteParty,
                t.filename,
                COALESCE(CONCAT(u.firstname, ' ', u.lastname), 
                         COALESCE(t.localParty, t.remoteParty)) as user_name
            FROM call_transcripts_v2 ct
            JOIN orktape t ON ct.orkuid = t.orkUid
            LEFT JOIN orksegment s ON t.id = s.tape_id
            LEFT JOIN orkuser u ON s.user_id = u.id
            WHERE ct.loan_numbers LIKE %s
            ORDER BY t.timestamp
        """, (f'%{loan_number}%',))
        
        calls = cursor.fetchall()
        
        print(f"\nFound {len(calls)} calls for loan {loan_number}:")
        
        for idx, call in enumerate(calls, 1):
            print(f"\n  Call {idx}:")
            print(f"    ID: {call['orkuid']}")
            print(f"    Date: {call['timestamp']}")
            print(f"    Duration: {call['duration']}s")
            print(f"    Parties: {call['localParty']} ↔ {call['remoteParty']}")
            print(f"    User: {call['user_name']}")
            
            # Show all loans mentioned in this call
            all_loans = json.loads(call['loan_numbers'])
            print(f"    Loans mentioned: {all_loans}")
            
            # Check if transcript exists
            if call['transcript_path']:
                print(f"    ✓ Has transcript at: {call['transcript_path']}")
            else:
                print(f"    ✗ No transcript available")
        
        # Summary statistics
        total_duration = sum(call['duration'] for call in calls)
        print(f"\n  Summary:")
        print(f"    Total calls: {len(calls)}")
        print(f"    Total duration: {total_duration}s ({total_duration/60:.1f} minutes)")
        print(f"    Transcripts available: {sum(1 for c in calls if c['transcript_path'])}/{len(calls)}")
    
    # Step 3: Test loan officer network
    print(f"\n\n{'='*80}")
    print("LOAN OFFICER NETWORK TEST")
    print(f"{'='*80}")
    
    # Find a loan officer who mentioned multiple loans
    cursor.execute("""
        SELECT 
            t.remoteParty as phone_number,
            COUNT(DISTINCT ct.orkuid) as call_count,
            COUNT(DISTINCT JSON_EXTRACT(ct.loan_numbers, '$[*]')) as unique_loans
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers != '[]'
        AND t.timestamp >= '2025-06-01'
        GROUP BY t.remoteParty
        HAVING call_count > 5
        ORDER BY unique_loans DESC
        LIMIT 1
    """)
    
    officer = cursor.fetchone()
    if officer:
        print(f"\nTesting loan officer: {officer['phone_number']}")
        print(f"  Calls with loans: {officer['call_count']}")
        
        # Get all their calls (with and without loans)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_calls,
                COUNT(CASE WHEN ct.loan_numbers != '[]' THEN 1 END) as calls_with_loans
            FROM orktape t
            LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
            WHERE t.remoteParty = %s
            AND t.timestamp >= '2025-06-01'
        """, (officer['phone_number'],))
        
        stats = cursor.fetchone()
        print(f"  Total calls: {stats['total_calls']}")
        print(f"  Calls with loans: {stats['calls_with_loans']}")
        print(f"  Non-loan calls: {stats['total_calls'] - stats['calls_with_loans']}")
        
        relevance_rate = (stats['calls_with_loans'] / stats['total_calls'] * 100) if stats['total_calls'] > 0 else 0
        print(f"  Relevance rate: {relevance_rate:.1f}%")
    
    cursor.close()
    conn.close()
    
    print(f"\n\n✅ First principles test complete!")

if __name__ == "__main__":
    test_loan_search()