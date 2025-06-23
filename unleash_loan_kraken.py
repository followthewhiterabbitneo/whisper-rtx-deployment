#!/usr/bin/env python3
"""
UNLEASH THE KRAKEN - AI-Powered Loan Analysis System
Generates comprehensive legal briefs and business intelligence for loan files
"""

import pymysql
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import re

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def extract_loan_intelligence(transcript):
    """Extract comprehensive business intelligence from transcript"""
    intelligence = {
        'loan_numbers': [],
        'amounts': [],
        'rates': [],
        'dates': [],
        'names': [],
        'addresses': [],
        'employers': [],
        'issues': [],
        'actions': [],
        'key_facts': []
    }
    
    # Extract loan numbers (various formats)
    loan_patterns = [
        r'\b\d{10}\b',  # 10-digit loan numbers
        r'loan\s*#?\s*(\d+)',
        r'file\s*#?\s*(\d+)',
        r'case\s*#?\s*(\d+)'
    ]
    for pattern in loan_patterns:
        matches = re.finditer(pattern, transcript, re.IGNORECASE)
        for match in matches:
            num = match.group(1) if match.groups() else match.group(0)
            if len(num) >= 7:  # At least 7 digits for loan number
                intelligence['loan_numbers'].append(num)
    
    # Extract dollar amounts
    amount_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
    for match in re.finditer(amount_pattern, transcript):
        amount = match.group(1).replace(',', '')
        try:
            if float(amount) > 1000:  # Significant amounts only
                intelligence['amounts'].append(amount)
        except:
            pass
    
    # Extract percentages/rates
    rate_pattern = r'(\d+(?:\.\d+)?)\s*%'
    for match in re.finditer(rate_pattern, transcript):
        intelligence['rates'].append(f"{match.group(1)}%")
    
    # Extract dates
    date_patterns = [
        r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',
        r'\b(\w+\s+\d{1,2},?\s+\d{4})\b',
        r'\b(\d{1,2}-\d{1,2}-\d{2,4})\b'
    ]
    for pattern in date_patterns:
        matches = re.finditer(pattern, transcript)
        for match in matches:
            intelligence['dates'].append(match.group(1))
    
    # Extract names (basic pattern)
    name_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
    for match in re.finditer(name_pattern, transcript):
        name = match.group(1)
        if name not in ['United Wholesale', 'Wholesale Mortgage']:
            intelligence['names'].append(name)
    
    # Extract key issues
    issue_keywords = [
        'expired', 'missing', 'incorrect', 'discrepancy', 'issue', 'problem',
        'concern', 'clarification', 'documentation', 'condition'
    ]
    for keyword in issue_keywords:
        pattern = rf'([^.]*{keyword}[^.]*\.)'
        for match in re.finditer(pattern, transcript, re.IGNORECASE):
            intelligence['issues'].append(match.group(1).strip())
    
    # Extract action items
    action_keywords = [
        'need', 'require', 'must', 'should', 'will', 'submit', 'provide',
        'update', 'correct', 'send'
    ]
    for keyword in action_keywords:
        pattern = rf'([^.]*{keyword}[^.]*\.)'
        for match in re.finditer(pattern, transcript, re.IGNORECASE):
            text = match.group(1).strip()
            if len(text) < 200:  # Reasonable length
                intelligence['actions'].append(text)
    
    return intelligence

def create_legal_brief_prompt(transcript, metadata):
    """Create prompt for legal brief generation"""
    
    prompt = f"""You are a legal assistant specializing in mortgage and loan documentation. Create a professional legal brief summary of this call transcript.

CALL INFORMATION:
- Date: {metadata.get('date', 'Unknown')}
- Recording ID: {metadata.get('orkuid', 'Unknown')}
- Duration: {metadata.get('duration', 'Unknown')}
- Parties: {metadata.get('parties', 'Unknown')}

TRANSCRIPT:
{transcript[:10000]}

Create a legal brief with EXACTLY this format:

**1. EXECUTIVE SUMMARY** (2-3 sentences summarizing the entire call)

**2. KEY FACTS** (bullet points with specific data):
- Loan Amount: $XXX,XXX
- Interest Rate: X.XX%
- Property Address: 
- Borrower Name:
- Important Dates:
- Other critical numbers/facts

**3. PARTIES INVOLVED** (with roles and identifiers)

**4. MAIN DISCUSSION POINTS** (what was actually discussed)

**5. ACTION ITEMS/AGREEMENTS** (specific commitments made)

**6. COMPLIANCE NOTES** (any regulatory concerns or requirements)

**7. RISK ASSESSMENT** (potential issues or red flags)"""
    
    return prompt

def generate_ai_summary(prompt):
    """Generate summary using available AI model"""
    try:
        # Try to use llama-cpp-python with local model
        from llama_cpp import Llama
        
        # Try different model paths
        model_paths = [
            "models/gemma-2-9b-it-Q5_K_M.gguf",
            "models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf",
            "models/gemma-3-12b-it-qat-q4_0/gemma-3-12b-it-qat-q4_0.gguf"
        ]
        
        model_path = None
        for path in model_paths:
            if os.path.exists(path):
                model_path = path
                print(f"   🤖 Using AI model: {path}")
                break
        
        if model_path:
            llm = Llama(
                model_path=model_path,
                n_gpu_layers=-1,
                n_ctx=8192,
                n_batch=512,
                verbose=False
            )
            
            response = llm(
                prompt,
                max_tokens=2048,
                temperature=0.1,
                top_p=0.9
            )
            
            return response['choices'][0]['text'].strip()
    except Exception as e:
        print(f"   ⚠️  AI generation failed: {e}")
    
    return None

def unleash_the_kraken(loan_number):
    """Generate comprehensive loan analysis with AI"""
    
    print(f"""
═══════════════════════════════════════════════════════════════════════════════
                    🐙 UNLEASHING THE KRAKEN ON LOAN #{loan_number} 🐙
                         AI-POWERED LOAN INTELLIGENCE SYSTEM
═══════════════════════════════════════════════════════════════════════════════
""")
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all recordings for this loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            ct.transcript_path,
            ct.loan_numbers,
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
    
    print(f"🎯 Found {len(recordings)} recordings to analyze\n")
    
    # Process each recording
    all_summaries = []
    all_intelligence = {
        'loan_amounts': set(),
        'interest_rates': set(),
        'key_dates': set(),
        'participants': set(),
        'issues': [],
        'actions': []
    }
    
    for i, rec in enumerate(recordings, 1):
        print(f"📞 Processing Recording {i}/{len(recordings)}: {rec['orkuid']}")
        print(f"   Date: {rec['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Duration: {rec['duration']/60:.1f} minutes")
        
        # Read transcript
        transcript_text = ""
        path = rec['transcript_path']
        
        if path:
            if path.startswith('C:/'):
                path = path.replace('/', '\\')
            
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    transcript_text = f.read()
                print(f"   ✓ Read transcript: {len(transcript_text)} characters")
            except Exception as e:
                print(f"   ❌ Error reading transcript: {e}")
                continue
        
        if transcript_text:
            # Extract intelligence
            intel = extract_loan_intelligence(transcript_text)
            
            # Update aggregate intelligence
            all_intelligence['loan_amounts'].update(intel['amounts'])
            all_intelligence['interest_rates'].update(intel['rates'])
            all_intelligence['key_dates'].update(intel['dates'])
            all_intelligence['participants'].add(rec['user_name'] or rec['localParty'])
            all_intelligence['issues'].extend(intel['issues'][:3])  # Top 3 issues
            all_intelligence['actions'].extend(intel['actions'][:3])  # Top 3 actions
            
            # Generate AI summary
            metadata = {
                'date': rec['timestamp'].strftime('%Y-%m-%d %H:%M'),
                'orkuid': rec['orkuid'],
                'duration': f"{rec['duration']/60:.1f} minutes",
                'parties': f"{rec['localParty']} / {rec['remoteParty']}"
            }
            
            prompt = create_legal_brief_prompt(transcript_text, metadata)
            ai_summary = generate_ai_summary(prompt)
            
            if ai_summary:
                print("   ✓ Generated AI legal brief")
                all_summaries.append({
                    'recording': rec,
                    'intelligence': intel,
                    'ai_summary': ai_summary
                })
            else:
                print("   ⚠️  Using intelligence extraction only")
                all_summaries.append({
                    'recording': rec,
                    'intelligence': intel,
                    'ai_summary': None
                })
        
        print()
    
    # Generate comprehensive report
    report_file = f"loan_{loan_number}_KRAKEN_ANALYSIS.html"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>KRAKEN Analysis - Loan #{loan_number}</title>
    <style>
        body {{ 
            font-family: 'Consolas', 'Monaco', monospace; 
            background: #0a0a0a;
            color: #00ff00;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            border: 2px solid #00ff00;
            padding: 20px;
            margin-bottom: 30px;
            background: #001100;
        }}
        h1 {{ 
            color: #00ff00;
            text-shadow: 0 0 10px #00ff00;
            margin: 0;
            font-size: 32px;
        }}
        .intelligence-box {{
            border: 1px solid #00ff00;
            padding: 20px;
            margin: 20px 0;
            background: #001100;
        }}
        .section-header {{
            color: #00ffff;
            font-size: 20px;
            margin: 20px 0 10px 0;
            border-bottom: 1px solid #00ff00;
            padding-bottom: 5px;
        }}
        .fact {{
            color: #ffff00;
            font-weight: bold;
        }}
        .legal-brief {{
            background: white;
            color: black;
            padding: 30px;
            margin: 20px 0;
            border-radius: 5px;
            font-family: 'Times New Roman', serif;
            line-height: 1.6;
        }}
        .legal-brief h3 {{
            color: #000080;
        }}
        pre {{
            background: #000033;
            padding: 15px;
            overflow-x: auto;
            border: 1px solid #0066ff;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-box {{
            border: 1px solid #00ff00;
            padding: 15px;
            text-align: center;
            background: #002200;
        }}
        .metric-value {{
            font-size: 24px;
            color: #00ffff;
            font-weight: bold;
        }}
        .metric-label {{
            color: #00ff00;
            font-size: 12px;
            text-transform: uppercase;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <pre>
═══════════════════════════════════════════════════════════════════════════════
                    🐙 KRAKEN LOAN ANALYSIS SYSTEM 🐙
                        LOAN #{loan_number}
═══════════════════════════════════════════════════════════════════════════════
            </pre>
            <h1>AI-POWERED INTELLIGENCE EXTRACTION</h1>
        </div>
        
        <div class="intelligence-box">
            <div class="section-header">📊 AGGREGATE INTELLIGENCE</div>
            
            <div class="summary-grid">
                <div class="metric-box">
                    <div class="metric-label">Total Calls</div>
                    <div class="metric-value">{len(recordings)}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Date Range</div>
                    <div class="metric-value">{(recordings[-1]['timestamp'] - recordings[0]['timestamp']).days} days</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Total Duration</div>
                    <div class="metric-value">{sum(r['duration'] for r in recordings)/60:.0f} min</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Participants</div>
                    <div class="metric-value">{len(all_intelligence['participants'])}</div>
                </div>
            </div>
            
            <pre>
┌─────────────────────────────────────────────────────────────────────────────┐
│ EXTRACTED FINANCIAL DATA                                                    │
├─────────────────────────────────────────────────────────────────────────────┤""")
        
        # Add loan amounts
        if all_intelligence['loan_amounts']:
            amounts = sorted([float(a) for a in all_intelligence['loan_amounts']], reverse=True)[:5]
            for amt in amounts:
                f.write(f"\n│ Loan Amount:           <span class='fact'>${amt:,.2f}</span>".ljust(79) + "│")
        
        # Add interest rates
        if all_intelligence['interest_rates']:
            for rate in sorted(all_intelligence['interest_rates'])[:5]:
                f.write(f"\n│ Interest Rate:         <span class='fact'>{rate}</span>".ljust(79) + "│")
        
        f.write("""
├─────────────────────────────────────────────────────────────────────────────┤
│ KEY PARTICIPANTS                                                            │
├─────────────────────────────────────────────────────────────────────────────┤""")
        
        for participant in sorted(all_intelligence['participants']):
            if participant:
                f.write(f"\n│ • {participant}".ljust(78) + "│")
        
        f.write("""
└─────────────────────────────────────────────────────────────────────────────┘
            </pre>
        </div>
""")
        
        # Add individual call summaries
        for i, summary in enumerate(all_summaries, 1):
            rec = summary['recording']
            f.write(f"""
        <div class="intelligence-box">
            <div class="section-header">📞 CALL {i}: {rec['orkuid']}</div>
            <pre>
Date: {rec['timestamp'].strftime('%Y-%m-%d %H:%M')}
Duration: {rec['duration']/60:.1f} minutes
Parties: {rec['localParty']} / {rec['remoteParty']}
            </pre>
""")
            
            if summary['ai_summary']:
                # Format the summary outside f-string to avoid backslash issues
                formatted_summary = summary['ai_summary'].replace('\n', '<br>')
                f.write(f"""
            <div class="legal-brief">
                <h3>AI-Generated Legal Brief</h3>
                {formatted_summary}
            </div>
""")
            else:
                # Show extracted intelligence
                intel = summary['intelligence']
                f.write("""
            <pre>
EXTRACTED INTELLIGENCE:
""")
                if intel['amounts']:
                    f.write(f"Amounts Found: {', '.join(['$' + a for a in intel['amounts'][:5]])}\n")
                if intel['rates']:
                    f.write(f"Rates Found: {', '.join(intel['rates'][:5])}\n")
                if intel['dates']:
                    f.write(f"Dates Found: {', '.join(intel['dates'][:5])}\n")
                if intel['issues']:
                    f.write(f"\nIssues Identified:\n")
                    for issue in intel['issues'][:3]:
                        f.write(f"  • {issue[:100]}...\n")
                f.write("</pre>")
            
            f.write("        </div>\n")
        
        # Add master summary
        f.write(f"""
        <div class="intelligence-box">
            <div class="section-header">🎯 MASTER LOAN SUMMARY</div>
            <pre>
┌─────────────────────────────────────────────────────────────────────────────┐
│ LOAN LIFECYCLE ANALYSIS                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ First Contact:         {recordings[0]['timestamp'].strftime('%B %d, %Y')}                                           │
│ Last Contact:          {recordings[-1]['timestamp'].strftime('%B %d, %Y')}                                           │
│ Total Interactions:    {len(recordings)} calls over {(recordings[-1]['timestamp'] - recordings[0]['timestamp']).days} days                             │
│ Communication Hours:   {sum(r['duration'] for r in recordings)/3600:.1f} hours total                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ KEY ISSUES & ACTIONS                                                        │
├─────────────────────────────────────────────────────────────────────────────┤""")
        
        # Add top issues
        for issue in all_intelligence['issues'][:5]:
            if issue:
                f.write(f"\n│ ⚠️  {issue[:70]}...".ljust(78) + "│")
        
        # Add top actions
        for action in all_intelligence['actions'][:5]:
            if action:
                f.write(f"\n│ ✓  {action[:70]}...".ljust(78) + "│")
        
        f.write("""
└─────────────────────────────────────────────────────────────────────────────┘
            </pre>
        </div>
        
        <div style="text-align: center; margin: 40px 0; color: #00ff00;">
            <p>═══════════════════════════════════════════════════════════════════════════════</p>
            <p>KRAKEN ANALYSIS COMPLETE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>═══════════════════════════════════════════════════════════════════════════════</p>
        </div>
    </div>
</body>
</html>
""")
    
    cursor.close()
    conn.close()
    
    print(f"""
═══════════════════════════════════════════════════════════════════════════════
                        🐙 KRAKEN ANALYSIS COMPLETE! 🐙
═══════════════════════════════════════════════════════════════════════════════

📊 SUMMARY:
   • Analyzed {len(recordings)} calls
   • Extracted {len(all_intelligence['loan_amounts'])} loan amounts
   • Found {len(all_intelligence['interest_rates'])} interest rates
   • Identified {len(all_intelligence['participants'])} participants
   • Generated {len([s for s in all_summaries if s['ai_summary']])} AI summaries

📁 Report saved to: {report_file}

🌐 Opening in browser...
""")
    
    try:
        import webbrowser
        webbrowser.open(report_file)
    except:
        print("⚠️  Could not auto-open browser")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        loan_number = sys.argv[1]
    else:
        loan_number = input("Enter loan number: ")
    
    unleash_the_kraken(loan_number)