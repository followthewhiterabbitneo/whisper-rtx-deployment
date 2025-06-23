#!/usr/bin/env python3
"""
FastAPI server for loan number search
Designed for React/Vite/TypeScript frontend
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import pymysql
import json
from datetime import datetime, date
import uvicorn

app = FastAPI(title="Loan Search API", version="1.0.0")

# Enable CORS for React frontend on s01vpsromuls001
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://s01vpsromuls001:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

# Pydantic models for TypeScript generation
class LoanSearchResult(BaseModel):
    loan_number: str
    orkuid: str
    user_name: Optional[str]
    call_date: date
    call_timestamp: datetime
    duration: int
    summary: Optional[str]
    transcript_path: Optional[str]

class UserLoanSummary(BaseModel):
    user_name: str
    firstname: Optional[str]
    lastname: Optional[str]
    primary_loan_number: Optional[str]
    all_loan_numbers: List[str]
    total_calls: int
    first_call_date: Optional[date]
    last_call_date: Optional[date]

class LoanAnalytics(BaseModel):
    total_loans: int
    total_calls: int
    users_with_loans: int
    average_calls_per_loan: float
    date_range: Dict[str, str]

def get_db_connection():
    """Get database connection"""
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

@app.get("/")
def root():
    """API root"""
    return {
        "message": "Loan Search API",
        "endpoints": [
            "/docs",
            "/search/loan/{loan_number}",
            "/search/user/{user_name}",
            "/users/summary",
            "/analytics"
        ]
    }

@app.get("/search/loan/{loan_number}", response_model=List[LoanSearchResult])
def search_by_loan_number(loan_number: str):
    """Search for all calls containing a specific loan number"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            l.loan_number,
            l.orkuid,
            l.user_name,
            l.call_date,
            l.call_timestamp,
            l.duration,
            ct.summary,
            ct.transcript_path
        FROM loan_number_index l
        LEFT JOIN call_transcripts_v2 ct ON l.orkuid = ct.orkuid
        WHERE l.loan_number = %s
        ORDER BY l.call_timestamp DESC
        """
        
        cursor.execute(query, (loan_number,))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/user/{user_name}", response_model=UserLoanSummary)
def search_by_user(user_name: str):
    """Get loan summary for a specific user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Try exact match first
        cursor.execute("""
            SELECT * FROM user_loan_mapping
            WHERE user_name = %s
        """, (user_name,))
        
        result = cursor.fetchone()
        
        if not result:
            # Try fuzzy match
            cursor.execute("""
                SELECT * FROM user_loan_mapping
                WHERE user_name LIKE %s
                OR CONCAT(user_firstname, ' ', user_lastname) LIKE %s
                LIMIT 1
            """, (f'%{user_name}%', f'%{user_name}%'))
            result = cursor.fetchone()
        
        if result:
            # Parse all_loan_numbers JSON
            if result['all_loan_numbers']:
                try:
                    result['all_loan_numbers'] = json.loads(result['all_loan_numbers'])
                except:
                    result['all_loan_numbers'] = []
            else:
                result['all_loan_numbers'] = []
                
            cursor.close()
            conn.close()
            return result
        else:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/summary", response_model=List[UserLoanSummary])
def get_all_users_summary(
    firstname: Optional[str] = Query(None, description="Filter by first name"),
    lastname: Optional[str] = Query(None, description="Filter by last name"),
    limit: int = Query(100, description="Limit results")
):
    """Get loan summary for all users or filtered users"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            u.*,
            COUNT(DISTINCT l.orkuid) as call_count
        FROM user_loan_mapping u
        LEFT JOIN loan_number_index l ON u.user_name = l.user_name
        WHERE 1=1
        """
        params = []
        
        if firstname:
            query += " AND u.user_firstname LIKE %s"
            params.append(f'%{firstname}%')
            
        if lastname:
            query += " AND u.user_lastname LIKE %s"
            params.append(f'%{lastname}%')
            
        query += " GROUP BY u.id ORDER BY u.total_calls DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Parse JSON fields
        for result in results:
            if result['all_loan_numbers']:
                try:
                    result['all_loan_numbers'] = json.loads(result['all_loan_numbers'])
                except:
                    result['all_loan_numbers'] = []
            else:
                result['all_loan_numbers'] = []
        
        cursor.close()
        conn.close()
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics", response_model=LoanAnalytics)
def get_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Get loan analytics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build date filter
        date_filter = ""
        params = []
        
        if start_date:
            date_filter += " AND call_date >= %s"
            params.append(start_date)
        if end_date:
            date_filter += " AND call_date <= %s"
            params.append(end_date)
        
        # Get analytics
        query = f"""
        SELECT 
            COUNT(DISTINCT loan_number) as total_loans,
            COUNT(DISTINCT orkuid) as total_calls,
            COUNT(DISTINCT user_name) as users_with_loans,
            MIN(call_date) as min_date,
            MAX(call_date) as max_date
        FROM loan_number_index
        WHERE 1=1 {date_filter}
        """
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        # Calculate average
        avg_calls = result['total_calls'] / result['total_loans'] if result['total_loans'] > 0 else 0
        
        analytics = {
            "total_loans": result['total_loans'],
            "total_calls": result['total_calls'],
            "users_with_loans": result['users_with_loans'],
            "average_calls_per_loan": round(avg_calls, 2),
            "date_range": {
                "start": str(result['min_date']) if result['min_date'] else None,
                "end": str(result['max_date']) if result['max_date'] else None
            }
        }
        
        cursor.close()
        conn.close()
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calls/{orkuid}")
def get_call_details(orkuid: str):
    """Get detailed information about a specific call"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get call details
        cursor.execute("""
            SELECT 
                t.orkUid as orkuid,
                t.filename,
                t.localParty,
                t.remoteParty,
                t.duration,
                t.timestamp,
                ct.summary,
                ct.loan_numbers,
                ct.key_facts,
                ct.sentiment,
                ct.transcript_path
            FROM orktape t
            LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
            WHERE t.orkUid = %s
        """, (orkuid,))
        
        result = cursor.fetchone()
        
        if result:
            # Parse JSON fields
            for field in ['loan_numbers', 'key_facts']:
                if result[field]:
                    try:
                        result[field] = json.loads(result[field])
                    except:
                        result[field] = None
                        
            cursor.close()
            conn.close()
            return result
        else:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Call not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# TypeScript interface generator endpoint
@app.get("/typescript/interfaces")
def get_typescript_interfaces():
    """Generate TypeScript interfaces for the API"""
    return {
        "message": "Copy these interfaces to your React app",
        "interfaces": """
// Generated TypeScript interfaces for Loan Search API

export interface LoanSearchResult {
  loan_number: string;
  orkuid: string;
  user_name?: string;
  call_date: string;
  call_timestamp: string;
  duration: number;
  summary?: string;
  transcript_path?: string;
}

export interface UserLoanSummary {
  user_name: string;
  firstname?: string;
  lastname?: string;
  primary_loan_number?: string;
  all_loan_numbers: string[];
  total_calls: number;
  first_call_date?: string;
  last_call_date?: string;
}

export interface LoanAnalytics {
  total_loans: number;
  total_calls: number;
  users_with_loans: number;
  average_calls_per_loan: number;
  date_range: {
    start?: string;
    end?: string;
  };
}

export interface CallDetails {
  orkuid: string;
  filename: string;
  localParty: string;
  remoteParty: string;
  duration: number;
  timestamp: string;
  summary?: string;
  loan_numbers?: string[];
  key_facts?: Record<string, any>;
  sentiment?: string;
  transcript_path?: string;
}
"""
    }

if __name__ == "__main__":
    print("Starting Loan Search API server...")
    print("API will be available at: http://localhost:8000")
    print("Documentation at: http://localhost:8000/docs")
    print("\nFor React development, use: http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)