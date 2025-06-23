# Loan Timeline Viewer System

A comprehensive system for viewing, analyzing, and summarizing loan call histories.

## 🚀 Quick Start

1. **Start the APIs** (in separate terminals):
   ```bash
   # Terminal 1
   python loan_search_api.py
   
   # Terminal 2
   python loan_timeline_api.py
   ```

2. **Launch the viewer**:
   ```bash
   python launch_loan_viewer.py
   ```

3. **Or open directly**:
   - Open `enhanced_loan_viewer.html` in your browser
   - Enter loan number (e.g., 1225290972)
   - Click "Search Timeline"

## 📁 Files Overview

### Core APIs
- `loan_search_api.py` - REST API for searching loans (port 8000)
- `loan_timeline_api.py` - REST API for timeline data (port 8001)

### Viewers
- `enhanced_loan_viewer.html` - Full-featured timeline viewer with insights
- `view_loan_now.html` - Basic timeline viewer
- `launch_loan_viewer.py` - Easy launcher with menu

### Summary Generation
- `summarize_loan_story.py` - Basic summary generator
- `auto_generate_summary.py` - Enhanced summary with sentiment analysis
- `get_loan_transcripts.py` - Extract all transcripts for a loan

### Utilities
- `open_transcripts.py` - Create batch file to open all transcripts
- `setup_react_rtx.md` - Instructions for React setup

## 🎯 Features

### Enhanced Loan Viewer
- **Real-time Search**: Search any loan number instantly
- **Timeline View**: See all calls in chronological order
- **Sentiment Analysis**: Track positive/negative/neutral trends
- **Key Milestones**: Automatically identified turning points
- **AI Insights**: Risk indicators and action items
- **Export Options**: CSV export for reporting
- **Summary Generation**: One-click comprehensive summaries

### Timeline API Features
- Complete call history aggregation
- Sentiment trend analysis
- Key milestone extraction
- User participation tracking
- Duration and frequency statistics

## 📊 Example Loan: 1225290972

This loan has 12 calls involving:
- Jonathan Boatright
- Raghava Nyapathy
- Russell Barratt
- Celina Krall

## 🔧 Configuration

### Database Connection
Edit `DB_CONFIG` in any Python file:
```python
DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka'
}
```

### Transcript Paths
Transcripts are expected at:
```
C:\transcripts\YYYY\MM\DD\{orkuid}.txt
```

## 🎨 UI Features

### Enhanced Viewer
- Modern, responsive design
- Real-time API status indicator
- Interactive timeline with expandable details
- Sentiment visualization
- One-click actions (summary, export, insights)

### Summary Reports
- Executive overview with statistics
- Sentiment progression charts
- Timeline with key points
- Participant analysis
- Print-friendly formatting

## 💡 Tips

1. **Performance**: APIs cache data for faster subsequent loads
2. **Batch Operations**: Use launcher script for multiple tasks
3. **Transcripts**: Click "Copy Path" to get Windows file paths
4. **Summaries**: Enhanced summaries auto-open in browser

## 🐛 Troubleshooting

### APIs Not Connecting
- Ensure both APIs are running (ports 8000, 8001)
- Check Windows Firewall settings
- Verify database connectivity

### Transcripts Not Found
- Check transcript path format
- Ensure files exist at expected locations
- Try both forward and backslash formats

### Summary Generation Issues
- Verify loan number exists in database
- Check that transcripts are readable
- Ensure sufficient permissions

## 📈 Next Steps

1. Add more AI-powered insights
2. Implement real-time notifications
3. Add export to PDF functionality
4. Create management dashboard
5. Add voice playback integration

---

For issues or questions, check the main project README or run:
```bash
python launch_loan_viewer.py
```