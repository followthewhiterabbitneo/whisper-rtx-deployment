#!/usr/bin/env python3
"""
GENERATE LOAN BRIEF - Comprehensive loan summary with all critical information
Tracks conditions, dates, sentiment, and creates daily timeline
"""

import pymysql
import json
from datetime import datetime, timedelta
import re
from collections import defaultdict

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def extract_conditions(text):
    """Extract conditions, deliverables, and dates from text"""
    conditions = []
    
    # Look for conditions patterns
    condition_patterns = [
        r'condition[s]?\s*[:]\s*([^\n]+)',
        r'clearing\s+condition[s]?',
        r'CR\s*[-:]?\s*([^\n]+)',  # Client Request
        r'client\s+request[s]?\s*[:]\s*([^\n]+)',
        r'deliverable[s]?\s*[:]\s*([^\n]+)',
        r'need[s]?\s*[:]\s*([^\n]+)',
        r'require[s]?\s*[:]\s*([^\n]+)',
        r'missing\s*[:]\s*([^\n]+)'
    ]
    
    for pattern in condition_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        conditions.extend(matches)
    
    return conditions

def extract_dates(text):
    """Extract important dates (CTC, submission, etc.)"""
    dates = {}
    
    # Date patterns
    date_patterns = [
        (r'CTC\s*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'CTC'),
        (r'clear\s+to\s+close\s*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'CTC'),
        (r'submission\s*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'Submission'),
        (r'closing\s*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'Closing'),
        (r'due\s*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'Due'),
    ]
    
    for pattern, date_type in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            dates[date_type] = matches[0]
    
    return dates

def detect_sentiment(text):
    """Detect sentiment, especially angry/frustrated"""
    angry_keywords = [
        'angry', 'frustrated', 'upset', 'mad', 'furious', 'annoyed',
        'unacceptable', 'ridiculous', 'terrible', 'horrible',
        'escalate', 'complaint', 'disappointed'
    ]
    
    positive_keywords = [
        'approved', 'cleared', 'good', 'excellent', 'great',
        'thank you', 'appreciate', 'perfect', 'wonderful'
    ]
    
    text_lower = text.lower() if text else ""
    
    angry_count = sum(1 for word in angry_keywords if word in text_lower)
    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    
    if angry_count > positive_count:
        return "NEGATIVE/ANGRY"
    elif positive_count > angry_count:
        return "POSITIVE"
    else:
        return "NEUTRAL"

def extract_names_and_roles(text, local_party, remote_party):
    """Extract broker names, LO info, and other names"""
    names = {
        'brokers': [],
        'loan_officers': [],
        'processors': [],
        'underwriters': [],
        'other': []
    }
    
    # Common patterns
    name_patterns = [
        (r'broker\s*[:]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', 'brokers'),
        (r'LO\s*[:]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', 'loan_officers'),
        (r'loan\s+officer\s*[:]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', 'loan_officers'),
        (r'processor\s*[:]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', 'processors'),
        (r'underwriter\s*[:]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', 'underwriters'),
    ]
    
    if text:
        for pattern, role in name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            names[role].extend(matches)
    
    return names

def generate_loan_brief(loan_number):
    """Generate comprehensive loan brief"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print(f"\n📄 GENERATING LOAN BRIEF FOR {loan_number}")
    print("=" * 80)
    
    # Get ALL calls for this loan (no date limit)
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            ct.transcript_text,
            ct.summary,
            ct.sentiment,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name,
            CASE 
                WHEN t.localParty LIKE '19472421%%' OR t.remoteParty LIKE '19472421%%' 
                THEN 'PROCESSOR'
                ELSE 'STANDARD'
            END as call_type
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp, t.orkUid
    """, (f'%{loan_number}%',))
    
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not calls:
        print(f"No calls found for loan {loan_number}")
        return
    
    # Group calls by day and exact timestamp
    calls_by_day = defaultdict(lambda: defaultdict(list))
    
    for call in calls:
        # Fix timezone - convert to local time
        local_time = call['timestamp']  # Assuming this needs timezone conversion
        day_key = local_time.strftime('%Y-%m-%d')
        time_key = local_time.strftime('%Y-%m-%d %H:%M:%S')
        calls_by_day[day_key][time_key].append(call)
    
    # Collect all data
    all_conditions = []
    all_dates = {}
    all_names = defaultdict(set)
    sentiment_counts = defaultdict(int)
    
    # Generate brief
    output_file = f"LOAN_BRIEF_{loan_number}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 100 + "\n")
        f.write(f"LOAN BRIEF - {loan_number}\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Total Calls: {len(calls)}\n")
        
        first_call = calls[0]['timestamp']
        last_call = calls[-1]['timestamp']
        journey_days = (last_call - first_call).days
        
        f.write(f"Journey: {first_call.strftime('%m/%d/%Y')} to {last_call.strftime('%m/%d/%Y')} ({journey_days} days)\n")
        f.write("=" * 100 + "\n\n")
        
        # Process each day
        for day in sorted(calls_by_day.keys()):
            f.write("\n" + "="*80 + "\n")
            f.write(f"📅 DATE: {datetime.strptime(day, '%Y-%m-%d').strftime('%A, %B %d, %Y')}\n")
            f.write("="*80 + "\n\n")
            
            day_calls = calls_by_day[day]
            
            # Process each conversation group (same timestamp)
            for time_key in sorted(day_calls.keys()):
                conversation = day_calls[time_key]
                
                # If multiple calls at exact same time, it's one conversation
                if len(conversation) > 1:
                    f.write(f"\n🔄 MULTI-PART CONVERSATION ({len(conversation)} parts)\n")
                
                for idx, call in enumerate(conversation):
                    # Format time in local timezone
                    time_str = call['timestamp'].strftime('%I:%M %p')
                    
                    f.write(f"\n⏰ {time_str} - Call {call['orkuid']}\n")
                    f.write(f"   Duration: {call['duration']}s ({call['duration']/60:.1f} min)\n")
                    f.write(f"   {call['localParty']} → {call['remoteParty']}\n")
                    f.write(f"   User: {call['user_name']}\n")
                    
                    if call['call_type'] == 'PROCESSOR':
                        f.write(f"   🤖 PROCESSOR ASSISTANT CALL\n")
                    
                    # Extract information from transcript/summary
                    text_to_analyze = (call.get('summary', '') or '') + ' ' + (call.get('transcript_text', '') or '')
                    
                    # Conditions
                    conditions = extract_conditions(text_to_analyze)
                    if conditions:
                        f.write(f"\n   ⚠️ CONDITIONS/REQUIREMENTS:\n")
                        for condition in conditions:
                            f.write(f"      • {condition}\n")
                            all_conditions.append(condition)
                    
                    # Dates
                    dates = extract_dates(text_to_analyze)
                    if dates:
                        f.write(f"\n   📅 IMPORTANT DATES:\n")
                        for date_type, date_value in dates.items():
                            f.write(f"      • {date_type}: {date_value}\n")
                            all_dates[date_type] = date_value
                    
                    # Names and roles
                    names = extract_names_and_roles(text_to_analyze, call['localParty'], call['remoteParty'])
                    for role, name_list in names.items():
                        if name_list:
                            for name in name_list:
                                all_names[role].add(name)
                                f.write(f"   👤 {role.title()}: {name}\n")
                    
                    # Sentiment
                    sentiment = call.get('sentiment') or detect_sentiment(text_to_analyze)
                    if sentiment and sentiment != "NEUTRAL":
                        f.write(f"   💭 Sentiment: {sentiment}\n")
                        sentiment_counts[sentiment] += 1
                    
                    # Summary
                    if call.get('summary'):
                        f.write(f"\n   📝 Summary: {call['summary']}\n")
                    
                    f.write(f"\n   📂 Transcript: {call.get('transcript_path', 'N/A')}\n")
                    f.write("-" * 60 + "\n")
        
        # Executive Summary Section
        f.write("\n\n" + "="*100 + "\n")
        f.write("EXECUTIVE SUMMARY\n")
        f.write("="*100 + "\n\n")
        
        # Key People
        f.write("👥 KEY PEOPLE INVOLVED:\n")
        for role, names in all_names.items():
            if names:
                f.write(f"   {role.title()}: {', '.join(sorted(names))}\n")
        
        # Critical Dates
        if all_dates:
            f.write("\n📅 CRITICAL DATES:\n")
            for date_type, date_value in all_dates.items():
                f.write(f"   {date_type}: {date_value}\n")
        
        # All Conditions
        if all_conditions:
            f.write("\n⚠️ ALL CONDITIONS TO CLEAR:\n")
            unique_conditions = list(set(all_conditions))
            for idx, condition in enumerate(unique_conditions, 1):
                f.write(f"   {idx}. {condition}\n")
        
        # Sentiment Summary
        if sentiment_counts:
            f.write("\n💭 SENTIMENT ANALYSIS:\n")
            total_calls_with_sentiment = sum(sentiment_counts.values())
            for sentiment, count in sentiment_counts.items():
                pct = (count / total_calls_with_sentiment) * 100
                f.write(f"   {sentiment}: {count} calls ({pct:.1f}%)\n")
        
        # Call Pattern Analysis
        f.write("\n📊 CALL PATTERNS:\n")
        
        # Most active parties
        party_counts = defaultdict(int)
        for call in calls:
            party_counts[call['localParty']] += 1
            party_counts[call['remoteParty']] += 1
        
        top_parties = sorted(party_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        f.write("   Most Active Numbers:\n")
        for party, count in top_parties:
            party_type = ""
            if party.startswith('19472421'):
                party_type = " (Processor)"
            f.write(f"      {party}{party_type}: {count} calls\n")
        
        # Processor involvement
        processor_calls = sum(1 for c in calls if c['call_type'] == 'PROCESSOR')
        if processor_calls:
            f.write(f"\n   Processor Assistant Involvement: {processor_calls} calls ({processor_calls/len(calls)*100:.1f}%)\n")
        
        f.write("\n" + "="*100 + "\n")
        f.write("END OF LOAN BRIEF\n")
        f.write("="*100 + "\n")
    
    print(f"\n✅ Loan brief saved to: {output_file}")
    print(f"📄 File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    
    return output_file

if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) > 1:
        loan_number = sys.argv[1]
    else:
        loan_number = input("Enter loan number: ").strip()
    
    generate_loan_brief(loan_number)