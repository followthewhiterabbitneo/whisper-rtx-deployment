#!/usr/bin/env python3
"""
Update the SCREAM pipeline to populate loan_number_index
This makes loan numbers immediately searchable
"""

# Add this function to scream_hybrid_pipeline.py after save_to_database()

def update_loan_index(self, orkuid, loan_numbers, call_info):
    """Update the loan number search index"""
    if not loan_numbers:
        return
        
    try:
        # Extract user name from parties
        user_name = None
        firstname = None
        lastname = None
        
        # Try to extract from call_info
        if 'localParty' in call_info and not call_info['localParty'].startswith('+'):
            user_name = call_info['localParty']
        elif 'remoteParty' in call_info and not call_info['remoteParty'].startswith('+'):
            user_name = call_info['remoteParty']
        
        # Try to parse name
        if user_name and ' ' in user_name:
            parts = user_name.split(' ', 1)
            firstname = parts[0]
            lastname = parts[1]
        
        # Insert each loan number
        for loan_number in loan_numbers:
            self.cursor.execute("""
                INSERT IGNORE INTO loan_number_index
                (loan_number, orkuid, user_name, user_firstname, user_lastname,
                 call_date, call_timestamp, duration)
                VALUES (%s, %s, %s, %s, %s, DATE(%s), %s, %s)
            """, (
                loan_number,
                orkuid,
                user_name,
                firstname,
                lastname,
                call_info.get('timestamp'),
                call_info.get('timestamp'),
                call_info.get('duration', 0)
            ))
        
        # Update user loan mapping
        if user_name and loan_numbers:
            # Get all loan numbers for this user
            self.cursor.execute("""
                SELECT DISTINCT loan_number 
                FROM loan_number_index 
                WHERE user_name = %s
            """, (user_name,))
            
            all_loans = [row['loan_number'] for row in self.cursor.fetchall()]
            
            # Update or insert user mapping
            self.cursor.execute("""
                INSERT INTO user_loan_mapping 
                (user_name, user_firstname, user_lastname, primary_loan_number, 
                 all_loan_numbers, total_calls, first_call_date, last_call_date)
                VALUES (%s, %s, %s, %s, %s, 1, DATE(%s), DATE(%s))
                ON DUPLICATE KEY UPDATE
                    all_loan_numbers = %s,
                    total_calls = total_calls + 1,
                    last_call_date = DATE(%s),
                    updated_at = CURRENT_TIMESTAMP
            """, (
                user_name,
                firstname,
                lastname,
                loan_numbers[0],  # Primary loan
                json.dumps(all_loans),
                call_info.get('timestamp'),
                call_info.get('timestamp'),
                json.dumps(all_loans),
                call_info.get('timestamp')
            ))
        
        self.db_conn.commit()
        print("   ✓ Loan index updated")
        
    except Exception as e:
        print(f"   ⚠️  Failed to update loan index: {e}")


# Example React component for searching loans

REACT_EXAMPLE = """
// Example React component using the Loan Search API
// Save as: LoanSearch.tsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';  // Change to your API server

interface LoanSearchResult {
  loan_number: string;
  orkuid: string;
  user_name?: string;
  call_date: string;
  call_timestamp: string;
  duration: number;
  summary?: string;
}

export const LoanSearch: React.FC = () => {
  const [loanNumber, setLoanNumber] = useState('');
  const [results, setResults] = useState<LoanSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const searchLoan = async () => {
    if (!loanNumber.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(`${API_BASE}/search/loan/${loanNumber}`);
      setResults(response.data);
    } catch (err) {
      setError('Failed to search loan number');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="loan-search">
      <h2>Loan Number Search</h2>
      
      <div className="search-box">
        <input
          type="text"
          value={loanNumber}
          onChange={(e) => setLoanNumber(e.target.value)}
          placeholder="Enter loan number..."
          onKeyPress={(e) => e.key === 'Enter' && searchLoan()}
        />
        <button onClick={searchLoan} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      
      {error && <div className="error">{error}</div>}
      
      {results.length > 0 && (
        <div className="results">
          <h3>Found {results.length} calls with loan #{loanNumber}</h3>
          
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>User</th>
                <th>Duration</th>
                <th>Summary</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {results.map((result) => (
                <tr key={result.orkuid}>
                  <td>{new Date(result.call_timestamp).toLocaleDateString()}</td>
                  <td>{result.user_name || 'Unknown'}</td>
                  <td>{Math.floor(result.duration / 60)}m</td>
                  <td>{result.summary?.substring(0, 100)}...</td>
                  <td>
                    <a href={`/calls/${result.orkuid}`}>View</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
"""

print("=" * 80)
print("LOAN INDEX INTEGRATION GUIDE")
print("=" * 80)

print("""
1. ADD TO SCREAM PIPELINE:
   - Copy the update_loan_index() function above
   - Add to scream_hybrid_pipeline.py
   - Call after save_to_database()

2. RUN THE API SERVER:
   python loan_search_api.py

3. REACT FRONTEND SETUP:
   - Install axios: npm install axios
   - Copy TypeScript interfaces from http://localhost:8000/typescript/interfaces
   - Use the example component above as a starting point

4. NGINX CONFIGURATION (for s01vpsromuls001):
   location /api/ {
       proxy_pass http://localhost:8000/;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection 'upgrade';
       proxy_set_header Host $host;
       proxy_cache_bypass $http_upgrade;
   }

5. PERFORMANCE OPTIMIZATION:
   - Loan numbers are indexed for fast lookup
   - User mappings are pre-calculated
   - API responses can be cached
   - Consider pagination for large result sets
""")

print("\n" + "=" * 80)
print("The system is designed for efficient loan number searching!")
print("=" * 80)