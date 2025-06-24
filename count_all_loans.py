#!/usr/bin/env python3
"""
Count total loan numbers found in the database
"""

import pymysql
import json

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def count_loans():
    """Count all loan numbers in the system"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("="*80)
    print("LOAN NUMBER STATISTICS")
    print("="*80)
    
    # 1. Total calls with loan numbers
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM call_transcripts_v2
        WHERE loan_numbers != '[]'
    """)
    
    calls_with_loans = cursor.fetchone()['total']
    print(f"\n📞 Calls containing loan numbers: {calls_with_loans:,}")
    
    # 2. Get all unique loan numbers
    print("\n🔍 Counting unique loan numbers...")
    cursor.execute("""
        SELECT loan_numbers
        FROM call_transcripts_v2
        WHERE loan_numbers != '[]'
    """)
    
    all_loans = set()
    total_mentions = 0
    
    for row in cursor.fetchall():
        loans = json.loads(row['loan_numbers'])
        all_loans.update(loans)
        total_mentions += len(loans)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Unique loan numbers found: {len(all_loans):,}")
    print(f"   Total loan mentions: {total_mentions:,}")
    print(f"   Average mentions per call: {total_mentions/calls_with_loans:.1f}")
    
    # 3. Show sample loan numbers
    print(f"\n📝 Sample loan numbers:")
    for i, loan in enumerate(sorted(all_loans)[:10]):
        print(f"   {i+1}. {loan}")
    
    # 4. Loan distribution by date
    cursor.execute("""
        SELECT 
            DATE(t.timestamp) as date,
            COUNT(DISTINCT ct.orkuid) as calls,
            COUNT(DISTINCT ct.loan_numbers) as unique_loan_sets
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers != '[]'
        AND t.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(t.timestamp)
        ORDER BY date DESC
    """)
    
    print(f"\n📅 Last 7 days activity:")
    for row in cursor.fetchall():
        print(f"   {row['date']}: {row['calls']} calls with loans")
    
    # 5. Top loan officers by unique loans
    cursor.execute("""
        SELECT 
            t.remoteParty as phone,
            COUNT(DISTINCT ct.orkuid) as calls,
            COUNT(DISTINCT ct.loan_numbers) as unique_loan_sets
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers != '[]'
        GROUP BY t.remoteParty
        ORDER BY calls DESC
        LIMIT 5
    """)
    
    print(f"\n👥 Top 5 phone numbers by loan activity:")
    for row in cursor.fetchall():
        print(f"   {row['phone']}: {row['calls']} calls with loans")
    
    cursor.close()
    conn.close()
    
    return len(all_loans)

if __name__ == "__main__":
    total = count_loans()
    print(f"\n\n✅ Total unique loan numbers in system: {total:,}")