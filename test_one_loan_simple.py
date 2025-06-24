#!/usr/bin/env python3
"""
Simplest possible loan test - no fancy features
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

def test_simple():
    """Simplest loan test"""
    
    try:
        conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        cursor = conn.cursor()
        
        print("SIMPLE LOAN TEST")
        print("="*50)
        
        # Get one loan
        cursor.execute("""
            SELECT loan_numbers, orkuid
            FROM call_transcripts_v2
            WHERE loan_numbers != '[]'
            AND loan_numbers LIKE '%1225381964%'
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if row:
            print(f"\nFound loan in call: {row['orkuid']}")
            print(f"Loan data: {row['loan_numbers']}")
            
            # Parse the loan
            loans = json.loads(row['loan_numbers'])
            loan_number = loans[0] if loans else None
            
            if loan_number:
                print(f"\nLoan number: {loan_number}")
                
                # Count how many calls have this loan
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM call_transcripts_v2
                    WHERE loan_numbers LIKE %s
                """, (f'%{loan_number}%',))
                
                count = cursor.fetchone()['count']
                print(f"This loan appears in {count} calls")
        else:
            print("No loan found!")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_simple()