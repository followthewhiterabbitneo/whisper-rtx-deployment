#!/usr/bin/env python3
"""
INSERT MISSING CALL - Add a call that should be part of a loan's journey
For calls that transferred between broker and underwriter
"""

import pymysql
from datetime import datetime
import sys

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def insert_call_to_loan(loan_number, orkuid, position=None):
    """
    Insert a missing call into a loan's journey
    
    Args:
        loan_number: The loan number this call belongs to
        orkuid: The call ID (e.g., 20250612_125406_UVCT)
        position: Optional position hint (e.g., "after call #12")
    """
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print(f"\n🔍 INSERTING CALL {orkuid} INTO LOAN {loan_number}")
    print("=" * 60)
    
    # First, check if this call exists in orktape
    cursor.execute("""
        SELECT 
            t.*,
            ct.loan_numbers,
            ct.transcript_path,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM orktape t
        LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE t.orkUid = %s
    """, (orkuid,))
    
    call = cursor.fetchone()
    
    if not call:
        print(f"❌ Error: Call {orkuid} not found in database!")
        cursor.close()
        conn.close()
        return False
    
    # Display call details
    print(f"\n📞 CALL DETAILS:")
    print(f"   Date/Time: {call['timestamp']}")
    print(f"   Duration: {call['duration']} seconds")
    print(f"   From: {call['localParty']}")
    print(f"   To: {call['remoteParty']}")
    print(f"   User: {call['user_name']}")
    
    # Check current loan assignments
    current_loans = []
    if call.get('loan_numbers'):
        try:
            import json
            current_loans = json.loads(call['loan_numbers'])
            print(f"   Current Loans: {', '.join(current_loans)}")
        except:
            pass
    
    # Check if loan already assigned
    if loan_number in current_loans:
        print(f"\n✅ This call is already assigned to loan {loan_number}")
        cursor.close()
        conn.close()
        return True
    
    # Add the loan number
    current_loans.append(loan_number)
    import json
    new_loan_json = json.dumps(current_loans)
    
    # Update or insert into call_transcripts_v2
    if call.get('loan_numbers') is not None:
        # Update existing record
        cursor.execute("""
            UPDATE call_transcripts_v2 
            SET loan_numbers = %s,
                updated_at = NOW()
            WHERE orkuid = %s
        """, (new_loan_json, orkuid))
        print(f"\n✅ Updated existing transcript record")
    else:
        # Insert new record
        cursor.execute("""
            INSERT INTO call_transcripts_v2 (orkuid, loan_numbers, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW())
        """, (orkuid, new_loan_json))
        print(f"\n✅ Created new transcript record")
    
    conn.commit()
    
    # Show the loan's updated timeline
    print(f"\n📊 UPDATED TIMELINE FOR LOAN {loan_number}:")
    
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
    
    calls = cursor.fetchall()
    
    print("-" * 80)
    print(f"{'#':<3} {'Date/Time':<20} {'From':<15} {'To':<15} {'User':<20}")
    print("-" * 80)
    
    for idx, timeline_call in enumerate(calls, 1):
        is_new = timeline_call['orkuid'] == orkuid
        marker = " ← NEW" if is_new else ""
        print(f"{idx:<3} {timeline_call['timestamp'].strftime('%m/%d/%Y %I:%M %p'):<20} {timeline_call['localParty']:<15} {timeline_call['remoteParty']:<15} {timeline_call['user_name']:<20}{marker}")
    
    cursor.close()
    conn.close()
    
    print(f"\n✅ Successfully added call {orkuid} to loan {loan_number}'s journey!")
    return True

def interactive_mode():
    """Interactive mode for inserting calls"""
    
    print("\n🔧 MISSING CALL INSERTER")
    print("Add calls that should be part of a loan's journey")
    print("-" * 50)
    
    while True:
        print("\nEnter details (or 'quit' to exit):")
        
        loan_number = input("Loan number: ").strip()
        if loan_number.lower() == 'quit':
            break
        
        orkuid = input("Call ID (orkUid): ").strip()
        if orkuid.lower() == 'quit':
            break
        
        position = input("Position hint (optional, e.g. 'after call #12'): ").strip()
        
        # Confirm
        print(f"\nReady to add call {orkuid} to loan {loan_number}")
        confirm = input("Proceed? (y/n): ").strip().lower()
        
        if confirm == 'y':
            success = insert_call_to_loan(loan_number, orkuid, position)
            if success:
                print("\n✅ Success! The timeline has been updated.")
        else:
            print("Skipped.")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        # Command line mode: python insert_missing_call.py <loan_number> <orkuid>
        loan_number = sys.argv[1]
        orkuid = sys.argv[2]
        insert_call_to_loan(loan_number, orkuid)
    else:
        # Interactive mode
        interactive_mode()