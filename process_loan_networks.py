#!/usr/bin/env python3
"""
Process all recordings in loan officer networks
Including short calls that were previously skipped
"""

import json
import sys
import time
from fast_loan_extractor import FastLoanExtractor
from smart_loan_network_finder import find_loan_officer_networks

def process_network_recordings():
    """Process all recordings found through loan officer network analysis"""
    
    print("="*80)
    print("LOAN NETWORK PROCESSOR")
    print("Processing ALL calls from loan officers (any duration)")
    print("="*80)
    
    # Find loan officer networks
    print("\nAnalyzing loan officer networks...")
    officers, recordings = find_loan_officer_networks()
    
    if not recordings:
        print("\nNo recordings to process!")
        return
    
    print(f"\n{'='*80}")
    print(f"Ready to process {len(recordings)} recordings")
    print(f"Including short calls (<90s) that contain important updates")
    print(f"{'='*80}")
    
    # Group by loan officer
    by_officer = {}
    for rec in recordings:
        officer = rec['loan_officer']
        if officer not in by_officer:
            by_officer[officer] = []
        by_officer[officer].append(rec)
    
    print("\nBreakdown by loan officer:")
    for officer, recs in by_officer.items():
        print(f"  {officer}: {len(recs)} calls")
    
    response = input(f"\nProcess all {len(recordings)} recordings? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Process with loan extractor
    extractor = FastLoanExtractor()
    
    processed = 0
    failed = 0
    loans_found = 0
    short_calls_with_loans = 0
    
    start_time = time.time()
    
    try:
        for i, rec in enumerate(recordings, 1):
            # Add required fields for processor
            rec['orkUid'] = rec['orkuid']
            rec['target_user'] = f"{rec.get('user_firstname', '')} {rec.get('user_lastname', '')}".strip() or 'Unknown'
            
            print(f"\n[{i}/{len(recordings)}] {rec['target_user']} - {rec['orkuid']}")
            print(f"  Duration: {rec['duration']}s, Officer: {rec['loan_officer']}")
            
            success = extractor.process_recording(rec)
            
            if success:
                processed += 1
                
                # Check if loans were found
                conn = extractor.db_conn
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT loan_numbers FROM call_transcripts_v2 
                    WHERE orkuid = %s
                """, (rec['orkuid'],))
                result = cursor.fetchone()
                
                if result and result[0] != '[]':
                    loans = json.loads(result[0])
                    loans_found += 1
                    print(f"  ✓ Found loans: {loans}")
                    
                    if rec['duration'] < 90:
                        short_calls_with_loans += 1
                else:
                    print(f"  ✓ Processed (no loans)")
            else:
                failed += 1
                print(f"  ✗ Failed")
            
            # Progress
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / (elapsed / 3600)
                remaining = (len(recordings) - i) / rate if rate > 0 else 0
                
                print(f"\nProgress: {i}/{len(recordings)} ({i/len(recordings)*100:.1f}%)")
                print(f"Loans found: {loans_found} ({short_calls_with_loans} in calls <90s)")
                print(f"Rate: {rate:.1f}/hour, ETA: {remaining:.1f} hours")
    
    finally:
        extractor.cleanup()
    
    # Summary
    total_time = time.time() - start_time
    print(f"\n{'='*80}")
    print("NETWORK PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"Processed: {processed}")
    print(f"Failed: {failed}")
    print(f"Total with loans: {loans_found}")
    print(f"Short calls (<90s) with loans: {short_calls_with_loans}")
    print(f"Time: {total_time/60:.1f} minutes")
    print(f"Speed: {len(recordings) / (total_time / 3600):.1f} recordings/hour")
    
    print("\n✓ Loan officer networks fully mapped!")
    print("✓ Ready for comprehensive timeline generation!")

def generate_enhanced_timeline(loan_number):
    """Generate timeline with full context from loan officer networks"""
    
    from smart_loan_network_finder import create_comprehensive_timeline
    
    print(f"\nGenerating enhanced timeline for loan #{loan_number}...")
    
    calls = create_comprehensive_timeline(loan_number)
    
    # Group by date
    by_date = {}
    for call in calls:
        date = call['timestamp'].date()
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(call)
    
    print(f"\n{'='*60}")
    print(f"ENHANCED TIMELINE - LOAN #{loan_number}")
    print(f"{'='*60}")
    
    for date in sorted(by_date.keys()):
        print(f"\n{date}")
        print("-" * 40)
        
        for call in by_date[date]:
            time_str = call['timestamp'].strftime("%H:%M")
            duration = call['duration'] / 60
            status = "📝" if call['transcript_path'] else "⚪"
            loans = json.loads(call['loan_numbers']) if call['loan_numbers'] else []
            loan_mark = "💰" if loan_number in [str(l) for l in loans] else ""
            
            print(f"{status} {time_str} ({duration:.1f}m) {loan_mark}")
            print(f"   {call['localParty']} ↔ {call['remoteParty']}")
            
            if loans:
                print(f"   Loans discussed: {loans}")

if __name__ == "__main__":
    process_network_recordings()