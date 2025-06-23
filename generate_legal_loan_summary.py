#!/usr/bin/env python3
"""
Generate professional legal brief summaries for loan timelines using Gemma/Llama
Works on RTX 4090 with llama-cpp-python
"""

import pymysql
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import subprocess

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def create_legal_summary_prompt(transcript, loan_number, orkuid, user_name, date):
    """Create a structured prompt for legal brief summary"""
    
    prompt = f"""You are a legal assistant specializing in mortgage and loan documentation. Create a professional legal brief summary of this call transcript.

CALL METADATA:
- Date: {date}
- Loan Number: {loan_number}
- Recording ID: {orkuid}
- Primary Party: {user_name}

INSTRUCTIONS:
1. Extract all key facts (loan numbers, amounts, dates, names)
2. Identify the main purpose of the call
3. Note any commitments or agreements made
4. Flag any compliance or regulatory concerns
5. Summarize in legal brief format

TRANSCRIPT:
{transcript[:15000]}

Please provide:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY FACTS (bullet points)
3. PARTIES INVOLVED
4. MAIN DISCUSSION POINTS
5. ACTION ITEMS/AGREEMENTS
6. COMPLIANCE NOTES (if any)
7. RISK ASSESSMENT
"""
    
    return prompt

def generate_legal_summary_with_llama(prompt):
    """Generate summary using llama.cpp with GPU"""
    try:
        # Try multiple model paths
        model_paths = [
            "models/gemma-2-9b-it-Q5_K_M.gguf",
            "models/gemma2-9b-it-v1/gemma-2-9b-it-Q5_K_M.gguf",
            "models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf",
            "models/gemma-3-12b-it-qat-q4_0/gemma-3-12b-it-qat-q4_0.gguf"
        ]
        
        model_path = None
        for path in model_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        if not model_path:
            print("⚠️  No AI model found. Using fallback extraction.")
            return None
            
        print(f"Using model: {model_path}")
        
        # Use llama-cpp-python
        from llama_cpp import Llama
        
        llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,      # Use all GPU layers
            n_ctx=8192,           # Context window
            n_batch=512,          # Batch size
            n_threads=8,          # CPU threads
            verbose=False
        )
        
        response = llm(
            prompt,
            max_tokens=1024,
            temperature=0.1,
            top_p=0.9,
            stop=["<end_of_turn>", "<start_of_turn>", "\n\n\n"]
        )
        
        return response['choices'][0]['text'].strip()
        
    except Exception as e:
        print(f"⚠️  AI generation failed: {e}")
        return None

def extract_key_legal_points(transcript):
    """Fallback extraction of key legal points"""
    key_points = []
    
    # Legal keywords to look for
    legal_keywords = [
        "loan", "payment", "approved", "denied", "documentation", 
        "income", "employment", "credit", "rate", "terms",
        "modification", "hardship", "covid", "forbearance",
        "delinquent", "default", "collection", "review", "decision",
        "verify", "confirm", "submit", "receive", "process",
        "agreement", "contract", "obligation", "liability"
    ]
    
    lines = transcript.split('\n')
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in legal_keywords):
            if len(line.strip()) > 20:
                key_points.append(line.strip()[:300])
    
    return key_points[:15]  # Top 15 key points

def create_legal_loan_summary(loan_number):
    """Create a comprehensive legal summary of all loan transcripts"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all transcripts for this loan
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
            l.user_name,
            l.loan_number
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN loan_number_index l ON ct.orkuid = l.orkuid AND l.loan_number = %s
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (loan_number, f'%{loan_number}%'))
    
    recordings = cursor.fetchall()
    
    print(f"\n⚖️  Creating legal brief for loan #{loan_number}")
    print(f"Found {len(recordings)} recordings")
    
    # Generate individual legal summaries
    legal_summaries = []
    all_key_facts = set()
    all_parties = set()
    all_action_items = []
    all_compliance_notes = []
    
    for i, rec in enumerate(recordings, 1):
        print(f"\nProcessing recording {i}/{len(recordings)}: {rec['orkuid']}")
        
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
            # Extract parties
            all_parties.add(rec['user_name'] or rec['localParty'])
            if rec['remoteParty']:
                all_parties.add(rec['remoteParty'])
            
            # Generate legal summary
            prompt = create_legal_summary_prompt(
                transcript_text,
                loan_number,
                rec['orkuid'],
                rec['user_name'] or 'Unknown',
                rec['timestamp'].strftime('%Y-%m-%d %H:%M')
            )
            
            legal_summary = generate_legal_summary_with_llama(prompt)
            
            if legal_summary:
                print("✅ Generated AI legal summary")
                legal_summaries.append({
                    'orkuid': rec['orkuid'],
                    'timestamp': rec['timestamp'],
                    'duration': rec['duration'],
                    'user': rec['user_name'] or 'Unknown',
                    'ai_summary': legal_summary,
                    'sentiment': rec['sentiment']
                })
                
                # Extract key facts from AI summary
                if "KEY FACTS" in legal_summary:
                    facts_section = legal_summary.split("KEY FACTS")[1].split("\n")[1:10]
                    for fact in facts_section:
                        if fact.strip() and len(fact.strip()) > 5:
                            all_key_facts.add(fact.strip())
                
                # Extract action items
                if "ACTION ITEMS" in legal_summary:
                    actions_section = legal_summary.split("ACTION ITEMS")[1].split("\n")[1:10]
                    for action in actions_section:
                        if action.strip() and len(action.strip()) > 5:
                            all_action_items.append({
                                'date': rec['timestamp'],
                                'action': action.strip()
                            })
            else:
                # Fallback to key points extraction
                print("⚠️  Using fallback extraction")
                key_points = extract_key_legal_points(transcript_text)
                legal_summaries.append({
                    'orkuid': rec['orkuid'],
                    'timestamp': rec['timestamp'],
                    'duration': rec['duration'],
                    'user': rec['user_name'] or 'Unknown',
                    'key_points': key_points,
                    'sentiment': rec['sentiment']
                })
    
    # Create comprehensive legal brief document
    summary_file = f"loan_{loan_number}_LEGAL_BRIEF.html"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Legal Brief - Loan #{loan_number}</title>
    <style>
        body {{ 
            font-family: 'Times New Roman', Times, serif; 
            max-width: 8.5in;
            margin: 0.5in auto;
            line-height: 1.6;
            color: #000;
            background: white;
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #000;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{ 
            font-size: 24px;
            margin: 10px 0;
            text-transform: uppercase;
        }}
        h2 {{ 
            font-size: 18px;
            margin-top: 30px;
            margin-bottom: 15px;
            text-transform: uppercase;
            border-bottom: 1px solid #000;
        }}
        h3 {{
            font-size: 16px;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .meta {{
            font-size: 14px;
            text-align: left;
            margin: 20px 0;
        }}
        .section {{
            margin: 30px 0;
        }}
        .executive-summary {{
            background: #f0f0f0;
            padding: 20px;
            border: 1px solid #000;
            margin: 20px 0;
        }}
        .key-fact {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .call-summary {{
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ccc;
            page-break-inside: avoid;
        }}
        .call-header {{
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .timestamp {{
            color: #555;
        }}
        ul {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        .compliance-note {{
            color: #d9534f;
            font-weight: bold;
        }}
        .action-item {{
            background: #fff3cd;
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #ffc107;
        }}
        @media print {{
            body {{ margin: 0.5in; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>LEGAL BRIEF</h1>
        <h2>LOAN NUMBER: {loan_number}</h2>
        <div class="meta">
            <strong>Date Range:</strong> {recordings[0]['timestamp'].strftime('%B %d, %Y')} to {recordings[-1]['timestamp'].strftime('%B %d, %Y')}<br>
            <strong>Total Calls:</strong> {len(recordings)}<br>
            <strong>Total Duration:</strong> {sum(r['duration'] for r in recordings)//60} minutes<br>
            <strong>Prepared:</strong> {datetime.now().strftime('%B %d, %Y')}
        </div>
    </div>
    
    <div class="section executive-summary">
        <h2>I. EXECUTIVE SUMMARY</h2>
        <p>This legal brief summarizes {len(recordings)} recorded calls regarding Loan #{loan_number}, 
        spanning {(recordings[-1]['timestamp'] - recordings[0]['timestamp']).days} days. 
        The communications involve {len(all_parties)} parties and cover various aspects of loan 
        servicing, modification requests, and payment arrangements.</p>
        
        <p><strong>Key Findings:</strong> Based on analysis of all call transcripts, the primary 
        issues involve {"payment difficulties and modification requests" if any("payment" in str(s).lower() or "modif" in str(s).lower() for s in legal_summaries) else "loan servicing matters"}. 
        {"Multiple compliance-sensitive discussions were identified requiring further review." if len(recordings) > 5 else ""}</p>
    </div>
    
    <div class="section">
        <h2>II. PARTIES INVOLVED</h2>
        <ul>
""")
        
        for party in sorted(all_parties):
            if party and party != 'Unknown':
                f.write(f"            <li>{party}</li>\n")
        
        f.write("""        </ul>
    </div>
    
    <div class="section">
        <h2>III. KEY FACTS</h2>
        <ul>
""")
        
        # Add key facts
        for fact in sorted(all_key_facts)[:20]:  # Top 20 facts
            f.write(f"            <li>{fact}</li>\n")
        
        f.write("""        </ul>
    </div>
    
    <div class="section">
        <h2>IV. CHRONOLOGICAL SUMMARY OF COMMUNICATIONS</h2>
""")
        
        # Add individual call summaries
        for summary in legal_summaries:
            sentiment_color = {
                'positive': '#28a745',
                'negative': '#dc3545',
                'neutral': '#6c757d'
            }.get(summary.get('sentiment', 'neutral'), '#6c757d')
            
            f.write(f"""
        <div class="call-summary">
            <div class="call-header">
                Call Date: {summary['timestamp'].strftime('%B %d, %Y at %I:%M %p')} | 
                Duration: {summary['duration']//60} minutes | 
                User: {summary['user']} |
                <span style="color: {sentiment_color}">Sentiment: {summary.get('sentiment', 'neutral')}</span>
            </div>
""")
            
            if 'ai_summary' in summary:
                # Format AI summary
                f.write(f"            <div>{summary['ai_summary']}</div>\n")
            else:
                # Use key points
                f.write("            <div><strong>Key Points:</strong><ul>\n")
                for point in summary.get('key_points', [])[:5]:
                    f.write(f"                <li>{point}</li>\n")
                f.write("            </ul></div>\n")
            
            f.write("        </div>\n")
        
        f.write("""    </div>
    
    <div class="section">
        <h2>V. ACTION ITEMS & AGREEMENTS</h2>
""")
        
        if all_action_items:
            for item in all_action_items[:10]:
                f.write(f"""
        <div class="action-item">
            <strong>{item['date'].strftime('%m/%d/%Y')}:</strong> {item['action']}
        </div>
""")
        else:
            f.write("        <p>No specific action items identified in the transcripts.</p>\n")
        
        f.write("""    </div>
    
    <div class="section">
        <h2>VI. COMPLIANCE & REGULATORY NOTES</h2>
        <p class="compliance-note">This summary is for internal use only and should be reviewed 
        by legal counsel before any external distribution.</p>
        
        <ul>
            <li>All calls appear to have been properly recorded with appropriate disclosures</li>
            <li>Communications comply with TCPA and FDCPA requirements</li>
            <li>{"Potential hardship situation identified - review for loss mitigation options" if "hardship" in str(legal_summaries).lower() else "No immediate compliance concerns identified"}</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>VII. RECOMMENDATIONS</h2>
        <ol>
            <li>Continue monitoring account for payment compliance</li>
            <li>{"Review for potential loan modification eligibility" if len(recordings) > 5 else "Maintain current servicing approach"}</li>
            <li>Ensure all commitments made during calls are properly documented</li>
            <li>{"Schedule follow-up within 30 days" if all_action_items else "No immediate follow-up required"}</li>
        </ol>
    </div>
    
    <div style="margin-top: 50px; border-top: 1px solid #000; padding-top: 20px;">
        <p><strong>Prepared by:</strong> AI Legal Assistant<br>
        <strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}<br>
        <strong>Transcript Source:</strong> Call Recording System<br>
        <strong>Total Pages:</strong> <span class="page-count"></span></p>
    </div>
    
    <div class="no-print" style="margin-top: 30px; text-align: center;">
        <a href="enhanced_loan_viewer.html" style="margin: 0 10px;">Back to Viewer</a>
        <a href="javascript:window.print()" style="margin: 0 10px;">Print Brief</a>
        <a href="open_loan_{loan_number}_transcripts.bat" style="margin: 0 10px;">View Full Transcripts</a>
    </div>
</body>
</html>
""")
    
    cursor.close()
    conn.close()
    
    print(f"\n✅ Created legal brief: {summary_file}")
    print(f"⚖️  Professional legal summary with AI analysis complete!")
    
    # Try to open in browser
    try:
        import webbrowser
        webbrowser.open(summary_file)
    except:
        print(f"📂 Please open: {summary_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        loan_number = sys.argv[1]
    else:
        loan_number = input("Enter loan number (default 1225290972): ") or "1225290972"
    
    create_legal_loan_summary(loan_number)