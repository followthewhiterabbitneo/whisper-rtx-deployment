#!/usr/bin/env python3
"""
FIRST PRINCIPLES: Get ALL loan IDs from the database
No fancy stuff - just a clean list of every loan number
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

def get_all_loans():
    """Get every single loan ID in the system"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("="*60)
    print("EXTRACTING ALL LOAN IDs")
    print("="*60)
    
    # Get all loan_numbers fields
    print("\nQuerying database...")
    cursor.execute("""
        SELECT loan_numbers, COUNT(*) as mentions
        FROM call_transcripts_v2
        WHERE loan_numbers != '[]'
        GROUP BY loan_numbers
    """)
    
    all_loans = {}  # loan_id -> mention_count
    
    # Parse each JSON array
    for row in cursor.fetchall():
        try:
            loans = json.loads(row['loan_numbers'])
            for loan in loans:
                if loan not in all_loans:
                    all_loans[loan] = 0
                all_loans[loan] += row['mentions']
        except:
            pass
    
    cursor.close()
    conn.close()
    
    # Sort by frequency (most mentioned first)
    sorted_loans = sorted(all_loans.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n✅ Found {len(sorted_loans)} unique loan IDs")
    print(f"\nTop 10 most mentioned:")
    for loan, count in sorted_loans[:10]:
        print(f"  {loan}: {count} mentions")
    
    # Save to file - just the loan numbers
    with open('all_loan_ids.txt', 'w') as f:
        for loan, count in sorted_loans:
            f.write(f"{loan}\n")
    
    # Also save with counts
    with open('all_loan_ids_with_counts.txt', 'w') as f:
        f.write("loan_id,mention_count\n")
        for loan, count in sorted_loans:
            f.write(f"{loan},{count}\n")
    
    print(f"\n📁 Files created:")
    print(f"   - all_loan_ids.txt (just IDs)")
    print(f"   - all_loan_ids_with_counts.txt (IDs + frequency)")
    
    return sorted_loans

if __name__ == "__main__":
    loans = get_all_loans()
    print(f"\n🎯 Ready to process {len(loans)} loans!")
    print("\nNext: Build visualizations call by call until CTC!")