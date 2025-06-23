#!/usr/bin/env python3
"""
Extract REAL loan facts - numbers, rates, amounts, dates
What underwriters actually need!
"""

import pymysql
import json
import os
import re
from datetime import datetime
from pathlib import Path

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def extract_numbers(text):
    """Extract all monetary amounts, percentages, and important numbers"""
    findings = {
        'loan_amounts': [],
        'payment_amounts': [],
        'interest_rates': [],
        'dates': [],
        'income_amounts': [],
        'credit_scores': [],
        'ltv_ratios': [],
        'dti_ratios': [],
        'other_numbers': []
    }
    
    # Loan amounts (usually 6-7 digits)
    loan_pattern = r'\$?(\d{1,3},?\d{3},?\d{3}|\d{6,7})\s*(?:loan|mortgage|principal|balance|amount)'
    for match in re.finditer(loan_pattern, text, re.IGNORECASE):
        amount = match.group(1).replace(',', '')
        findings['loan_amounts'].append(amount)
    
    # Payment amounts (usually 3-5 digits)
    payment_pattern = r'\$?(\d{1,3},?\d{3}|\d{3,5})\s*(?:payment|monthly|month|due)'
    for match in re.finditer(payment_pattern, text, re.IGNORECASE):
        amount = match.group(1).replace(',', '')
        findings['payment_amounts'].append(amount)
    
    # Interest rates
    rate_pattern = r'(\d+\.?\d*)\s*(?:%|percent|percentage|rate|APR)'
    for match in re.finditer(rate_pattern, text, re.IGNORECASE):
        rate = match.group(1)
        findings['interest_rates'].append(f"{rate}%")
    
    # Credit scores (3 digits between 300-850)
    credit_pattern = r'\b([3-8]\d{2})\s*(?:credit|FICO|score)'
    for match in re.finditer(credit_pattern, text, re.IGNORECASE):
        score = match.group(1)
        if 300 <= int(score) <= 850:
            findings['credit_scores'].append(score)
    
    # Income amounts
    income_pattern = r'\$?(\d{1,3},?\d{3})\s*(?:income|salary|earn|make)'
    for match in re.finditer(income_pattern, text, re.IGNORECASE):
        amount = match.group(1).replace(',', '')
        findings['income_amounts'].append(amount)
    
    # LTV ratios
    ltv_pattern = r'(\d{2,3})\s*(?:%|percent)?\s*LTV'
    for match in re.finditer(ltv_pattern, text, re.IGNORECASE):
        ltv = match.group(1)
        findings['ltv_ratios'].append(f"{ltv}%")
    
    # DTI ratios
    dti_pattern = r'DTI\s*(?:of|is)?\s*(\d{2,3})\s*(?:%|percent)?'
    for match in re.finditer(dti_pattern, text, re.IGNORECASE):
        dti = match.group(1)
        findings['dti_ratios'].append(f"{dti}%")
    
    # Important dates
    date_patterns = [
        r'(\d{1,2}/\d{1,2}/\d{2,4})',
        r'(\w+ \d{1,2}, \d{4})',
        r'(\d{1,2}-\d{1,2}-\d{2,4})'
    ]
    for pattern in date_patterns:
        for match in re.finditer(pattern, text):
            findings['dates'].append(match.group(1))
    
    return findings

def extract_loan_terms(text):
    """Extract specific loan terms and conditions"""
    terms = {
        'loan_type': None,
        'term_length': None,
        'property_type': None,
        'occupancy': None,
        'purpose': None
    }
    
    # Loan types
    if re.search(r'\bFHA\b', text, re.IGNORECASE):
        terms['loan_type'] = 'FHA'
    elif re.search(r'\bVA\b', text, re.IGNORECASE):
        terms['loan_type'] = 'VA'
    elif re.search(r'\bconventional\b', text, re.IGNORECASE):
        terms['loan_type'] = 'Conventional'
    elif re.search(r'\bjumbo\b', text, re.IGNORECASE):
        terms['loan_type'] = 'Jumbo'
    
    # Term length
    term_match = re.search(r'(\d{2})\s*year', text, re.IGNORECASE)
    if term_match:
        terms['term_length'] = f"{term_match.group(1)} year"
    
    # Property type
    if re.search(r'single\s*family', text, re.IGNORECASE):
        terms['property_type'] = 'Single Family'
    elif re.search(r'condo', text, re.IGNORECASE):
        terms['property_type'] = 'Condo'
    elif re.search(r'multi\s*family', text, re.IGNORECASE):
        terms['property_type'] = 'Multi-family'
    
    # Purpose
    if re.search(r'refinance|refi', text, re.IGNORECASE):
        terms['purpose'] = 'Refinance'
    elif re.search(r'purchase', text, re.IGNORECASE):
        terms['purpose'] = 'Purchase'
    elif re.search(r'cash\s*out', text, re.IGNORECASE):
        terms['purpose'] = 'Cash-out Refinance'
    
    return terms

def create_underwriter_summary(loan_number):
    """Create a summary with ACTUAL LOAN FACTS for underwriters"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all transcripts for this loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            ct.transcript_path,
            ct.loan_numbers,
            t.timestamp,
            t.duration,
            l.user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN loan_number_index l ON ct.orkuid = l.orkuid AND l.loan_number = %s
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (loan_number, f'%{loan_number}%'))
    
    recordings = cursor.fetchall()
    
    print(f"\n💰 EXTRACTING REAL LOAN DATA FOR #{loan_number}")
    print(f"Found {len(recordings)} recordings to analyze")
    
    # Aggregate all findings
    all_findings = {
        'loan_amounts': set(),
        'payment_amounts': set(),
        'interest_rates': set(),
        'dates': set(),
        'income_amounts': set(),
        'credit_scores': set(),
        'ltv_ratios': set(),
        'dti_ratios': set(),
        'loan_terms': {}
    }
    
    # Process each transcript
    for i, rec in enumerate(recordings, 1):
        print(f"\nScanning recording {i}/{len(recordings)}: {rec['orkuid']}")
        
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
            # Extract numbers
            findings = extract_numbers(transcript_text)
            for key, values in findings.items():
                if isinstance(all_findings[key], set):
                    all_findings[key].update(values)
            
            # Extract loan terms
            terms = extract_loan_terms(transcript_text)
            for key, value in terms.items():
                if value and not all_findings['loan_terms'].get(key):
                    all_findings['loan_terms'][key] = value
    
    # Create underwriter fact sheet
    summary_file = f"loan_{loan_number}_FACTS.html"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Loan #{loan_number} - Underwriting Facts</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 800px;
            margin: 20px auto;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            background: #ecf0f1;
            padding: 10px;
            border-left: 4px solid #3498db;
        }}
        .fact-group {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .fact-label {{
            font-weight: bold;
            color: #2c3e50;
            display: inline-block;
            width: 150px;
        }}
        .fact-value {{
            color: #e74c3c;
            font-size: 18px;
            font-weight: bold;
        }}
        .numbers-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        .number-box {{
            background: #fff;
            border: 2px solid #3498db;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .number-box h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 14px;
        }}
        .number-box .value {{
            font-size: 24px;
            font-weight: bold;
            color: #e74c3c;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .success {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        ul {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 LOAN #{loan_number} - UNDERWRITING FACT SHEET</h1>
        <p style="color: #7f8c8d;">Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        
        <div class="numbers-grid">
""")
        
        # Loan Amount
        if all_findings['loan_amounts']:
            loan_amt = max(all_findings['loan_amounts'], key=lambda x: int(x))
            f.write(f"""
            <div class="number-box">
                <h3>LOAN AMOUNT</h3>
                <div class="value">${int(loan_amt):,}</div>
            </div>
""")
        
        # Monthly Payment
        if all_findings['payment_amounts']:
            payment = max(all_findings['payment_amounts'], key=lambda x: int(x))
            f.write(f"""
            <div class="number-box">
                <h3>MONTHLY PAYMENT</h3>
                <div class="value">${int(payment):,}</div>
            </div>
""")
        
        # Interest Rate
        if all_findings['interest_rates']:
            f.write(f"""
            <div class="number-box">
                <h3>INTEREST RATE</h3>
                <div class="value">{sorted(all_findings['interest_rates'])[0]}</div>
            </div>
""")
        
        # Credit Score
        if all_findings['credit_scores']:
            f.write(f"""
            <div class="number-box">
                <h3>CREDIT SCORE</h3>
                <div class="value">{max(all_findings['credit_scores'])}</div>
            </div>
""")
        
        f.write("""        </div>
        
        <h2>🏠 LOAN DETAILS</h2>
        <div class="fact-group">
""")
        
        # Loan terms
        if all_findings['loan_terms']:
            for key, value in all_findings['loan_terms'].items():
                if value:
                    label = key.replace('_', ' ').title()
                    f.write(f'            <div><span class="fact-label">{label}:</span> <span class="fact-value">{value}</span></div>\n')
        
        # LTV
        if all_findings['ltv_ratios']:
            f.write(f'            <div><span class="fact-label">LTV Ratio:</span> <span class="fact-value">{sorted(all_findings["ltv_ratios"])[0]}</span></div>\n')
        
        # DTI
        if all_findings['dti_ratios']:
            f.write(f'            <div><span class="fact-label">DTI Ratio:</span> <span class="fact-value">{sorted(all_findings["dti_ratios"])[0]}</span></div>\n')
        
        f.write("""        </div>
        
        <h2>💵 INCOME INFORMATION</h2>
        <div class="fact-group">
""")
        
        if all_findings['income_amounts']:
            f.write("            <div><strong>Income amounts mentioned:</strong></div>\n            <ul>\n")
            for income in sorted(all_findings['income_amounts'], key=lambda x: int(x), reverse=True):
                f.write(f"                <li>${int(income):,}</li>\n")
            f.write("            </ul>\n")
        else:
            f.write("            <div class='warning'>⚠️ No specific income amounts found in transcripts</div>\n")
        
        f.write("""        </div>
        
        <h2>📅 IMPORTANT DATES</h2>
        <div class="fact-group">
""")
        
        if all_findings['dates']:
            f.write("            <ul>\n")
            for date in sorted(set(all_findings['dates']))[:10]:
                f.write(f"                <li>{date}</li>\n")
            f.write("            </ul>\n")
        
        f.write("""        </div>
        
        <h2>🔍 ALL NUMBERS FOUND</h2>
        <div class="fact-group">
            <p>Complete list of all amounts and percentages mentioned:</p>
""")
        
        # Show all unique numbers found
        all_numbers = set()
        for key in ['loan_amounts', 'payment_amounts', 'income_amounts']:
            all_numbers.update(all_findings[key])
        
        if all_numbers:
            f.write("            <ul>\n")
            for num in sorted(all_numbers, key=lambda x: int(x), reverse=True):
                f.write(f"                <li>${int(num):,}</li>\n")
            f.write("            </ul>\n")
        
        # All rates found
        if all_findings['interest_rates']:
            f.write("            <p><strong>All rates mentioned:</strong> " + ", ".join(sorted(set(all_findings['interest_rates']))) + "</p>\n")
        
        f.write(f"""        </div>
        
        <h2>📞 CALL SUMMARY</h2>
        <div class="fact-group">
            <div><span class="fact-label">Total Calls:</span> {len(recordings)}</div>
            <div><span class="fact-label">Date Range:</span> {recordings[0]['timestamp'].strftime('%m/%d/%Y')} - {recordings[-1]['timestamp'].strftime('%m/%d/%Y')}</div>
            <div><span class="fact-label">Total Duration:</span> {sum(r['duration'] for r in recordings)//60} minutes</div>
        </div>
        
        <div style="margin-top: 40px; padding: 20px; background: #e8f4fd; border-radius: 5px;">
            <h3>🎯 UNDERWRITER ACTION ITEMS</h3>
            <ol>
                <li>Verify loan amount: ${int(loan_amt):,} if all_findings['loan_amounts'] else 'NOT FOUND'}</li>
                <li>Confirm interest rate: {sorted(all_findings['interest_rates'])[0] if all_findings['interest_rates'] else 'NOT FOUND'}</li>
                <li>Validate monthly payment: ${int(payment):,} if all_findings['payment_amounts'] else 'NOT FOUND'}</li>
                <li>Check credit score: {max(all_findings['credit_scores']) if all_findings['credit_scores'] else 'NOT FOUND'}</li>
                <li>Review income documentation{' - amounts found: ' + ', '.join([f'${int(x):,}' for x in sorted(all_findings['income_amounts'], key=lambda x: int(x), reverse=True)[:3]]) if all_findings['income_amounts'] else ' - NO AMOUNTS FOUND'}</li>
            </ol>
        </div>
        
        <div style="margin-top: 30px; text-align: center;">
            <a href="enhanced_loan_viewer.html" style="margin: 0 10px;">Back to Timeline</a>
            <a href="javascript:window.print()" style="margin: 0 10px;">Print Facts</a>
            <a href="open_loan_{loan_number}_transcripts.bat" style="margin: 0 10px;">View Transcripts</a>
        </div>
    </div>
</body>
</html>
""")
    
    cursor.close()
    conn.close()
    
    print(f"\n✅ Created fact sheet: {summary_file}")
    print("\n📊 SUMMARY OF FINDINGS:")
    if all_findings['loan_amounts']:
        print(f"   Loan Amount: ${int(max(all_findings['loan_amounts'], key=lambda x: int(x))):,}")
    if all_findings['interest_rates']:
        print(f"   Interest Rate: {sorted(all_findings['interest_rates'])[0]}")
    if all_findings['payment_amounts']:
        print(f"   Monthly Payment: ${int(max(all_findings['payment_amounts'], key=lambda x: int(x))):,}")
    if all_findings['credit_scores']:
        print(f"   Credit Score: {max(all_findings['credit_scores'])}")
    
    # Try to open in browser
    try:
        import webbrowser
        webbrowser.open(summary_file)
    except:
        print(f"\n📂 Please open: {summary_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        loan_number = sys.argv[1]
    else:
        loan_number = input("Enter loan number (default 1225290972): ") or "1225290972"
    
    create_underwriter_summary(loan_number)