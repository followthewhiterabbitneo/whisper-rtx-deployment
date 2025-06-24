"""
API endpoint for processing loan feedback
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymysql
from datetime import datetime

app = FastAPI()

class LoanFeedback(BaseModel):
    orkuid: str
    feedback_type: str  # 'confirmed', 'irrelevant', 'corrected'
    loan_number: str = None
    user_id: str = "default_user"

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

@app.post("/api/loan-feedback")
async def submit_feedback(feedback: LoanFeedback):
    """Process user feedback on loan relevance"""
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Insert feedback
        if feedback.feedback_type == 'confirmed':
            cursor.execute("""
                INSERT INTO loan_call_feedback 
                (orkuid, loan_number, is_relevant, feedback_type, user_id)
                VALUES (%s, %s, TRUE, %s, %s)
                ON DUPLICATE KEY UPDATE
                is_relevant = TRUE,
                feedback_type = %s,
                created_at = NOW()
            """, (feedback.orkuid, feedback.loan_number, feedback.feedback_type, 
                  feedback.user_id, feedback.feedback_type))
                  
        elif feedback.feedback_type == 'irrelevant':
            cursor.execute("""
                INSERT INTO loan_call_feedback 
                (orkuid, is_relevant, feedback_type, user_id)
                VALUES (%s, FALSE, %s, %s)
                ON DUPLICATE KEY UPDATE
                is_relevant = FALSE,
                feedback_type = %s,
                created_at = NOW()
            """, (feedback.orkuid, feedback.feedback_type, feedback.user_id, 
                  feedback.feedback_type))
                  
        elif feedback.feedback_type == 'corrected':
            cursor.execute("""
                INSERT INTO loan_call_feedback 
                (orkuid, corrected_loan_number, is_relevant, feedback_type, user_id)
                VALUES (%s, %s, TRUE, %s, %s)
                ON DUPLICATE KEY UPDATE
                corrected_loan_number = %s,
                is_relevant = TRUE,
                feedback_type = %s,
                created_at = NOW()
            """, (feedback.orkuid, feedback.loan_number, feedback.feedback_type, 
                  feedback.user_id, feedback.loan_number, feedback.feedback_type))
        
        # Update loan officer accuracy if it's marked irrelevant
        if feedback.feedback_type == 'irrelevant':
            cursor.execute("""
                UPDATE loan_officer_accuracy loa
                JOIN orktape t ON t.orkUid = %s
                SET loa.irrelevant_calls = loa.irrelevant_calls + 1,
                    loa.total_calls = loa.total_calls + 1,
                    loa.accuracy_rate = (loa.relevant_calls / loa.total_calls) * 100
                WHERE loa.phone_number IN (t.localParty, t.remoteParty)
            """, (feedback.orkuid,))
        
        conn.commit()
        
        return {"status": "success", "message": "Feedback recorded"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/loan-accuracy/{phone_number}")
async def get_loan_officer_accuracy(phone_number: str):
    """Get accuracy stats for a loan officer"""
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("""
        SELECT * FROM loan_officer_accuracy
        WHERE phone_number = %s
    """, (phone_number,))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        return result
    else:
        return {"phone_number": phone_number, "accuracy_rate": "No data yet"}

# Query to use feedback in searches
def get_verified_loan_calls(loan_number):
    """Get calls verified to be about a specific loan"""
    
    query = """
    SELECT 
        t.*,
        lf.is_relevant,
        lf.feedback_type,
        COALESCE(lf.corrected_loan_number, ct.loan_numbers) as verified_loan_number
    FROM orktape t
    LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
    LEFT JOIN loan_call_feedback lf ON t.orkUid = lf.orkuid
    WHERE 
        (ct.loan_numbers LIKE %s OR lf.corrected_loan_number = %s)
        AND (lf.is_relevant IS NULL OR lf.is_relevant = TRUE)
    ORDER BY t.timestamp DESC
    """
    
    return query