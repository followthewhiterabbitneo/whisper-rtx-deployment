#!/usr/bin/env python3
"""
REAL BROKER NETWORKS - Fixed logic
- Broker is ALWAYS remoteParty (calling IN)
- Exclude internal UWM calls (1555, 1947 processor)
- Focus on REAL area codes
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

def find_real_broker_networks():
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("="*80)
    print("FINDING REAL BROKER LOAN NETWORKS")
    print("="*80)
    
    # Step 1: Find BROKERS (remoteParty) who mention loans
    print("\n1. Finding REAL BROKERS (external callers)...")
    cursor.execute("""
        SELECT 
            t.remoteParty as broker_phone,
            ct.loan_numbers,
            COUNT(DISTINCT ct.orkuid) as loan_mentions,
            MIN(t.timestamp) as first_call
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers != '[]'
        AND t.remoteParty NOT LIKE '+1555%'  -- Not internal UWM
        AND t.remoteParty NOT LIKE '%1947242%'  -- Not processor
        AND t.remoteParty NOT LIKE '1555%'   -- Not internal
        AND LENGTH(t.remoteParty) >= 10      -- Real phone numbers
        GROUP BY t.remoteParty
        HAVING loan_mentions >= 2  -- Brokers mention loans multiple times
        ORDER BY loan_mentions DESC
        LIMIT 20
    """)
    
    brokers = cursor.fetchall()
    print(f"\nFound {len(brokers)} real brokers")
    
    # Step 2: For each broker, find their loan networks
    print("\n2. Analyzing broker networks...")
    
    strong_networks = []
    
    for broker in brokers[:10]:  # Top 10 brokers
        broker_phone = broker['broker_phone']
        loans = json.loads(broker['loan_numbers'])
        
        # Get a specific loan this broker worked on
        if not loans:
            continue
            
        loan_number = loans[0]
        
        # Find ALL calls from this broker (within 30 days of first loan mention)
        first_call = broker['first_call']
        start_date = first_call - timedelta(days=15)
        end_date = first_call + timedelta(days=30)
        
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT t.orkUid) as total_calls,
                COUNT(DISTINCT CASE WHEN ct.loan_numbers IS NOT NULL THEN t.orkUid END) as calls_with_loans,
                COUNT(DISTINCT t.localParty) as uwm_contacts,
                SUM(t.duration) as total_duration
            FROM orktape t
            LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
            WHERE t.remoteParty = %s
            AND t.timestamp BETWEEN %s AND %s
            AND t.localParty NOT LIKE '%%1947242%%'  -- Exclude processor on local side too
            AND t.duration >= 30  -- Real conversations
        """, (broker_phone, start_date, end_date))
        
        network = cursor.fetchone()
        
        if network['total_calls'] >= 5:  # At least 5 calls
            # Get loan details
            cursor.execute("""
                SELECT DISTINCT
                    JSON_UNQUOTE(JSON_EXTRACT(ct.loan_numbers, '$[0]')) as loan,
                    COUNT(DISTINCT t.orkUid) as mentions
                FROM call_transcripts_v2 ct
                JOIN orktape t ON ct.orkuid = t.orkUid
                WHERE t.remoteParty = %s
                AND ct.loan_numbers != '[]'
                GROUP BY loan
                ORDER BY mentions DESC
                LIMIT 3
            """, (broker_phone,))
            
            top_loans = [row['loan'] for row in cursor.fetchall() if row['loan']]
            
            strong_networks.append({
                'broker_phone': broker_phone,
                'primary_loan': loan_number,
                'all_loans': top_loans,
                'total_calls': network['total_calls'],
                'calls_with_loans': network['calls_with_loans'],
                'uwm_contacts': network['uwm_contacts'],
                'total_minutes': network['total_duration'] / 60,
                'first_call': first_call
            })
            
            print(f"\n✅ STRONG BROKER NETWORK:")
            print(f"   Broker: {broker_phone}")
            print(f"   Primary Loan: {loan_number}")
            print(f"   Total Calls: {network['total_calls']}")
            print(f"   UWM Contacts: {network['uwm_contacts']} different team members")
            print(f"   Total Time: {network['total_duration']/60:.1f} minutes")
    
    # Step 3: Show top 5
    print(f"\n\n{'='*80}")
    print("TOP 5 BROKER NETWORKS FOR ARCHITECT")
    print("="*80)
    
    strong_networks.sort(key=lambda x: x['total_calls'], reverse=True)
    
    for idx, network in enumerate(strong_networks[:5], 1):
        print(f"\n{idx}. BROKER: {network['broker_phone']}")
        print(f"   Loans: {', '.join(network['all_loans'][:3])}")
        print(f"   Network: {network['total_calls']} calls to {network['uwm_contacts']} UWM team members")
        print(f"   Duration: {network['total_minutes']:.1f} minutes total")
        print(f"   Loan mentions: {network['calls_with_loans']} calls")
        
    # Generate visualization script
    print("\n\n📊 TO VISUALIZE THESE NETWORKS:")
    for idx, network in enumerate(strong_networks[:5], 1):
        print(f"\n{idx}. python visualize_broker_network.py {network['primary_loan']} {network['broker_phone']}")
    
    # Save results
    with open('real_broker_networks.json', 'w') as f:
        json.dump(strong_networks[:5], f, indent=2, default=str)
    
    print(f"\n\n✅ Saved to real_broker_networks.json")
    
    cursor.close()
    conn.close()
    
    return strong_networks[:5]

if __name__ == "__main__":
    networks = find_real_broker_networks()
    print("\n🎯 These show REAL broker-to-UWM loan lifecycles!")