# Deployment Split Guide - RTX 4090 vs s01vpsromuls001

## What Goes Where

### On RTX 4090 (Backend Processing & APIs)
These files run on your RTX 4090:
- `process_three_users_june.py` - Batch processing recordings
- `loan_search_api.py` - Search API (port 8000)
- `loan_timeline_api.py` - Timeline API (port 8001)
- `scream_hybrid_pipeline.py` - Core pipeline
- All transcription/summary generation scripts
- Whisper and Gemma models

### On s01vpsromuls001 (Frontend)
These files go on the RHEL8 server:
- `loan_timeline_react.tsx` - React component
- TypeScript interfaces (from API `/typescript/interfaces`)
- Your existing React/Vite app

## Setup Instructions

### Step 1: On s01vpsromuls001 (RHEL8)

```bash
# Navigate to your React app directory
cd /moneyball/your-react-app  # Replace with actual path

# Pull the React component
cd /moneyball/whisper-rtx-deployment
git pull

# Copy React component to your app
cp loan_timeline_react.tsx /moneyball/your-react-app/src/components/

# Install required npm packages
cd /moneyball/your-react-app
npm install axios date-fns
```

### Step 2: Get TypeScript Interfaces

First, start the API on RTX 4090:
```bash
python loan_search_api.py
```

Then on s01vpsromuls001, fetch the interfaces:
```bash
# Get TypeScript interfaces from the API
curl http://[RTX-IP]:8000/typescript/interfaces > interfaces.ts

# Or manually copy from the API response
```

### Step 3: Configure API Endpoints

In your React app's `.env` file:
```env
VITE_API_URL=http://[RTX-IP]:8000
VITE_TIMELINE_API_URL=http://[RTX-IP]:8001
```

Or hardcode in your component:
```typescript
const API_BASE = 'http://[RTX-IP]:8000';
const TIMELINE_API = 'http://[RTX-IP]:8001';
```

### Step 4: Import Component in Your App

In your React app:
```typescript
import { LoanTimelineView } from './components/loan_timeline_react';

function App() {
  return (
    <div>
      <LoanTimelineView />
    </div>
  );
}
```

## Network Considerations

Since s01vpsromuls001 is on the corporate network and can reach the RTX 4090:

1. **Direct Connection**: 
   - React app on s01vpsromuls001 → APIs on RTX 4090
   - No proxy needed if both are on same network

2. **CORS is Enabled**:
   - APIs already configured to accept requests from any origin
   - Should work with s01vpsromuls001

3. **Firewall**:
   - Ensure ports 8000 and 8001 are accessible from s01vpsromuls001
   - Test with: `curl http://[RTX-IP]:8000` from RHEL8

## Quick Test

On s01vpsromuls001, test API connectivity:
```bash
# Test search API
curl http://[RTX-IP]:8000/

# Test timeline API  
curl http://[RTX-IP]:8001/

# Test loan search (replace with actual loan number)
curl http://[RTX-IP]:8001/timeline/12345678
```

## File Summary

**Only React component needed on s01vpsromuls001:**
- `loan_timeline_react.tsx` - The UI component
- TypeScript interfaces (from API endpoint)
- Dependencies: axios, date-fns

**Everything else stays on RTX 4090:**
- All Python scripts
- Database connections
- Whisper/Gemma models
- APIs serving data

This way s01vpsromuls001 just handles the UI while RTX 4090 does all the heavy processing!