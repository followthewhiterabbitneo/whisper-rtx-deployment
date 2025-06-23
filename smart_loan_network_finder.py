#!/usr/bin/env python3
"""
Smart loan network finder - finds all calls from loan officers
by tracking remote party numbers where loans were mentioned
"""

import pymysql
import json
from datetime import datetime
from collections import defaultdict

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def find_loan_officer_networks():
    """Find all loan officer phone numbers and their call networks"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("="*80)
    print("SMART LOAN NETWORK ANALYSIS")
    print("="*80)
    
    # Step 1: Find all remote parties who mentioned loan numbers
    print("\n1. Finding loan officer phone numbers...")
    
    cursor.execute("""
        SELECT DISTINCT
            t.remoteParty as loan_officer_number,
            t.localParty as customer_number,
            ct.loan_numbers,
            COUNT(DISTINCT ct.orkuid) as calls_with_loans
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers != '[]'
        AND t.remoteParty NOT LIKE '%Unknown%'
        GROUP BY t.remoteParty
        ORDER BY calls_with_loans DESC
    """)
    
    loan_officers = cursor.fetchall()
    
    print(f"\nFound {len(loan_officers)} potential loan officer numbers:")
    
    loan_officer_phones = []
    for officer in loan_officers[:10]:  # Top 10
        print(f"\n  Phone: {officer['loan_officer_number']}")
        print(f"  Calls with loans: {officer['calls_with_loans']}")
        loans = json.loads(officer['loan_numbers'])
        print(f"  Sample loans: {loans[:3]}")
        loan_officer_phones.append(officer['loan_officer_number'])
    
    # Step 2: Find ALL calls from these loan officers
    print("\n\n2. Finding ALL calls from loan officers (any duration)...")
    
    loan_officer_networks = {}
    
    for officer_phone in loan_officer_phones[:5]:  # Process top 5
        print(f"\n{'='*60}")
        print(f"Loan Officer: {officer_phone}")
        print(f"{'='*60}")
        
        # Get ALL calls from this officer
        cursor.execute("""
            SELECT 
                t.orkUid,
                t.filename,
                t.duration,
                t.timestamp,
                t.localParty,
                t.remoteParty,
                u.firstname,
                u.lastname,
                ct.loan_numbers,
                ct.transcript_path
            FROM orktape t
            LEFT JOIN orksegment s ON t.id = s.tape_id
            LEFT JOIN orkuser u ON s.user_id = u.id
            LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
            WHERE (t.remoteParty = %s OR t.localParty = %s)
            AND t.timestamp >= '2025-06-01'
            AND t.timestamp <= '2025-06-20'
            ORDER BY t.timestamp
        """, (officer_phone, officer_phone))
        
        calls = cursor.fetchall()
        
        # Group by customer
        customers = defaultdict(list)
        for call in calls:
            customer = call['localParty'] if call['remoteParty'] == officer_phone else call['remoteParty']
            customers[customer].append(call)
        
        print(f"\nFound {len(calls)} total calls")
        print(f"Unique customers: {len(customers)}")
        
        # Show customer summary
        for customer, customer_calls in list(customers.items())[:3]:
            print(f"\n  Customer: {customer}")
            
            # Find user name
            user_name = "Unknown"
            for call in customer_calls:
                if call['firstname']:
                    user_name = f"{call['firstname']} {call['lastname']}"
                    break
            
            print(f"  Name: {user_name}")
            print(f"  Total calls: {len(customer_calls)}")
            
            # Timeline
            print(f"  Timeline:")
            for call in customer_calls[:5]:
                duration_min = call['duration'] / 60
                loans = json.loads(call['loan_numbers']) if call['loan_numbers'] else []
                status = "✓ Has loans" if loans else "○ No transcript"
                print(f"    {call['timestamp']} - {duration_min:.1f}min - {status}")
                if loans:
                    print(f"      Loans: {loans}")
        
        loan_officer_networks[officer_phone] = {
            'total_calls': len(calls),
            'customers': len(customers),
            'calls': calls
        }
    
    # Step 3: Find calls that need transcription
    print("\n\n3. Identifying calls that need transcription...")
    
    to_transcribe = []
    
    for officer_phone, network in loan_officer_networks.items():
        for call in network['calls']:
            # If no transcript exists, add to list
            if not call['transcript_path']:
                to_transcribe.append({
                    'orkuid': call['orkUid'],
                    'filename': call['filename'],
                    'duration': call['duration'],
                    'timestamp': call['timestamp'],
                    'loan_officer': officer_phone,
                    'customer': call['localParty'] if call['remoteParty'] == officer_phone else call['remoteParty'],
                    'user_firstname': call['firstname'],
                    'user_lastname': call['lastname']
                })
    
    print(f"\nCalls needing transcription: {len(to_transcribe)}")
    print(f"Breakdown by duration:")
    
    # Duration breakdown
    short_calls = [c for c in to_transcribe if c['duration'] < 90]
    medium_calls = [c for c in to_transcribe if 90 <= c['duration'] < 300]
    long_calls = [c for c in to_transcribe if c['duration'] >= 300]
    
    print(f"  < 90 seconds: {len(short_calls)} calls")
    print(f"  90-300 seconds: {len(medium_calls)} calls")
    print(f"  > 300 seconds: {len(long_calls)} calls")
    
    cursor.close()
    conn.close()
    
    return loan_officer_phones, to_transcribe

def create_comprehensive_timeline(loan_number):
    """Create comprehensive timeline including all loan officer calls"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE TIMELINE FOR LOAN #{loan_number}")
    print(f"{'='*80}")
    
    # Get all calls mentioning this loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            ct.loan_numbers,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            u.firstname,
            u.lastname
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    direct_calls = cursor.fetchall()
    
    print(f"\nDirect mentions of loan #{loan_number}: {len(direct_calls)} calls")
    
    # Get loan officers from these calls
    loan_officers = set()
    customers = set()
    
    for call in direct_calls:
        loan_officers.add(call['remoteParty'])
        customers.add(call['localParty'])
        
        name = f"{call['firstname'] or ''} {call['lastname'] or ''}".strip() or "Unknown"
        print(f"\n{call['timestamp']} - {name}")
        print(f"  Duration: {call['duration']/60:.1f} minutes")
        print(f"  Parties: {call['localParty']} <-> {call['remoteParty']}")
    
    # Now find ALL calls between these parties
    print(f"\n\nLoan officers identified: {len(loan_officers)}")
    print(f"Customers identified: {len(customers)}")
    
    # Get extended network
    all_calls = []
    for officer in loan_officers:
        for customer in customers:
            cursor.execute("""
                SELECT 
                    t.orkUid,
                    t.timestamp,
                    t.duration,
                    t.localParty,
                    t.remoteParty,
                    ct.transcript_path,
                    ct.loan_numbers
                FROM orktape t
                LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
                WHERE ((t.localParty = %s AND t.remoteParty = %s) OR
                       (t.localParty = %s AND t.remoteParty = %s))
                AND t.timestamp >= '2025-06-01'
                ORDER BY t.timestamp
            """, (customer, officer, officer, customer))
            
            all_calls.extend(cursor.fetchall())
    
    print(f"\nTotal calls in extended network: {len(all_calls)}")
    
    cursor.close()
    conn.close()
    
    return all_calls

if __name__ == "__main__":
    # Find loan officer networks
    officers, to_transcribe = find_loan_officer_networks()
    
    # Save list of recordings to transcribe
    if to_transcribe:
        # Convert datetime objects to strings for JSON
        for rec in to_transcribe:
            if 'timestamp' in rec and hasattr(rec['timestamp'], 'isoformat'):
                rec['timestamp'] = rec['timestamp'].isoformat()
        
        with open('recordings_to_transcribe.json', 'w') as f:
            json.dump(to_transcribe, f, indent=2, default=str)
        print(f"\nSaved {len(to_transcribe)} recordings to: recordings_to_transcribe.json")
    
    # Show loan numbers found
    print("\n" + "="*60)
    print("LOAN NUMBERS FOUND SO FAR:")
    print("="*60)
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT loan_number, COUNT(*) as count
        FROM loan_number_index
        GROUP BY loan_number
        ORDER BY count DESC
    """)
    
    loans = cursor.fetchall()
    for loan in loans:
        print(f"Loan #{loan['loan_number']}: {loan['count']} calls")
    
    cursor.close()
    conn.close()
    
    print("\nNext step: Run process_loan_networks.py to transcribe all 778 calls!")