#!/usr/bin/env python3
"""
LOAN TIMELINE WITH ADD CALL - Timeline plus ability to insert missing calls
"""

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
import pymysql
import json
from datetime import datetime
import uvicorn

app = FastAPI(title="Loan Timeline with Add Call")

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
    
    # Get loans with counts - ONLY 10+ calls
    cursor.execute("""
        SELECT 
            loan_numbers,
            COUNT(*) as mention_count,
            MIN(t.timestamp) as first_mention,
            MAX(t.timestamp) as last_mention,
            SUM(CASE WHEN t.localParty LIKE '19472421%%' OR t.remoteParty LIKE '19472421%%' THEN 1 ELSE 0 END) as processor_calls
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE loan_numbers != '[]'
        GROUP BY loan_numbers
        HAVING mention_count >= 10
        ORDER BY mention_count DESC, last_mention DESC
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
                            <span class="label">calls</span>
                        </div>
                        <div class="stat">
                            <span class="value">{row['processor_calls']}</span>
                            <span class="label">processor</span>
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
        <title>Loan Timeline with Add Call</title>
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
            <h1>🎯 Loan Timeline with Add Call</h1>
            <p class="subtitle">Showing loans with 10+ calls - Add missing calls to timeline</p>
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
    """Show surgical timeline with add call option"""
    
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
        
        timeline_html += f'''
        <div class="timeline-item {'processor' if is_processor else ''}" id="call_{call_id}">
            <div class="timeline-marker">
                <div class="marker-dot"></div>
                <div class="marker-line"></div>
            </div>
            <div class="timeline-content">
                <div class="call-header">
                    <span class="call-number">Call #{idx}</span>
                    <span class="call-orkuid">{call_id}</span>
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
                    <div class="feedback-controls">
                        <button class="thumbs-up" onclick="markGood('{call_id}')" title="Correct loan">
                            👍
                        </button>
                        <button class="thumbs-down" onclick="markBad('{call_id}')" title="Wrong loan">
                            👎
                        </button>
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
        <title>Loan #{loan_number} - Timeline with Add Call</title>
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
            .add-call-btn {{
                background: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                float: right;
                margin-top: -5px;
            }}
            .add-call-btn:hover {{
                background: #229954;
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
            .timeline-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
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
            .call-orkuid {{
                font-family: monospace;
                color: #666;
                font-size: 12px;
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
            .thumbs-up, .thumbs-down {{
                background: #f0f0f0;
                border: none;
                padding: 8px 12px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 18px;
                width: 40px;
                height: 40px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
            }}
            .thumbs-up:hover {{
                background: #e0e0e0;
                transform: scale(1.1);
            }}
            .thumbs-down:hover {{
                background: #e0e0e0;
                transform: scale(1.1);
            }}
            .thumbs-up.active {{
                background: #d4edda;
            }}
            .thumbs-down.active {{
                background: #f8d7da;
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
            /* Add Call Modal */
            .modal {{
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
            }}
            .modal-content {{
                background-color: white;
                margin: 15% auto;
                padding: 30px;
                border-radius: 8px;
                width: 500px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }}
            .modal-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }}
            .modal-header h2 {{
                margin: 0;
                color: #2c3e50;
            }}
            .close {{
                color: #aaa;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }}
            .close:hover {{
                color: black;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            .form-group label {{
                display: block;
                margin-bottom: 5px;
                color: #2c3e50;
                font-weight: 500;
            }}
            .form-group input {{
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
            }}
            .form-group small {{
                color: #7f8c8d;
                display: block;
                margin-top: 5px;
            }}
            .modal-buttons {{
                display: flex;
                gap: 10px;
                justify-content: flex-end;
            }}
            .btn-submit {{
                background: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }}
            .btn-submit:hover {{
                background: #229954;
            }}
            .btn-cancel {{
                background: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }}
            .btn-cancel:hover {{
                background: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <a href="/" class="back">← Back to Loans</a>
                <button class="add-call-btn" onclick="showAddCallModal()">+ Add Missing Call</button>
                <h1>Loan #{loan_number} - Timeline</h1>
                <p style="color: #7f8c8d; margin: 5px 0;">Review calls and add any missing transfers</p>
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
                <div class="timeline-header">
                    <h2>Call Timeline</h2>
                </div>
                {timeline_html}
            </div>
        </div>
        
        <!-- Add Call Modal -->
        <div id="addCallModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Add Missing Call</h2>
                    <span class="close" onclick="closeAddCallModal()">&times;</span>
                </div>
                <form id="addCallForm">
                    <div class="form-group">
                        <label for="orkuid">Call ID (orkUid)</label>
                        <input type="text" id="orkuid" name="orkuid" placeholder="e.g., 20250612_125406_UVCT" required>
                        <small>The orkUid/filename of the missing call</small>
                    </div>
                    <div class="form-group">
                        <label for="position">Position in Timeline (optional)</label>
                        <input type="text" id="position" name="position" placeholder="e.g., After call #12">
                        <small>Where this call should appear in the timeline</small>
                    </div>
                    <div class="modal-buttons">
                        <button type="button" class="btn-cancel" onclick="closeAddCallModal()">Cancel</button>
                        <button type="submit" class="btn-submit">Add Call</button>
                    </div>
                </form>
            </div>
        </div>
        
        <div id="toast" class="toast"></div>
        
        <script>
            const loanNumber = '{loan_number}';
            
            function copyPath(button) {{
                const input = button.previousElementSibling;
                input.select();
                document.execCommand('copy');
                button.textContent = '✓';
                setTimeout(() => button.textContent = '📋', 2000);
            }}
            
            async function markGood(callId) {{
                const callDiv = document.getElementById('call_' + callId);
                const thumbsUp = callDiv.querySelector('.thumbs-up');
                const thumbsDown = callDiv.querySelector('.thumbs-down');
                
                thumbsUp.classList.toggle('active');
                thumbsDown.classList.remove('active');
                
                await fetch('/feedback', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        call_id: callId,
                        type: 'correct'
                    }})
                }});
            }}
            
            async function markBad(callId) {{
                const callDiv = document.getElementById('call_' + callId);
                const thumbsUp = callDiv.querySelector('.thumbs-up');
                const thumbsDown = callDiv.querySelector('.thumbs-down');
                
                thumbsDown.classList.toggle('active');
                thumbsUp.classList.remove('active');
                
                await fetch('/feedback', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        call_id: callId,
                        type: 'wrong'
                    }})
                }});
            }}
            
            function showAddCallModal() {{
                document.getElementById('addCallModal').style.display = 'block';
            }}
            
            function closeAddCallModal() {{
                document.getElementById('addCallModal').style.display = 'none';
                document.getElementById('addCallForm').reset();
            }}
            
            document.getElementById('addCallForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const orkuid = document.getElementById('orkuid').value;
                const position = document.getElementById('position').value;
                
                const response = await fetch('/add-call', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        loan_number: loanNumber,
                        orkuid: orkuid,
                        position: position
                    }})
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    showToast('Call added successfully! Refreshing timeline...');
                    setTimeout(() => window.location.reload(), 2000);
                }} else {{
                    showToast('Error: ' + result.message, 'error');
                }}
                
                closeAddCallModal();
            }});
            
            function showToast(message, type = 'success') {{
                const toast = document.getElementById('toast');
                toast.textContent = message;
                toast.style.background = type === 'error' ? '#dc3545' : '#28a745';
                toast.classList.add('show');
                setTimeout(() => {{
                    toast.classList.remove('show');
                }}, 3000);
            }}
            
            // Close modal when clicking outside
            window.onclick = function(event) {{
                const modal = document.getElementById('addCallModal');
                if (event.target == modal) {{
                    closeAddCallModal();
                }}
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
    
    feedback_data[call_id] = {
        'type': feedback_type,
        'timestamp': datetime.now().isoformat()
    }
    
    return JSONResponse({"status": "success", "message": "Feedback saved"})

@app.post("/add-call")
async def add_call(data: dict):
    """Add a missing call to a loan"""
    loan_number = data.get('loan_number')
    orkuid = data.get('orkuid')
    position = data.get('position')
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    try:
        # Check if call exists
        cursor.execute("SELECT * FROM orktape WHERE orkUid = %s", (orkuid,))
        call = cursor.fetchone()
        
        if not call:
            return JSONResponse({
                "success": False, 
                "message": f"Call {orkuid} not found in database"
            }, status_code=404)
        
        # Check if already has loan assignments
        cursor.execute("SELECT loan_numbers FROM call_transcripts_v2 WHERE orkuid = %s", (orkuid,))
        existing = cursor.fetchone()
        
        current_loans = []
        if existing and existing.get('loan_numbers'):
            current_loans = json.loads(existing['loan_numbers'])
        
        if loan_number not in current_loans:
            current_loans.append(loan_number)
            new_loan_json = json.dumps(current_loans)
            
            if existing:
                # Update
                cursor.execute("""
                    UPDATE call_transcripts_v2 
                    SET loan_numbers = %s, updated_at = NOW()
                    WHERE orkuid = %s
                """, (new_loan_json, orkuid))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO call_transcripts_v2 (orkuid, loan_numbers, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                """, (orkuid, new_loan_json))
            
            conn.commit()
        
        cursor.close()
        conn.close()
        
        return JSONResponse({
            "success": True,
            "message": f"Call {orkuid} added to loan {loan_number}"
        })
        
    except Exception as e:
        cursor.close()
        conn.close()
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)

if __name__ == "__main__":
    print("Starting Loan Timeline with Add Call...")
    print("Open: http://localhost:8002")
    print("\nAdd missing calls directly from the timeline!")
    uvicorn.run(app, host="0.0.0.0", port=8002)