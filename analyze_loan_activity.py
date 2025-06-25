#!/usr/bin/env python3
"""
ANALYZE LOAN ACTIVITY - Find loans with 10+ calls
Focus on processor assistant involvement
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

def analyze_loan_activity():
    """Find loans with significant activity (10+ calls)"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("\n📊 ANALYZING LOAN ACTIVITY")
    print("=" * 80)
    
    # Get loans with their call counts
    cursor.execute("""
        SELECT 
            loan_numbers,
            COUNT(*) as total_calls,
            MIN(t.timestamp) as first_call,
            MAX(t.timestamp) as last_call,
            SUM(CASE WHEN t.localParty LIKE '19472421%%' OR t.remoteParty LIKE '19472421%%' THEN 1 ELSE 0 END) as processor_calls
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE loan_numbers != '[]'
        GROUP BY loan_numbers
        HAVING total_calls >= 10
        ORDER BY total_calls DESC
    """)
    
    rows = cursor.fetchall()
    
    print(f"\n🎯 Found {len(rows)} loan groups with 10+ calls")
    
    # Process each loan group
    active_loans = []
    
    for row in rows:
        try:
            loans = json.loads(row['loan_numbers'])
            journey_days = (row['last_call'] - row['first_call']).days
            
            for loan in loans:
                active_loans.append({
                    'loan_number': loan,
                    'total_calls': row['total_calls'],
                    'processor_calls': row['processor_calls'],
                    'journey_days': journey_days,
                    'first_call': row['first_call'],
                    'last_call': row['last_call']
                })
        except:
            pass
    
    # Sort by total calls
    active_loans.sort(key=lambda x: x['total_calls'], reverse=True)
    
    print(f"\n📈 TOP 20 MOST ACTIVE LOANS:")
    print("-" * 100)
    print(f"{'Loan #':<12} {'Total':<8} {'Processor':<10} {'Days':<6} {'First Call':<20} {'Last Call':<20}")
    print("-" * 100)
    
    for loan in active_loans[:20]:
        print(f"{loan['loan_number']:<12} {loan['total_calls']:<8} {loan['processor_calls']:<10} {loan['journey_days']:<6} {loan['first_call'].strftime('%m/%d/%Y %I:%M %p'):<20} {loan['last_call'].strftime('%m/%d/%Y %I:%M %p'):<20}")
    
    # Analyze processor assistant patterns
    print(f"\n🤖 PROCESSOR ASSISTANT ANALYSIS:")
    
    # Get specific processor numbers involved
    cursor.execute("""
        SELECT 
            CASE 
                WHEN t.localParty LIKE '19472421%%' THEN t.localParty
                WHEN t.remoteParty LIKE '19472421%%' THEN t.remoteParty
            END as processor_number,
            COUNT(DISTINCT ct.loan_numbers) as loans_handled,
            COUNT(*) as total_calls
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE (t.localParty LIKE '19472421%%' OR t.remoteParty LIKE '19472421%%')
        AND ct.loan_numbers != '[]'
        GROUP BY processor_number
        HAVING processor_number IS NOT NULL
        ORDER BY total_calls DESC
    """)
    
    processors = cursor.fetchall()
    
    print(f"\nMost Active Processor Assistants:")
    print("-" * 60)
    print(f"{'Number':<15} {'Loans Handled':<15} {'Total Calls':<15}")
    print("-" * 60)
    
    for proc in processors[:10]:
        print(f"{proc['processor_number']:<15} {proc['loans_handled']:<15} {proc['total_calls']:<15}")
    
    # Find loans with highest processor involvement
    print(f"\n📞 LOANS WITH HIGH PROCESSOR INVOLVEMENT:")
    
    high_processor_loans = [l for l in active_loans if l['processor_calls'] >= 5]
    high_processor_loans.sort(key=lambda x: x['processor_calls'], reverse=True)
    
    print("-" * 80)
    print(f"{'Loan #':<12} {'Total':<8} {'Processor':<10} {'% Processor':<12}")
    print("-" * 80)
    
    for loan in high_processor_loans[:15]:
        pct = (loan['processor_calls'] / loan['total_calls']) * 100
        print(f"{loan['loan_number']:<12} {loan['total_calls']:<8} {loan['processor_calls']:<10} {pct:<12.1f}%")
    
    # Time-based analysis
    print(f"\n⏱️  JOURNEY LENGTH ANALYSIS:")
    
    journey_ranges = {
        '0-7 days': 0,
        '8-14 days': 0,
        '15-21 days': 0,
        '22-30 days': 0,
        '30+ days': 0
    }
    
    for loan in active_loans:
        days = loan['journey_days']
        if days <= 7:
            journey_ranges['0-7 days'] += 1
        elif days <= 14:
            journey_ranges['8-14 days'] += 1
        elif days <= 21:
            journey_ranges['15-21 days'] += 1
        elif days <= 30:
            journey_ranges['22-30 days'] += 1
        else:
            journey_ranges['30+ days'] += 1
    
    print("\nLoan Journey Duration Distribution:")
    for range_name, count in journey_ranges.items():
        pct = (count / len(active_loans)) * 100 if active_loans else 0
        bar = '█' * int(pct / 2)
        print(f"{range_name:<12}: {count:>4} loans ({pct:>5.1f}%) {bar}")
    
    cursor.close()
    conn.close()
    
    return active_loans

if __name__ == "__main__":
    print("🔍 LOAN ACTIVITY ANALYZER")
    print("Finding loans with 10+ calls and processor involvement")
    
    active_loans = analyze_loan_activity()
    
    # Save results
    output_file = f"active_loans_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, 'w') as f:
        f.write("ACTIVE LOANS REPORT\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Total Active Loans (10+ calls): {len(active_loans)}\n")
        f.write("=" * 80 + "\n\n")
        
        for loan in active_loans:
            f.write(f"Loan: {loan['loan_number']}\n")
            f.write(f"  Total Calls: {loan['total_calls']}\n")
            f.write(f"  Processor Calls: {loan['processor_calls']}\n")
            f.write(f"  Journey: {loan['journey_days']} days\n")
            f.write(f"  Period: {loan['first_call'].strftime('%m/%d/%Y')} to {loan['last_call'].strftime('%m/%d/%Y')}\n")
            f.write("\n")
    
    print(f"\n📄 Full report saved to: {output_file}")