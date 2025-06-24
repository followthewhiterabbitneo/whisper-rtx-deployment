"""
Loan Call Feedback Component
Allows users to verify if calls are actually loan-related
"""

def generate_feedback_html(orkuid, detected_loan_number=None):
    """Generate HTML for feedback buttons"""
    
    html = f"""
    <div class="loan-feedback" data-orkuid="{orkuid}">
        <div class="detected-info">
            {f'<span>Detected Loan: <strong>{detected_loan_number}</strong></span>' if detected_loan_number else '<span>No loan number detected</span>'}
        </div>
        
        <div class="feedback-buttons">
            <!-- Thumbs up - This IS about this loan -->
            <button class="btn-feedback thumbs-up" onclick="submitFeedback('{orkuid}', 'confirmed', '{detected_loan_number}')">
                👍 Correct
            </button>
            
            <!-- Thumbs down - NOT about loans -->
            <button class="btn-feedback thumbs-down" onclick="submitFeedback('{orkuid}', 'irrelevant')">
                👎 Not loan related
            </button>
            
            <!-- Wrong loan number -->
            <button class="btn-feedback wrong-loan" onclick="showLoanInput('{orkuid}')">
                ✏️ Different loan
            </button>
        </div>
        
        <!-- Hidden input for loan number correction -->
        <div id="loan-input-{orkuid}" class="loan-input-section" style="display:none;">
            <input type="text" 
                   id="loan-number-{orkuid}" 
                   placeholder="Enter correct loan number (8 digits)"
                   maxlength="8"
                   pattern="[0-9]{8}">
            <button onclick="submitCorrectedLoan('{orkuid}')">Submit</button>
            <button onclick="hideLoanInput('{orkuid}')">Cancel</button>
        </div>
    </div>
    
    <style>
    .loan-feedback {
        border: 1px solid #ddd;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    .feedback-buttons {
        margin-top: 10px;
        display: flex;
        gap: 10px;
    }
    
    .btn-feedback {
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
    }
    
    .thumbs-up:hover { background: #4CAF50; color: white; }
    .thumbs-down:hover { background: #f44336; color: white; }
    .wrong-loan:hover { background: #ff9800; color: white; }
    
    .loan-input-section {
        margin-top: 10px;
        padding: 10px;
        background: #f5f5f5;
        border-radius: 4px;
    }
    </style>
    """
    
    return html

def generate_feedback_javascript():
    """JavaScript for handling feedback"""
    
    js = """
    <script>
    function submitFeedback(orkuid, feedbackType, loanNumber) {
        fetch('/api/loan-feedback', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                orkuid: orkuid,
                feedback_type: feedbackType,
                loan_number: loanNumber || null
            })
        })
        .then(response => response.json())
        .then(data => {
            // Update UI to show feedback submitted
            document.querySelector(`[data-orkuid="${orkuid}"]`).innerHTML = 
                '<div style="color: green;">✓ Feedback saved!</div>';
        });
    }
    
    function showLoanInput(orkuid) {
        document.getElementById(`loan-input-${orkuid}`).style.display = 'block';
    }
    
    function hideLoanInput(orkuid) {
        document.getElementById(`loan-input-${orkuid}`).style.display = 'none';
    }
    
    function submitCorrectedLoan(orkuid) {
        const loanNumber = document.getElementById(`loan-number-${orkuid}`).value;
        if (loanNumber.length === 8 && /^\d+$/.test(loanNumber)) {
            submitFeedback(orkuid, 'corrected', loanNumber);
        } else {
            alert('Please enter a valid 8-digit loan number');
        }
    }
    </script>
    """
    
    return js

# Example usage in search results
def display_search_results_with_feedback(results):
    """Display search results with feedback options"""
    
    html_output = ""
    
    for result in results:
        html_output += f"""
        <div class="search-result">
            <h4>Call ID: {result['orkuid']}</h4>
            <p>Date: {result['timestamp']}</p>
            <p>Duration: {result['duration']}s</p>
            <p>Parties: {result['localParty']} ↔ {result['remoteParty']}</p>
            
            {generate_feedback_html(result['orkuid'], result.get('loan_number'))}
        </div>
        """
    
    return html_output + generate_feedback_javascript()