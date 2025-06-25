#!/usr/bin/env python3
"""
LOAN TIMELINE WITH FEEDBACK - Surgical view plus thumbs down and loan correction
"""

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
import pymysql
import json
from datetime import datetime
import uvicorn

app = FastAPI(title="Loan Timeline with Feedback")

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

# Store feedback in memory (in production, use database)
feedback_data = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    """List loans with their mention counts"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get loans with counts
    cursor.execute("""
        SELECT 
            loan_numbers,
            COUNT(*) as mention_count,
            MIN(t.timestamp) as first_mention,
            MAX(t.timestamp) as last_mention
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE loan_numbers != '[]'
        GROUP BY loan_numbers
        HAVING mention_count >= 3
        ORDER BY last_mention DESC
        LIMIT 50
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    loan_cards = ""
    for row in rows:
        try:
            loans = json.loads(row['loan_numbers'])
            for loan in loans[:1]:
                days = (row['last_mention'] - row['first_mention']).days
                loan_cards += f'''
                <div class="loan-card" onclick="window.location.href='/timeline/{loan}'">
                    <div class="loan-number">#{loan}</div>
                    <div class="stats">
                        <div class="stat">
                            <span class="value">{row['mention_count']}</span>
                            <span class="label">mentions</span>
                        </div>
                        <div class="stat">
                            <span class="value">{days}</span>
                            <span class="label">days</span>
                        </div>
                    </div>
                    <div class="dates">{row['first_mention'].strftime('%m/%d')} → {row['last_mention'].strftime('%m/%d')}</div>
                </div>
                '''
        except:
            pass
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Timeline with Feedback</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f7fa;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                margin-bottom: 10px;
            }}
            .subtitle {{
                text-align: center;
                color: #7f8c8d;
                margin-bottom: 30px;
            }}
            .loan-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
            }}
            .loan-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                cursor: pointer;
                transition: all 0.2s;
                text-align: center;
            }}
            .loan-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            .loan-number {{
                font-size: 24px;
                font-weight: bold;
                color: #3498db;
                margin-bottom: 15px;
            }}
            .stats {{
                display: flex;
                justify-content: space-around;
                margin: 15px 0;
            }}
            .stat {{
                text-align: center;
            }}
            .stat .value {{
                display: block;
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .stat .label {{
                display: block;
                font-size: 12px;
                color: #95a5a6;
                text-transform: uppercase;
            }}
            .dates {{
                font-size: 14px;
                color: #7f8c8d;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Loan Timeline with Feedback</h1>
            <p class="subtitle">Review calls and provide feedback</p>
            <div class="loan-grid">
                {loan_cards}
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.get("/timeline/{loan_number}", response_class=HTMLResponse)
async def show_timeline(loan_number: str):
    """Show surgical timeline with feedback options"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get ONLY calls that mention this loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            ct.summary,
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
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not calls:
        return HTMLResponse(f"<h1>No calls found for loan {loan_number}</h1><a href='/'>Back</a>")
    
    # Calculate stats
    first_call = calls[0]
    last_call = calls[-1]
    journey_days = (last_call['timestamp'] - first_call['timestamp']).days
    total_duration = sum(c['duration'] for c in calls)
    processor_count = sum(1 for c in calls if c['call_type'] == 'PROCESSOR')
    
    # Build timeline with feedback
    timeline_html = ""
    for idx, call in enumerate(calls, 1):
        is_processor = call['call_type'] == 'PROCESSOR'
        call_id = call['orkuid']
        
        # Check if we have feedback for this call
        feedback = feedback_data.get(call_id, {})
        is_marked_wrong = feedback.get('type') == 'wrong'
        correct_loan = feedback.get('correct_loan', '')
        
        timeline_html += f'''
        <div class="timeline-item {'processor' if is_processor else ''} {'marked-wrong' if is_marked_wrong else ''}" id="call_{call_id}">
            <div class="timeline-marker">
                <div class="marker-dot"></div>
                <div class="marker-line"></div>
            </div>
            <div class="timeline-content">
                <div class="call-header">
                    <span class="call-number">Call #{idx}</span>
                    <span class="call-date">{call['timestamp'].strftime('%m/%d/%Y %I:%M %p')}</span>
                    <span class="call-duration">{call['duration']}s</span>
                </div>
                <div class="call-parties">
                    <span class="party from">{call['localParty']}</span>
                    <span class="arrow">→</span>
                    <span class="party to">{call['remoteParty']}</span>
                </div>
                <div class="call-user">User: {call['user_name']}</div>
                {'<div class="processor-tag">PROCESSOR ASSISTANT</div>' if is_processor else ''}
                
                <div class="feedback-section">
                    {'<div class="feedback-status">✓ Marked as wrong loan - Should be: ' + correct_loan + '</div>' if is_marked_wrong else ''}
                    <div class="feedback-controls" {'style="display:none;"' if is_marked_wrong else ''}>
                        <button class="thumbs-down" onclick="markWrongLoan('{call_id}')" title="This call is about a different loan">
                            👎 Wrong loan
                        </button>
                        <div class="loan-input" id="input_{call_id}" style="display:none;">
                            <input type="text" placeholder="Enter correct loan #" id="loan_{call_id}">
                            <button onclick="submitCorrection('{call_id}')">Submit</button>
                            <button onclick="cancelCorrection('{call_id}')">Cancel</button>
                        </div>
                    </div>
                </div>
                
                <div class="transcript-path">
                    <input type="text" value="{call.get('transcript_path', '') or ''}" readonly>
                    <button onclick="copyPath(this)">📋</button>
                </div>
            </div>
        </div>
        '''
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan #{loan_number} - Timeline with Feedback</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f7fa;
            }}
            .header {{
                background: white;
                padding: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
            }}
            h1 {{
                margin: 0;
                color: #2c3e50;
            }}
            .back {{
                color: #3498db;
                text-decoration: none;
                margin-bottom: 20px;
                display: inline-block;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .stat-value {{
                font-size: 32px;
                font-weight: bold;
                color: #3498db;
            }}
            .stat-label {{
                color: #7f8c8d;
                margin-top: 5px;
            }}
            .timeline {{
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 20px 0;
            }}
            .timeline-item {{
                display: flex;
                margin-bottom: 30px;
                position: relative;
            }}
            .timeline-marker {{
                width: 40px;
                position: relative;
                flex-shrink: 0;
            }}
            .marker-dot {{
                width: 16px;
                height: 16px;
                background: #3498db;
                border-radius: 50%;
                position: absolute;
                left: 12px;
                top: 5px;
                z-index: 2;
            }}
            .marker-line {{
                width: 2px;
                background: #e0e0e0;
                position: absolute;
                left: 19px;
                top: 25px;
                bottom: -30px;
            }}
            .timeline-item:last-child .marker-line {{
                display: none;
            }}
            .timeline-content {{
                flex: 1;
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-left: 10px;
            }}
            .processor .timeline-content {{
                background: #fff3cd;
                border: 1px solid #ffeeba;
            }}
            .processor .marker-dot {{
                background: #ff9900;
            }}
            .marked-wrong .timeline-content {{
                background: #f8d7da;
                border: 1px solid #f5c6cb;
            }}
            .marked-wrong .marker-dot {{
                background: #dc3545;
            }}
            .call-header {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                font-size: 14px;
            }}
            .call-number {{
                font-weight: bold;
                color: #2c3e50;
            }}
            .call-date {{
                color: #7f8c8d;
            }}
            .call-duration {{
                color: #3498db;
            }}
            .call-parties {{
                font-size: 16px;
                margin: 10px 0;
            }}
            .party {{
                font-weight: 500;
            }}
            .arrow {{
                margin: 0 10px;
                color: #7f8c8d;
            }}
            .call-user {{
                color: #7f8c8d;
                font-size: 14px;
                margin: 5px 0;
            }}
            .processor-tag {{
                display: inline-block;
                background: #ff9900;
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
                margin: 5px 0;
            }}
            .feedback-section {{
                margin: 15px 0;
                padding: 10px 0;
                border-top: 1px solid #e0e0e0;
            }}
            .feedback-controls {{
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .thumbs-down {{
                background: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }}
            .thumbs-down:hover {{
                background: #c82333;
            }}
            .loan-input {{
                display: flex;
                gap: 5px;
                align-items: center;
            }}
            .loan-input input {{
                padding: 5px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 150px;
            }}
            .loan-input button {{
                padding: 5px 10px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }}
            .loan-input button:first-of-type {{
                background: #28a745;
                color: white;
            }}
            .loan-input button:last-of-type {{
                background: #6c757d;
                color: white;
            }}
            .feedback-status {{
                color: #721c24;
                background: #f8d7da;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 14px;
            }}
            .transcript-path {{
                display: flex;
                align-items: center;
                margin-top: 10px;
                gap: 5px;
            }}
            .transcript-path input {{
                flex: 1;
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-family: monospace;
                font-size: 12px;
                background: white;
            }}
            .transcript-path button {{
                background: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
            }}
            .toast {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: #28a745;
                color: white;
                padding: 12px 20px;
                border-radius: 5px;
                opacity: 0;
                transition: opacity 0.3s;
                pointer-events: none;
            }}
            .toast.show {{
                opacity: 1;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <a href="/" class="back">← Back to Loans</a>
                <h1>Loan #{loan_number} - Timeline with Feedback</h1>
                <p style="color: #7f8c8d; margin: 5px 0;">Review calls and mark any that belong to different loans</p>
            </div>
        </div>
        
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{len(calls)}</div>
                    <div class="stat-label">Total Mentions</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{journey_days}</div>
                    <div class="stat-label">Journey Days</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{processor_count}</div>
                    <div class="stat-label">Processor Calls</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{int(total_duration/60)}</div>
                    <div class="stat-label">Total Minutes</div>
                </div>
            </div>
            
            <div class="timeline">
                <h2>Call Timeline</h2>
                {timeline_html}
            </div>
        </div>
        
        <div id="toast" class="toast"></div>
        
        <script>
            function copyPath(button) {{
                const input = button.previousElementSibling;
                input.select();
                document.execCommand('copy');
                button.textContent = '✓';
                setTimeout(() => button.textContent = '📋', 2000);
            }}
            
            function markWrongLoan(callId) {{
                document.getElementById('input_' + callId).style.display = 'flex';
            }}
            
            function cancelCorrection(callId) {{
                document.getElementById('input_' + callId).style.display = 'none';
                document.getElementById('loan_' + callId).value = '';
            }}
            
            async function submitCorrection(callId) {{
                const loanInput = document.getElementById('loan_' + callId);
                const correctLoan = loanInput.value.trim();
                
                if (!correctLoan) {{
                    alert('Please enter the correct loan number');
                    return;
                }}
                
                // Send feedback to server
                const response = await fetch('/feedback', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        call_id: callId,
                        type: 'wrong',
                        correct_loan: correctLoan
                    }})
                }});
                
                if (response.ok) {{
                    // Update UI
                    const callDiv = document.getElementById('call_' + callId);
                    callDiv.classList.add('marked-wrong');
                    
                    const feedbackSection = callDiv.querySelector('.feedback-section');
                    feedbackSection.innerHTML = `
                        <div class="feedback-status">✓ Marked as wrong loan - Should be: ${{correctLoan}}</div>
                    `;
                    
                    showToast('Feedback saved successfully!');
                }}
            }}
            
            function showToast(message) {{
                const toast = document.getElementById('toast');
                toast.textContent = message;
                toast.classList.add('show');
                setTimeout(() => {{
                    toast.classList.remove('show');
                }}, 3000);
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.post("/feedback")
async def save_feedback(data: dict):
    """Save feedback about a call"""
    call_id = data.get('call_id')
    feedback_type = data.get('type')
    correct_loan = data.get('correct_loan')
    
    # Store feedback (in production, save to database)
    feedback_data[call_id] = {
        'type': feedback_type,
        'correct_loan': correct_loan,
        'timestamp': datetime.now().isoformat()
    }
    
    return JSONResponse({"status": "success", "message": "Feedback saved"})

if __name__ == "__main__":
    print("Starting Loan Timeline with Feedback...")
    print("Open: http://localhost:8000")
    print("\nReview calls and provide feedback on wrong loan assignments!")
    uvicorn.run(app, host="0.0.0.0", port=8000)