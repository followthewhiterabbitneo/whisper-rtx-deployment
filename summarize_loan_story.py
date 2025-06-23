#!/usr/bin/env python3
"""
Summarize all transcripts for a loan into a coherent story
"""

import pymysql
import json
import os
from datetime import datetime
from transformers import pipeline

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def load_gemma_summarizer():
    """Load Gemma model for summarization"""
    try:
        print("Loading Gemma model for summarization...")
        # Try to use local Gemma model if available
        model_path = "models/gemma-3-12b-it-qat-q4_0/gemma-3-12b-it-qat-q4_0.gguf"
        if os.path.exists(model_path):
            print("Using local Gemma model")
            # Would need llama.cpp integration here
            return None
        else:
            # Fallback to simple extraction
            print("Using simple summarization")
            return None
    except:
        return None

def extract_key_points(transcript):
    """Extract key points from transcript"""
    key_points = []
    
    # Look for key phrases
    key_phrases = [
        "loan", "payment", "approved", "denied", "documentation", 
        "income", "employment", "credit", "rate", "terms",
        "modification", "hardship", "covid", "forbearance"
    ]
    
    lines = transcript.split('\n')
    for line in lines:
        line_lower = line.lower()
        if any(phrase in line_lower for phrase in key_phrases):
            # Get surrounding context
            if len(line.strip()) > 20:
                key_points.append(line.strip()[:200])
    
    return key_points[:5]  # Top 5 key points

def create_loan_summary(loan_number):
    """Create a comprehensive summary of all loan transcripts"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all transcripts for this loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            ct.transcript_path,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            l.user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN loan_number_index l ON ct.orkuid = l.orkuid AND l.loan_number = %s
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (loan_number, f'%{loan_number}%'))
    
    recordings = cursor.fetchall()
    
    print(f"\nCreating summary for loan #{loan_number}")
    print(f"Found {len(recordings)} recordings")
    
    # Collect all transcripts
    all_transcripts = []
    timeline_events = []
    
    for rec in recordings:
        transcript_text = ""
        
        # Read transcript
        if rec['transcript_path'] and os.path.exists(rec['transcript_path']):
            with open(rec['transcript_path'], 'r', encoding='utf-8') as f:
                transcript_text = f.read()
        elif rec['transcript_path']:
            # Try Windows path
            win_path = rec['transcript_path'].replace('/', '\\')
            if os.path.exists(win_path):
                with open(win_path, 'r', encoding='utf-8') as f:
                    transcript_text = f.read()
        
        if transcript_text:
            all_transcripts.append({
                'orkuid': rec['orkuid'],
                'timestamp': rec['timestamp'],
                'duration': rec['duration'],
                'user': rec['user_name'] or 'Unknown',
                'text': transcript_text,
                'key_points': extract_key_points(transcript_text)
            })
            
            # Create timeline event
            timeline_events.append({
                'date': rec['timestamp'].strftime('%Y-%m-%d %H:%M'),
                'user': rec['user_name'] or 'Unknown',
                'duration': f"{rec['duration']//60}m {rec['duration']%60}s",
                'key_points': extract_key_points(transcript_text)[:2]
            })
    
    # Create summary document
    summary_file = f"loan_{loan_number}_SUMMARY.html"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Loan #{loan_number} - Complete Summary</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 1000px; 
            margin: 0 auto; 
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        h1 {{ color: #333; margin: 0; }}
        .meta {{ color: #666; margin-top: 10px; }}
        .timeline {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .event {{
            border-left: 3px solid #007bff;
            padding-left: 15px;
            margin: 15px 0;
        }}
        .event-date {{ font-weight: bold; color: #007bff; }}
        .event-user {{ color: #666; }}
        .key-point {{ 
            background: #f8f9fa; 
            padding: 5px 10px; 
            margin: 5px 0; 
            border-radius: 4px;
            font-size: 14px;
        }}
        .summary-box {{
            background: #e8f4fd;
            border: 1px solid #007bff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .back-link {{
            display: inline-block;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        .back-link:hover {{ background: #0056b3; }}
    </style>
</head>
<body>
    <a href="view_loan_now.html" class="back-link">← Back to Timeline</a>
    
    <div class="header">
        <h1>Loan #{loan_number} - Complete Summary</h1>
        <div class="meta">
            Total Calls: {len(recordings)} | 
            Date Range: {recordings[0]['timestamp'].strftime('%b %d')} - {recordings[-1]['timestamp'].strftime('%b %d, %Y')} |
            Total Duration: {sum(r['duration'] for r in recordings)//60} minutes
        </div>
    </div>
    
    <div class="summary-box">
        <h2>📊 Executive Summary</h2>
        <p>This loan was discussed across {len(recordings)} calls over a {(recordings[-1]['timestamp'] - recordings[0]['timestamp']).days} day period.</p>
        
        <h3>Key Participants:</h3>
        <ul>
""")
        
        # Get unique participants
        participants = {}
        for t in all_transcripts:
            user = t['user']
            if user not in participants:
                participants[user] = 0
            participants[user] += 1
        
        for user, count in sorted(participants.items(), key=lambda x: x[1], reverse=True):
            f.write(f"            <li>{user} - {count} calls</li>\n")
        
        f.write("""        </ul>
        
        <h3>Key Topics Discussed:</h3>
        <ul>
""")
        
        # Extract common themes
        all_text = ' '.join([t['text'].lower() for t in all_transcripts])
        themes = {
            'Loan Application': all_text.count('application'),
            'Payment Issues': all_text.count('payment'),
            'Documentation': all_text.count('document'),
            'Employment/Income': all_text.count('employment') + all_text.count('income'),
            'Modification Request': all_text.count('modif'),
            'COVID/Hardship': all_text.count('covid') + all_text.count('hardship')
        }
        
        for theme, count in sorted(themes.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                f.write(f"            <li>{theme} (mentioned {count} times)</li>\n")
        
        f.write("""        </ul>
    </div>
    
    <div class="timeline">
        <h2>📅 Chronological Timeline</h2>
""")
        
        # Add timeline events
        for event in timeline_events:
            f.write(f"""
        <div class="event">
            <div class="event-date">{event['date']}</div>
            <div class="event-user">{event['user']} ({event['duration']})</div>
""")
            for point in event['key_points']:
                if point:
                    f.write(f'            <div class="key-point">{point[:150]}...</div>\n')
            f.write("        </div>\n")
        
        f.write("""    </div>
    
    <div style="text-align: center; margin-top: 40px; color: #666;">
        <p>Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        <p><a href="open_loan_""" + loan_number + """_transcripts.bat">Open All Transcripts</a></p>
    </div>
</body>
</html>
""")
    
    cursor.close()
    conn.close()
    
    print(f"\n✓ Created summary: {summary_file}")
    print(f"✓ Open this file in your browser to see the complete loan story!")
    
    # Also update the view_loan_now.html to include summary link
    update_main_viewer(loan_number, summary_file)

def update_main_viewer(loan_number, summary_file):
    """Add summary link to main viewer"""
    viewer_file = "view_loan_now.html"
    if os.path.exists(viewer_file):
        with open(viewer_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add link after search box if not already there
        if 'loan_.*_SUMMARY.html' not in content:
            search_box_end = content.find('</div>', content.find('class="search-box"'))
            if search_box_end > 0:
                insert_point = search_box_end + 6
                summary_link = f'''
        
        <div style="text-align: center; margin: 20px 0;">
            <a href="{summary_file}" style="display: inline-block; padding: 10px 30px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; font-size: 16px;">
                📊 View Complete Summary for Loan #{loan_number}
            </a>
        </div>'''
                
                new_content = content[:insert_point] + summary_link + content[insert_point:]
                
                with open(viewer_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✓ Added summary link to {viewer_file}")

if __name__ == "__main__":
    loan = input("Enter loan number (default 1225290972): ") or "1225290972"
    create_loan_summary(loan)