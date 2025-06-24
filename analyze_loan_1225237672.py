#!/usr/bin/env python3
"""
Deep dive into loan 1225237672 - the one with 26 network calls
Shows the difference between direct mentions and network expansion
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

def analyze_loan_network():
    """Analyze loan 1225237672's network"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    loan_number = "1225237672"
    
    print("="*80)
    print(f"DEEP DIVE: LOAN {loan_number}")
    print("="*80)
    
    # 1. Direct mentions
    print("\n📍 STEP 1: Finding DIRECT mentions of loan...")
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    direct_calls = cursor.fetchall()
    print(f"\n✅ Found {len(direct_calls)} calls that mention loan {loan_number}:")
    
    parties_involved = set()
    for idx, call in enumerate(direct_calls, 1):
        print(f"\n  Call {idx}:")
        print(f"    Date: {call['timestamp']}")
        print(f"    Parties: {call['localParty']} ↔ {call['remoteParty']}")
        print(f"    User: {call['user_name']}")
        print(f"    Duration: {call['duration']}s")
        
        parties_involved.add(call['localParty'])
        parties_involved.add(call['remoteParty'])
    
    # 2. Find the loan officer
    print(f"\n📍 STEP 2: Identifying loan officer...")
    
    # Count which party appears most
    party_counts = {}
    for call in direct_calls:
        for party in [call['localParty'], call['remoteParty']]:
            party_counts[party] = party_counts.get(party, 0) + 1
    
    loan_officer = max(party_counts, key=party_counts.get)
    print(f"\n✅ Loan officer identified: {loan_officer}")
    print(f"   (Appears in {party_counts[loan_officer]} of the {len(direct_calls)} direct mentions)")
    
    # 3. Get ALL calls from loan officer
    print(f"\n📍 STEP 3: Finding ALL calls involving loan officer {loan_officer}...")
    
    cursor.execute("""
        SELECT 
            t.orkUid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.loan_numbers,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM orktape t
        LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE (t.localParty = %s OR t.remoteParty = %s)
        AND t.timestamp >= DATE_SUB((SELECT MIN(timestamp) FROM orktape t2 
                                     JOIN call_transcripts_v2 ct2 ON t2.orkUid = ct2.orkuid
                                     WHERE ct2.loan_numbers LIKE %s), INTERVAL 30 DAY)
        ORDER BY t.timestamp
    """, (loan_officer, loan_officer, f'%{loan_number}%'))
    
    all_officer_calls = cursor.fetchall()
    
    # 4. Filter to relevant customers
    print(f"\n📍 STEP 4: Filtering to customers involved with this loan...")
    
    # Get customers from direct mentions
    customers = set()
    for call in direct_calls:
        other_party = call['localParty'] if call['remoteParty'] == loan_officer else call['remoteParty']
        customers.add(other_party)
    
    print(f"\n✅ Customers involved: {customers}")
    
    # Filter calls to just these customers
    network_calls = []
    for call in all_officer_calls:
        other_party = call['localParty'] if call['remoteParty'] == loan_officer else call['remoteParty']
        if other_party in customers:
            network_calls.append(call)
    
    # 5. Show the network
    print(f"\n📊 NETWORK ANALYSIS:")
    print(f"   Direct mentions: {len(direct_calls)} calls")
    print(f"   Extended network: {len(network_calls)} calls")
    print(f"   Hidden calls: {len(network_calls) - len(direct_calls)} calls")
    
    # Show timeline
    print(f"\n📅 COMPLETE TIMELINE:")
    for idx, call in enumerate(network_calls, 1):
        other_party = call['localParty'] if call['remoteParty'] == loan_officer else call['remoteParty']
        
        # Check if this call mentions the loan
        has_loan = False
        if call['loan_numbers']:
            try:
                loans = json.loads(call['loan_numbers'])
                has_loan = loan_number in loans
            except:
                pass
        
        status = "💬 LOAN MENTIONED" if has_loan else "📞 No loan mention"
        
        print(f"\n  Call {idx}: {call['timestamp']}")
        print(f"    {loan_officer} ↔ {other_party}")
        print(f"    Duration: {call['duration']}s")
        print(f"    Status: {status}")
        
        if idx > 10:
            print(f"\n  ... and {len(network_calls) - 10} more calls")
            break
    
    cursor.close()
    conn.close()
    
    print(f"\n\n✨ INSIGHT: This loan's story spans {len(network_calls)} calls,")
    print(f"   but the loan number was only mentioned in {len(direct_calls)} of them!")
    print(f"   The network approach captures the FULL customer journey.")

if __name__ == "__main__":
    analyze_loan_network()