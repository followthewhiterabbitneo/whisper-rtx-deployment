#!/usr/bin/env python3
"""
Automatically generate loan summary with enhanced features
"""

import pymysql
import json
import os
from datetime import datetime
import sys
import webbrowser

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def extract_key_points(transcript):
    """Extract key points from transcript"""
    key_points = []
    
    # Enhanced key phrases
    key_phrases = [
        "loan", "payment", "approved", "denied", "documentation", 
        "income", "employment", "credit", "rate", "terms",
        "modification", "hardship", "covid", "forbearance",
        "delinquent", "default", "collection", "review", "decision",
        "verify", "confirm", "submit", "receive", "process"
    ]
    
    lines = transcript.split('\n')
    for line in lines:
        line_lower = line.lower()
        if any(phrase in line_lower for phrase in key_phrases):
            # Get surrounding context
            if len(line.strip()) > 20:
                key_points.append(line.strip()[:250])
    
    return key_points[:10]  # Top 10 key points

def analyze_sentiment_progression(transcripts):
    """Analyze how sentiment changes over time"""
    progression = []
    for t in transcripts:
        if t.get('sentiment'):
            progression.append({
                'date': t['timestamp'].strftime('%Y-%m-%d'),
                'sentiment': t['sentiment'],
                'summary': t.get('summary', '')[:100]
            })
    return progression

def identify_turning_points(transcripts):
    """Identify critical turning points in the loan journey"""
    turning_points = []
    
    for i, t in enumerate(transcripts):
        text_lower = t['text'].lower()
        
        # Check for major events
        if 'approved' in text_lower and 'loan' in text_lower:
            turning_points.append({
                'date': t['timestamp'],
                'event': 'Loan Approval',
                'context': extract_context(t['text'], 'approved')
            })
        elif 'denied' in text_lower or 'declined' in text_lower:
            turning_points.append({
                'date': t['timestamp'],
                'event': 'Loan Denial',
                'context': extract_context(t['text'], 'denied')
            })
        elif 'modification' in text_lower and ('approved' in text_lower or 'accept' in text_lower):
            turning_points.append({
                'date': t['timestamp'],
                'event': 'Modification Approved',
                'context': extract_context(t['text'], 'modification')
            })
    
    return turning_points

def extract_context(text, keyword, context_length=100):
    """Extract context around keyword"""
    text_lower = text.lower()
    pos = text_lower.find(keyword.lower())
    if pos == -1:
        return text[:200]
    
    start = max(0, pos - context_length)
    end = min(len(text), pos + len(keyword) + context_length)
    
    context = text[start:end]
    if start > 0:
        context = "..." + context
    if end < len(text):
        context = context + "..."
    
    return context.strip()

def create_enhanced_summary(loan_number):
    """Create an enhanced summary of all loan transcripts"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all transcripts for this loan with enhanced data
    cursor.execute("""
        SELECT 
            ct.orkuid,
            ct.transcript_path,
            ct.summary,
            ct.sentiment,
            ct.key_facts,
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
    
    print(f"\n📊 Creating enhanced summary for loan #{loan_number}")
    print(f"Found {len(recordings)} recordings")
    
    # Collect all transcripts with metadata
    all_transcripts = []
    timeline_events = []
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    
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
            sentiment = rec['sentiment'] or 'neutral'
            sentiment_counts[sentiment] += 1
            
            all_transcripts.append({
                'orkuid': rec['orkuid'],
                'timestamp': rec['timestamp'],
                'duration': rec['duration'],
                'user': rec['user_name'] or 'Unknown',
                'text': transcript_text,
                'summary': rec['summary'],
                'sentiment': sentiment,
                'key_facts': json.loads(rec['key_facts']) if rec['key_facts'] else {},
                'key_points': extract_key_points(transcript_text)
            })
            
            # Create timeline event
            timeline_events.append({
                'date': rec['timestamp'].strftime('%Y-%m-%d %H:%M'),
                'user': rec['user_name'] or 'Unknown',
                'duration': f"{rec['duration']//60}m {rec['duration']%60}s",
                'sentiment': sentiment,
                'summary': rec['summary'] or 'No summary available',
                'key_points': extract_key_points(transcript_text)[:3]
            })
    
    # Analyze data
    sentiment_progression = analyze_sentiment_progression(all_transcripts)
    turning_points = identify_turning_points(all_transcripts)
    
    # Create enhanced summary document
    summary_file = f"loan_{loan_number}_ENHANCED_SUMMARY.html"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Loan #{loan_number} - Enhanced Summary Report</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
            background: #f5f5f5;
            color: #1a1a1a;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            text-align: center;
        }}
        h1 {{ 
            color: #0969da; 
            margin: 0 0 10px 0;
            font-size: 32px;
        }}
        .meta {{ 
            color: #586069; 
            font-size: 16px;
        }}
        .nav {{
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .nav a {{
            padding: 8px 16px;
            background: #f6f8fa;
            color: #0969da;
            text-decoration: none;
            border-radius: 6px;
            border: 1px solid #e1e4e8;
            transition: all 0.2s;
        }}
        .nav a:hover {{
            background: #0969da;
            color: white;
        }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        h2 {{ 
            color: #24292e; 
            margin-top: 0;
            border-bottom: 2px solid #e1e4e8;
            padding-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f6f8fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
            border: 1px solid #e1e4e8;
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            color: #0969da;
        }}
        .stat-label {{
            color: #586069;
            font-size: 14px;
            margin-top: 5px;
        }}
        .timeline {{
            position: relative;
            padding-left: 30px;
        }}
        .timeline::before {{
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #e1e4e8;
        }}
        .event {{
            position: relative;
            margin: 20px 0;
            padding: 20px;
            background: #f6f8fa;
            border-radius: 6px;
            border: 1px solid #e1e4e8;
        }}
        .event::before {{
            content: '';
            position: absolute;
            left: -25px;
            top: 25px;
            width: 12px;
            height: 12px;
            background: #0969da;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 0 0 1px #e1e4e8;
        }}
        .event-date {{ 
            font-weight: bold; 
            color: #0969da; 
            font-size: 16px;
        }}
        .event-user {{ 
            color: #586069; 
            margin: 5px 0;
        }}
        .key-point {{ 
            background: white; 
            padding: 10px 15px; 
            margin: 8px 0; 
            border-radius: 4px;
            font-size: 14px;
            border-left: 3px solid #0969da;
        }}
        .sentiment-chart {{
            display: flex;
            height: 30px;
            border-radius: 6px;
            overflow: hidden;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .sentiment-positive {{ background: #2ea043; }}
        .sentiment-negative {{ background: #cf222e; }}
        .sentiment-neutral {{ background: #6e7781; }}
        .turning-point {{
            background: #fffbdd;
            border: 1px solid #d4a72c;
            padding: 20px;
            border-radius: 6px;
            margin: 15px 0;
        }}
        .turning-point-title {{
            font-weight: bold;
            color: #735c0f;
            margin-bottom: 10px;
        }}
        .summary-box {{
            background: #ddf4ff;
            border: 1px solid #54aeff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .participants-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .participant {{
            background: #f6f8fa;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e1e4e8;
        }}
        .participant-name {{
            font-weight: bold;
            color: #24292e;
        }}
        .participant-stats {{
            color: #586069;
            font-size: 14px;
            margin-top: 5px;
        }}
        .back-link {{
            display: inline-block;
            padding: 10px 20px;
            background: #0969da;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        .back-link:hover {{ background: #0860ca; }}
        @media print {{
            .nav {{ display: none; }}
            .back-link {{ display: none; }}
        }}
    </style>
</head>
<body>
    <a href="enhanced_loan_viewer.html" class="back-link">← Back to Timeline Viewer</a>
    
    <div class="header">
        <h1>Loan #{loan_number}</h1>
        <div class="meta">
            Enhanced Summary Report | Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
    </div>
    
    <div class="nav">
        <a href="#overview">Overview</a>
        <a href="#sentiment">Sentiment Analysis</a>
        <a href="#timeline">Timeline</a>
        <a href="#turning-points">Turning Points</a>
        <a href="#participants">Participants</a>
        <a href="javascript:window.print()">🖨️ Print Report</a>
    </div>
    
    <div class="section" id="overview">
        <h2>📊 Executive Overview</h2>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(recordings)}</div>
                <div class="stat-label">Total Calls</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(r['duration'] for r in recordings)//60}</div>
                <div class="stat-label">Total Minutes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{(recordings[-1]['timestamp'] - recordings[0]['timestamp']).days}</div>
                <div class="stat-label">Days Active</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(set(t['user'] for t in all_transcripts))}</div>
                <div class="stat-label">Unique Participants</div>
            </div>
        </div>
        
        <div class="summary-box">
            <h3>Case Summary</h3>
            <p>This loan has been actively managed through {len(recordings)} calls spanning {(recordings[-1]['timestamp'] - recordings[0]['timestamp']).days} days, 
            from {recordings[0]['timestamp'].strftime('%B %d, %Y')} to {recordings[-1]['timestamp'].strftime('%B %d, %Y')}.</p>
            
            <p>The case involves {len(set(t['user'] for t in all_transcripts))} different participants and has accumulated 
            {sum(r['duration'] for r in recordings)//60} minutes of documented communication.</p>
        </div>
    </div>
    
    <div class="section" id="sentiment">
        <h2>😊 Sentiment Analysis</h2>
        
        <p>Overall sentiment distribution across all calls:</p>
        
        <div class="sentiment-chart">
            <div class="sentiment-positive" style="width: {sentiment_counts['positive'] / len(recordings) * 100}%"></div>
            <div class="sentiment-neutral" style="width: {sentiment_counts['neutral'] / len(recordings) * 100}%"></div>
            <div class="sentiment-negative" style="width: {sentiment_counts['negative'] / len(recordings) * 100}%"></div>
        </div>
        
        <div style="display: flex; justify-content: space-around; margin-top: 10px;">
            <span>✅ Positive: {sentiment_counts['positive']} calls ({sentiment_counts['positive'] / len(recordings) * 100:.0f}%)</span>
            <span>➖ Neutral: {sentiment_counts['neutral']} calls ({sentiment_counts['neutral'] / len(recordings) * 100:.0f}%)</span>
            <span>❌ Negative: {sentiment_counts['negative']} calls ({sentiment_counts['negative'] / len(recordings) * 100:.0f}%)</span>
        </div>
        
        {"<p style='margin-top: 20px; color: #2ea043; font-weight: bold;'>✅ Overall sentiment is predominantly positive, indicating successful resolution or progress.</p>" if sentiment_counts['positive'] > sentiment_counts['negative'] else ""}
        {"<p style='margin-top: 20px; color: #cf222e; font-weight: bold;'>⚠️ Multiple negative interactions detected. This case may require additional attention.</p>" if sentiment_counts['negative'] > sentiment_counts['positive'] else ""}
    </div>
""")
        
        # Add turning points section if any found
        if turning_points:
            f.write("""
    <div class="section" id="turning-points">
        <h2>🎯 Key Turning Points</h2>
""")
            for tp in turning_points:
                f.write(f"""
        <div class="turning-point">
            <div class="turning-point-title">{tp['event']} - {tp['date'].strftime('%B %d, %Y')}</div>
            <div>{tp['context']}</div>
        </div>
""")
            f.write("    </div>\n")
        
        # Add timeline section
        f.write("""
    <div class="section" id="timeline">
        <h2>📅 Detailed Timeline</h2>
        <div class="timeline">
""")
        
        for event in timeline_events:
            sentiment_emoji = {'positive': '😊', 'negative': '😟', 'neutral': '😐'}.get(event['sentiment'], '😐')
            f.write(f"""
            <div class="event">
                <div class="event-date">{event['date']} {sentiment_emoji}</div>
                <div class="event-user">{event['user']} • {event['duration']}</div>
                <div style="margin-top: 10px; color: #586069;">{event['summary']}</div>
""")
            for point in event['key_points']:
                if point:
                    f.write(f'                <div class="key-point">{point[:200]}...</div>\n')
            f.write("            </div>\n")
        
        f.write("""        </div>
    </div>
    
    <div class="section" id="participants">
        <h2>👥 Participants</h2>
        <div class="participants-list">
""")
        
        # Get unique participants with stats
        participants = {}
        for t in all_transcripts:
            user = t['user']
            if user not in participants:
                participants[user] = {
                    'calls': 0,
                    'duration': 0,
                    'sentiments': []
                }
            participants[user]['calls'] += 1
            participants[user]['duration'] += t['duration']
            participants[user]['sentiments'].append(t['sentiment'])
        
        for user, stats in sorted(participants.items(), key=lambda x: x[1]['calls'], reverse=True):
            dominant_sentiment = max(set(stats['sentiments']), key=stats['sentiments'].count)
            f.write(f"""
            <div class="participant">
                <div class="participant-name">{user}</div>
                <div class="participant-stats">
                    {stats['calls']} calls • {stats['duration']//60} minutes • 
                    Mostly {dominant_sentiment}
                </div>
            </div>
""")
        
        f.write("""        </div>
    </div>
    
    <div style="text-align: center; margin-top: 40px; padding: 20px; color: #586069;">
        <p>End of Report</p>
        <p>Generated by Enhanced Loan Summary System</p>
        <p><a href="open_loan_""" + loan_number + """_transcripts.bat">Open All Transcripts</a> | 
           <a href="enhanced_loan_viewer.html">Back to Viewer</a></p>
    </div>
</body>
</html>
""")
    
    cursor.close()
    conn.close()
    
    print(f"\n✅ Created enhanced summary: {summary_file}")
    print(f"📂 Opening in browser...")
    
    # Try to open in browser
    try:
        webbrowser.open(summary_file)
    except:
        print(f"⚠️  Could not auto-open browser. Please open: {summary_file}")
    
    return summary_file

if __name__ == "__main__":
    if len(sys.argv) > 1:
        loan_number = sys.argv[1]
    else:
        loan_number = input("Enter loan number (default 1225290972): ") or "1225290972"
    
    create_enhanced_summary(loan_number)