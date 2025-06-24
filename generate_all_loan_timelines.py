#!/usr/bin/env python3
"""
Generate timelines for ALL loans in the system
"""

import sys
sys.path.append('whisper-rtx-deployment')

from smart_loan_network_finder import create_comprehensive_timeline
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

def get_all_loan_numbers():
    """Get all unique loan numbers from the database"""
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("Finding all loan numbers in the system...")
    
    cursor.execute("""
        SELECT DISTINCT loan_numbers
        FROM call_transcripts_v2
        WHERE loan_numbers != '[]'
        ORDER BY created_at DESC
        LIMIT 100  -- Start with first 100 records to avoid too many
    """)
    
    all_loans = set()
    for row in cursor.fetchall():
        loans = json.loads(row['loan_numbers'])
        all_loans.update(loans)
    
    cursor.close()
    conn.close()
    
    return sorted(list(all_loans))

def main():
    print("="*80)
    print("GENERATING TIMELINES FOR ALL LOANS")
    print("="*80)
    
    # Get all loan numbers
    loan_numbers = get_all_loan_numbers()
    
    print(f"\nFound {len(loan_numbers)} unique loan numbers")
    print(f"First 10: {loan_numbers[:10]}")
    
    # Ask user how many to process
    print(f"\nHow many timelines to generate?")
    print(f"1. First 5 loans (quick test)")
    print(f"2. First 20 loans")
    print(f"3. All {len(loan_numbers)} loans")
    
    choice = input("\nEnter choice (1-3) or specific number: ")
    
    if choice == '1':
        process_loans = loan_numbers[:5]
    elif choice == '2':
        process_loans = loan_numbers[:20]
    elif choice == '3':
        process_loans = loan_numbers
    else:
        try:
            num = int(choice)
            process_loans = loan_numbers[:num]
        except:
            process_loans = loan_numbers[:5]
    
    print(f"\nGenerating timelines for {len(process_loans)} loans...")
    
    for idx, loan_number in enumerate(process_loans, 1):
        print(f"\n{'='*80}")
        print(f"Processing {idx}/{len(process_loans)}")
        
        try:
            create_comprehensive_timeline(loan_number)
        except Exception as e:
            print(f"Error processing loan {loan_number}: {e}")
        
        # Optional: save to file
        # with open(f'timeline_{loan_number}.txt', 'w') as f:
        #     # Redirect output to file
    
    print(f"\n\n✅ Generated {len(process_loans)} timelines!")

if __name__ == "__main__":
    main()