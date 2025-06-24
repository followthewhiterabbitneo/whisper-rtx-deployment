#!/usr/bin/env python3
"""
First principles test - Deep dive into ONE loan (Fixed for MariaDB 5.5)
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

def test_one_loan():
    """Deep dive into a single loan"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("="*80)
    print("FIRST PRINCIPLES: ONE LOAN DEEP DIVE")
    print("="*80)
    
    # Step 1: Find ONE recent loan number
    print("\n1. Finding ONE loan number to analyze...")
    cursor.execute("""
        SELECT 
            ct.loan_numbers,
            ct.orkuid,
            t.timestamp
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers != '[]'
        AND ct.loan_numbers NOT LIKE '%,%'  -- Single loan only
        AND t.timestamp >= '2025-06-01'
        ORDER BY t.timestamp DESC
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    if not row:
        print("No recent single-loan calls found!")
        return
    
    # Extract the loan number
    loans = json.loads(row['loan_numbers'])
    loan_number = loans[0]
    
    print(f"\n✅ Selected Loan: {loan_number}")
    print(f"   From call: {row['orkuid']}")
    print(f"   Date: {row['timestamp']}")
    
    # Step 2: Get EVERY call mentioning this loan
    print(f"\n2. Finding ALL calls for loan {loan_number}...")
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
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    calls = cursor.fetchall()
    
    print(f"\n📞 Found {len(calls)} calls:")
    
    # Step 3: Analyze each call
    for idx, call in enumerate(calls, 1):
        print(f"\n{'='*60}")
        print(f"Call {idx} of {len(calls)}")
        print(f"{'='*60}")
        print(f"ID: {call['orkuid']}")
        print(f"Date/Time: {call['timestamp']}")
        print(f"Duration: {call['duration']} seconds")
        print(f"Local Party: {call['localParty']}")
        print(f"Remote Party: {call['remoteParty']}")
        print(f"User: {call['user_name']}")
        print(f"File: {call['filename']}")
        
        # Check loans in this call
        all_loans = json.loads(call['loan_numbers'])
        if len(all_loans) == 1:
            print(f"Loans: [{loan_number}] ✓ Only this loan")
        else:
            print(f"Loans: {all_loans} ⚠️ Multiple loans mentioned")
        
        # Transcript status
        if call['transcript_path']:
            print(f"Transcript: ✓ Available at {call['transcript_path']}")
            
            # Try to read a snippet
            try:
                cursor.execute("""
                    SELECT LEFT(transcript_text, 200) as snippet
                    FROM call_transcripts_v2
                    WHERE orkuid = %s
                """, (call['orkuid'],))
                result = cursor.fetchone()
                if result and result['snippet']:
                    print(f"Preview: \"{result['snippet']}...\"")
            except:
                pass
        else:
            print(f"Transcript: ✗ Not available")
    
    # Step 4: Analyze the loan timeline
    print(f"\n\n{'='*80}")
    print("LOAN TIMELINE ANALYSIS")
    print(f"{'='*80}")
    
    if calls:
        first_call = calls[0]
        last_call = calls[-1]
        total_duration = sum(c['duration'] for c in calls)
        
        print(f"\nLoan Number: {loan_number}")
        print(f"First mention: {first_call['timestamp']}")
        print(f"Last mention: {last_call['timestamp']}")
        print(f"Total calls: {len(calls)}")
        print(f"Total duration: {total_duration}s ({total_duration/60:.1f} minutes)")
        
        # Unique parties involved
        parties = set()
        for call in calls:
            parties.add(call['localParty'])
            parties.add(call['remoteParty'])
        print(f"Unique phone numbers involved: {len(parties)}")
        for party in sorted(parties):
            print(f"  - {party}")
    
    # Step 5: Check if this is part of a network
    print(f"\n\n{'='*80}")
    print("NETWORK CHECK")
    print(f"{'='*80}")
    
    # Find the most active party (likely loan officer)
    party_counts = {}
    for call in calls:
        for party in [call['localParty'], call['remoteParty']]:
            party_counts[party] = party_counts.get(party, 0) + 1
    
    loan_officer = max(party_counts, key=party_counts.get)
    print(f"\nMost active party: {loan_officer} ({party_counts[loan_officer]} calls)")
    
    # Check how many other loans this party handles (MariaDB 5.5 compatible)
    cursor.execute("""
        SELECT COUNT(DISTINCT ct.loan_numbers) as unique_loan_sets
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE (t.localParty = %s OR t.remoteParty = %s)
        AND ct.loan_numbers != '[]'
    """, (loan_officer, loan_officer))
    
    result = cursor.fetchone()
    print(f"This party is involved in {result['unique_loan_sets']} calls with loans")
    
    # Get a sample of other loans
    cursor.execute("""
        SELECT DISTINCT ct.loan_numbers
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE (t.localParty = %s OR t.remoteParty = %s)
        AND ct.loan_numbers != '[]'
        LIMIT 5
    """, (loan_officer, loan_officer))
    
    other_loans = set()
    for row in cursor.fetchall():
        loans = json.loads(row['loan_numbers'])
        other_loans.update(loans)
    
    print(f"Sample of loans handled by this party: {list(other_loans)[:5]}")
    
    cursor.close()
    conn.close()
    
    print(f"\n\n✅ First principles analysis complete for loan {loan_number}!")

if __name__ == "__main__":
    test_one_loan()