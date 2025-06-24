#!/usr/bin/env python3
"""
FIND LOANS WITH STRONG NETWORKS - For Enterprise AI Architect
Looking for loans with 10+ calls in the network
"""

import pymysql
import json
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def find_strong_networks():
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("="*80)
    print("FINDING LOANS WITH STRONG NETWORKS (10+ CALLS)")
    print("="*80)
    
    # Step 1: Find loans with their loan officers
    print("\n1. Finding loans and identifying loan officers...")
    cursor.execute("""
        SELECT 
            ct.loan_numbers,
            t.remoteParty as loan_officer,
            MIN(t.timestamp) as first_mention,
            COUNT(DISTINCT ct.orkuid) as direct_mentions
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers != '[]'
        AND ct.loan_numbers NOT LIKE '%,%'  -- Single loan only for clarity
        GROUP BY ct.loan_numbers, t.remoteParty
        HAVING direct_mentions >= 1
        ORDER BY direct_mentions DESC
        LIMIT 50
    """)
    
    loan_candidates = cursor.fetchall()
    strong_networks = []
    
    print(f"\nFound {len(loan_candidates)} loan/officer combinations")
    print("\n2. Checking network strength...")
    
    # Step 2: For each loan, count total network calls
    for candidate in loan_candidates:
        loans = json.loads(candidate['loan_numbers'])
        loan_number = loans[0] if loans else None
        
        if not loan_number:
            continue
            
        loan_officer = candidate['loan_officer']
        first_mention = candidate['first_mention']
        
        # Date range: 20 days before and after first mention
        start_date = first_mention - timedelta(days=20)
        end_date = first_mention + timedelta(days=20)
        
        # Count ALL calls from this loan officer in the time window
        cursor.execute("""
            SELECT COUNT(DISTINCT t.orkUid) as network_calls
            FROM orktape t
            WHERE (t.remoteParty = %s OR t.localParty = %s)
            AND t.timestamp BETWEEN %s AND %s
            AND t.duration >= 30
        """, (loan_officer, loan_officer, start_date, end_date))
        
        network_count = cursor.fetchone()['network_calls']
        
        if network_count >= 10:
            strong_networks.append({
                'loan_number': loan_number,
                'loan_officer': loan_officer,
                'direct_mentions': candidate['direct_mentions'],
                'network_calls': network_count,
                'first_mention': first_mention
            })
            
            print(f"\n✅ STRONG NETWORK FOUND!")
            print(f"   Loan: {loan_number}")
            print(f"   Officer: {loan_officer}")
            print(f"   Direct mentions: {candidate['direct_mentions']}")
            print(f"   Total network calls: {network_count}")
    
    # Step 3: Show top 5 strongest networks
    print(f"\n\n{'='*80}")
    print("TOP 5 STRONGEST LOAN NETWORKS")
    print("="*80)
    
    strong_networks.sort(key=lambda x: x['network_calls'], reverse=True)
    
    for idx, network in enumerate(strong_networks[:5], 1):
        print(f"\n{idx}. Loan #{network['loan_number']}")
        print(f"   Loan Officer: {network['loan_officer']}")
        print(f"   Network Size: {network['network_calls']} calls")
        print(f"   Direct Mentions: {network['direct_mentions']}")
        print(f"   First Contact: {network['first_mention'].strftime('%Y-%m-%d')}")
        
        # Generate visualization command
        print(f"   📊 Visualize: python visualize_loan_network_simple.py")
        print(f"      Enter: {network['loan_number']}")
    
    # Save results
    with open('strong_loan_networks.json', 'w') as f:
        json.dump(strong_networks[:5], f, indent=2, default=str)
    
    print(f"\n\n✅ Saved top 5 networks to strong_loan_networks.json")
    print(f"\n🎯 TOTAL LOANS ANALYZED: {len(loan_candidates)}")
    print(f"🎯 STRONG NETWORKS FOUND: {len(strong_networks)}")
    
    cursor.close()
    conn.close()
    
    return strong_networks[:5]

if __name__ == "__main__":
    networks = find_strong_networks()
    
    print("\n\n🚀 READY FOR ARCHITECT!")
    print("These loans show complete customer journeys with 10+ interactions")