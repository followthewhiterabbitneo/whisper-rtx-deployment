# Windsurf Local MCP + Gemma Setup

## The Architecture
Everything runs on your work laptop - no external connections needed!

```
Windsurf Claude
    ↓ (local MCP connection)
Local MCP Server (Python)
    ├→ Oreka DB (internal network)
    └→ Local Gemma (for analysis)
```

## Step 1: Create Local MCP Server

```python
# local_mcp_server.py
import json
import sys
import pymysql
import subprocess
from datetime import datetime

class LocalMCPServer:
    def __init__(self):
        self.db_config = {
            'host': 'your-dev-server',  # Internal network
            'user': 'root',
            'password': 'admin',
            'database': 'oreka'
        }
        
        # Gemma model path (after you download it)
        self.gemma_path = "C:/Users/YourName/models/gemma-2b"
    
    def list_tools(self):
        return {
            'tools': [
                {
                    'name': 'search_calls',
                    'description': 'Search Oreka recordings',
                    'parameters': {
                        'query': {'type': 'string'},
                        'hours_back': {'type': 'integer', 'default': 24}
                    }
                },
                {
                    'name': 'analyze_call',
                    'description': 'Analyze call with local Gemma model',
                    'parameters': {
                        'orkuid': {'type': 'string'},
                        'prompt': {'type': 'string', 'default': 'Summarize this call'}
                    }
                },
                {
                    'name': 'batch_analyze',
                    'description': 'Run Gemma analysis on multiple calls',
                    'parameters': {
                        'call_ids': {'type': 'array'},
                        'analysis_type': {
                            'type': 'string',
                            'enum': ['summary', 'sentiment', 'issues', 'compliance']
                        }
                    }
                }
            ]
        }
    
    def search_calls(self, query, hours_back=24):
        # Your existing DB search logic
        conn = pymysql.connect(**self.db_config)
        # ... query logic ...
        return results
    
    def analyze_call(self, orkuid, prompt="Summarize this call"):
        # Get call transcript from DB
        transcript = self.get_transcript(orkuid)
        
        # Run through local Gemma
        result = self.run_gemma(f"{prompt}: {transcript}")
        
        return {
            'orkuid': orkuid,
            'analysis': result,
            'model': 'gemma-2b-local'
        }
    
    def run_gemma(self, prompt):
        # Run Gemma locally (example with llama.cpp or similar)
        cmd = [
            'python', 'run_gemma.py',
            '--model', self.gemma_path,
            '--prompt', prompt
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
```

## Step 2: Download Gemma (or any small model)

```python
# download_gemma.py
import requests
import os

def download_gemma():
    # Option 1: Hugging Face (if accessible)
    # Option 2: Download on home laptop, transfer via USB
    # Option 3: Use ollama if it works internally
    
    model_dir = "C:/Users/YourName/models/gemma-2b"
    os.makedirs(model_dir, exist_ok=True)
    
    # Download model files...
    print(f"Model ready at: {model_dir}")
```

## Step 3: Configure Windsurf

In Windsurf, configure Claude to use your local MCP server:

```bash
# If Windsurf supports MCP configuration:
claude mcp add oreka-local -- python C:/path/to/local_mcp_server.py
```

## Step 4: Use It!

Now in Windsurf with Claude:
- "Search for calls from angry customers today"
- "Analyze the top 5 longest calls and summarize the issues"
- "Run compliance check on all calls from agent 8001"

Everything runs locally on your work laptop!