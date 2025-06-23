# Quick React Setup on RTX 4090

## 1. Create React App (Terminal 5)
```bash
cd C:\Users\estillmane\.aria
npx create-react-app loan-search-ui --template typescript
cd loan-search-ui
```

## 2. Install Dependencies
```bash
npm install axios date-fns
```

## 3. Copy the React Component
Copy `loan_timeline_react.tsx` to `src/LoanTimelineView.tsx`

## 4. Update src/App.tsx
```tsx
import React from 'react';
import './App.css';

// Update the import path in LoanTimelineView.tsx first:
// const API_BASE = 'http://localhost:8001';

function App() {
  return (
    <div className="App">
      <h1>Loan Search System</h1>
      
      {/* Quick test of the API */}
      <div style={{ margin: '20px' }}>
        <h2>Test Loan: 1225290972</h2>
        <iframe 
          src="http://localhost:8001/timeline/1225290972"
          style={{ width: '100%', height: '600px', border: '1px solid #ccc' }}
        />
      </div>
      
      {/* TODO: Add the full React component here */}
    </div>
  );
}

export default App;
```

## 5. Start the React App
```bash
npm start
```

## 6. Quick and Dirty Display
For NOW, while processing continues, you can just use the JSON directly:

1. Go to: http://localhost:8001/timeline/1225290972
2. Install JSON Viewer Chrome extension for pretty display
3. Or create a simple HTML file:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Loan Timeline</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .call { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .header { font-weight: bold; color: #333; }
        .meta { color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <h1>Loan Timeline Viewer</h1>
    <input type="text" id="loanNumber" placeholder="Enter loan number" value="1225290972">
    <button onclick="loadTimeline()">Load Timeline</button>
    
    <div id="timeline"></div>
    
    <script>
        async function loadTimeline() {
            const loanNumber = document.getElementById('loanNumber').value;
            const response = await fetch(`http://localhost:8001/timeline/${loanNumber}`);
            const data = await response.json();
            
            let html = `<h2>Loan #${data.loan_number}</h2>`;
            html += `<p>Total Calls: ${data.total_calls} | Duration: ${data.total_duration_minutes} minutes</p>`;
            html += `<p>Primary User: ${data.primary_user}</p>`;
            
            html += '<h3>Timeline:</h3>';
            data.timeline_events.forEach(event => {
                const date = new Date(event.timestamp).toLocaleString();
                html += `
                    <div class="call">
                        <div class="header">${date} - ${event.user_name}</div>
                        <div class="meta">${Math.floor(event.duration/60)} minutes | ${event.sentiment}</div>
                        <div>Recording: ${event.orkuid}</div>
                    </div>
                `;
            });
            
            document.getElementById('timeline').innerHTML = html;
        }
        
        // Load on page load
        loadTimeline();
    </script>
</body>
</html>
```

Save as `loan_viewer.html` and open in browser!