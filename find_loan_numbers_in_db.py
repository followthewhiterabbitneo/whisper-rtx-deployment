#!/usr/bin/env python3
"""
Find where loan numbers are stored in the database
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

def find_loan_storage():
    """Find where loan numbers are stored"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("="*80)
    print("FINDING LOAN NUMBER STORAGE LOCATIONS")
    print("="*80)
    
    # 1. Check call_transcripts_v2 table
    print("\n1. Checking call_transcripts_v2 table...")
    cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN loan_numbers != '[]' THEN 1 END) as records_with_loans,
            MIN(created_at) as earliest_record,
            MAX(created_at) as latest_record
        FROM call_transcripts_v2
    """)
    
    stats = cursor.fetchone()
    print(f"   Total records: {stats['total_records']:,}")
    print(f"   Records with loans: {stats['records_with_loans']:,}")
    print(f"   Date range: {stats['earliest_record']} to {stats['latest_record']}")
    
    # 2. Get sample loan numbers
    print("\n2. Sample loan numbers from call_transcripts_v2:")
    cursor.execute("""
        SELECT 
            orkuid,
            loan_numbers,
            created_at
        FROM call_transcripts_v2
        WHERE loan_numbers != '[]'
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    samples = cursor.fetchall()
    for sample in samples:
        loans = json.loads(sample['loan_numbers'])
        print(f"   {sample['orkuid']} - Loans: {loans} - {sample['created_at']}")
    
    # 3. Check if loan_number_index exists
    print("\n3. Checking for loan_number_index table...")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.tables 
        WHERE table_schema = 'oreka' 
        AND table_name = 'loan_number_index'
    """)
    
    if cursor.fetchone()['count'] > 0:
        cursor.execute("SELECT COUNT(*) as total FROM loan_number_index")
        count = cursor.fetchone()['total']
        print(f"   ✅ loan_number_index exists with {count:,} records")
    else:
        print("   ❌ loan_number_index does not exist")
    
    # 4. Get some specific loan numbers for testing
    print("\n4. Getting specific loan numbers for testing:")
    cursor.execute("""
        SELECT DISTINCT loan_numbers
        FROM call_transcripts_v2
        WHERE loan_numbers != '[]'
        AND loan_numbers LIKE '%[%'
        LIMIT 20
    """)
    
    all_loans = set()
    for row in cursor.fetchall():
        loans = json.loads(row['loan_numbers'])
        all_loans.update(loans)
    
    # Print first 10 unique loan numbers
    loan_list = list(all_loans)[:10]
    print(f"\n   Unique loan numbers for testing:")
    for loan in loan_list:
        print(f"   - {loan}")
    
    cursor.close()
    conn.close()
    
    return loan_list

if __name__ == "__main__":
    loan_numbers = find_loan_storage()
    
    # Save loan numbers for testing
    with open('test_loan_numbers.json', 'w') as f:
        json.dump(loan_numbers, f, indent=2)
    
    print(f"\n✅ Saved {len(loan_numbers)} loan numbers to test_loan_numbers.json")