# SCREAM Enterprise Integration - UWM Call Recording System

## Executive Summary

SCREAM (Speech Conversion & Recognition Engine for Audio Management) will be integrated with UWM's call recording infrastructure to provide automated transcription and summarization of underwriter calls. This system will serve as a defensive documentation tool, protecting underwriters by creating legal-brief style summaries of all calls with brokers and loan officers.

## Business Context

### Current Situation
- **Volume**: 2,745 underwriters handling 30,000 calls/day (150,000/week)
- **Problem**: Underwriters lack documentation when brokers/loan officers claim inaccurate or missing information was provided
- **Impact**: Underwriters cannot defend themselves during escalations without listening to entire calls
- **Need**: Quick-access summaries that capture who said what, key facts, and next actions

### Solution Benefits
1. **Underwriter Protection**: Legal-brief style documentation for defense
2. **Leadership Visibility**: Quick access to call facts during escalations
3. **Sentiment Tracking**: Identify positive performance and problematic interactions
4. **Time Savings**: No need to listen to full recordings during disputes

## Infrastructure Overview

### Servers and Roles

| Server | Role | Key Components |
|--------|------|----------------|
| **s40vpsoxweb002** | Database & Storage | MariaDB 5.5.68 (oreka DB), NFS mount for recordings |
| **RTX Workstation** | Processing Engine | SCREAM, Whisper model, GPU acceleration |
| **s01vpsromuls001** | Frontend | RHEL8, Preact/TypeScript/Vite application |

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          SCREAM ENTERPRISE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  s40vpsoxweb002                    RTX Workstation                            │
│  ┌─────────────────┐              ┌──────────────────────────┐               │
│  │ MariaDB 5.5.68  │              │ SCREAM Processing Engine │               │
│  │ Database: oreka │◄─────────────│                          │               │
│  │ User: readonly  │  Query calls │ 1. Query DB for calls   │               │
│  │                 │              │ 2. Read WAV from NFS     │               │
│  │ Tables:         │              │ 3. Transcribe (Whisper)  │               │
│  │ - orkuser       │              │ 4. Extract loan number   │               │
│  │ - orksegment    │              │ 5. Generate summary      │               │
│  │ - orktape       │              │ 6. Analyze sentiment     │               │
│  │ - orkmetadata   │              │ 7. Store results         │               │
│  └─────────────────┘              └──────────────────────────┘               │
│           │                                    │                              │
│           │                                    │                              │
│  ┌─────────────────┐                   ┌──────▼───────────┐                 │
│  │ NFS Mount       │                   │ Summary Storage  │                 │
│  │ /var/log/       │◄──────────────────│ - Transcripts    │                 │
│  │ orkaudio.nfs.   │   Read WAV files  │ - Summaries      │                 │
│  │ prod/           │                   │ - Sentiment      │                 │
│  │                 │                   │ - Metadata       │                 │
│  │ Structure:      │                   └──────────────────┘                 │
│  │ /audio/YYYY/    │                                                        │
│  │   MM/DD/HH/     │                   s01vpsromuls001                      │
│  │   *.wav         │                   ┌──────────────────┐                 │
│  └─────────────────┘                   │ Frontend App     │                 │
│                                        │ - Display summary│                 │
│                                        │ - Search by loan │                 │
│                                        │ - Filter by date │                 │
│                                        └──────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Database Schema

### Key Tables in oreka Database

#### orkuser
- **orkuser_id**: Primary key, links to underwriter
- **name**: Underwriter name
- **extension**: Phone extension

#### orksegment
- **orkuid**: Unique recording ID (matches filename)
- **timestamp**: Call timestamp
- **duration**: Call duration in seconds
- **localparty**: Underwriter phone number
- **remoteparty**: Broker/loan officer number
- **orkuser_id**: Foreign key to orkuser

#### orktape
- **orkuid**: Recording identifier
- **filename**: Full path to WAV file
- **filesize**: Size in bytes

#### orkmetadata
- Additional call metadata
- Custom fields for business data

### File Naming Convention
```
/audio/YYYY/MM/DD/HH/YYYYMMDD_HHMMSS_XXXX.wav

Where:
- YYYY: Year (2025)
- MM: Month (01-12)
- DD: Day (01-31)
- HH: Hour (00-23)
- HHMMSS: Time stamp
- XXXX: orkuid (unique identifier)
```

## Summary Specification

### Required Elements

```
═══════════════════════════════════════════════════════════════
                    CALL SUMMARY REPORT
═══════════════════════════════════════════════════════════════

CALL IDENTIFICATION
├─ Recording ID: 20250121_143052_7823
├─ Date/Time: January 21, 2025 2:30:52 PM
├─ Duration: 8:34
├─ Loan Number: 459782314
└─ Borrower: Smith, John & Jane

PARTICIPANTS
├─ Underwriter: Sarah Johnson (ext. 5432)
└─ Broker: Mike Wilson (555-867-5309)

KEY FACTS DISCUSSED
├─ Loan Amount: $485,000
├─ Interest Rate: 6.75%
├─ Property: 123 Maple Street, Detroit, MI 48201
├─ DTI Ratio: 42.3%
├─ LTV: 80%
└─ Loan Type: Conventional 30-year fixed

UNDERWRITER STATEMENTS
├─ [02:15] "The DTI ratio of 42.3% requires additional documentation"
├─ [03:47] "You'll need to provide bank statements for the last 60 days"
├─ [05:21] "The appraisal must be ordered within 48 hours"
└─ [07:33] "I'm approving with conditions listed in the portal"

BROKER STATEMENTS
├─ [02:45] "The borrower's bonus income should be included"
├─ [04:12] "I can have the bank statements by Friday"
├─ [05:45] "The appraisal is already scheduled for Thursday"
└─ [08:01] "I'll notify the borrower about the conditional approval"

INSTRUCTIONS GIVEN
1. Submit 60 days of bank statements by 01/26/2025
2. Order appraisal by 01/23/2025
3. Provide bonus income documentation
4. Complete conditions in portal within 5 business days

NEXT ACTIONS
├─ Broker: Upload bank statements to portal
├─ Broker: Confirm appraisal appointment
├─ Underwriter: Review submissions by 01/27/2025
└─ Follow-up call: 01/28/2025 at 10:00 AM

SENTIMENT ANALYSIS
├─ Overall: 🟢 POSITIVE
├─ Underwriter Tone: Professional, Clear, Helpful
├─ Broker Tone: Cooperative, Engaged
└─ Risk Indicators: None detected

COMPLIANCE FLAGS
└─ ✓ All required disclosures mentioned
```

### Sentiment Scoring

| Score | Indicator | Description |
|-------|-----------|-------------|
| 🟢 Green | Positive | Professional, cooperative interaction |
| 🟡 Yellow | Neutral | Standard interaction, minor friction |
| 🔴 Red | Negative | Hostile, uncooperative, or problematic |

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1-2)
1. Set up read-only database access
2. Configure NFS mount access from RTX
3. Install SCREAM on RTX workstation
4. Test connectivity and permissions

### Phase 2: Processing Pipeline (Week 3-4)
1. Create MariaDB source connector
2. Implement call filtering (≥2 minutes)
3. Set up batch processing schedule
4. Test transcription accuracy

### Phase 3: Summary Generation (Week 5-6)
1. Implement loan number extraction
2. Create legal-brief formatter
3. Add speaker separation
4. Implement sentiment analysis

### Phase 4: Storage & Access (Week 7-8)
1. Design summary storage structure
2. Create search/retrieval system
3. Build API for frontend
4. Implement data retention policy

### Phase 5: Frontend Integration (Week 9-10)
1. Create summary display components
2. Add search functionality
3. Implement filtering/sorting
4. Add export capabilities

## Technical Requirements

### SCREAM Configuration
```yaml
# scream-enterprise.yaml
source:
  type: mariadb
  host: s40vpsoxweb002
  port: 3306
  database: oreka
  user: readonly_user
  query: |
    SELECT s.*, t.filename, u.name as underwriter_name
    FROM orksegment s
    JOIN orktape t ON s.orkuid = t.orkuid
    JOIN orkuser u ON s.orkuser_id = u.orkuser_id
    WHERE s.duration >= 120
    AND s.timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
    ORDER BY s.timestamp DESC

engine:
  type: whisper
  model_path: models/faster-whisper-large-v3-turbo-ct2
  device: cuda
  compute_type: int8_float16
  language: en
  task: transcribe

processing:
  extract_loan_number: true
  generate_summary: true
  analyze_sentiment: true
  speaker_diarization: true

sink:
  type: structured
  base_path: /summaries
  format: json
  include_transcript: true
  include_audio_path: true
```

### Security Considerations

1. **Database Access**
   - Read-only user with minimal permissions
   - Encrypted connection (SSL/TLS)
   - No write access to production data

2. **File Access**
   - Read-only mount of NFS share
   - No deletion or modification of recordings
   - Audit trail of accessed files

3. **Data Privacy**
   - Summaries stored separately from recordings
   - No PII in filenames
   - Access controls on summary storage

## Monitoring & Metrics

### Key Performance Indicators
- Calls processed per hour
- Average processing time per call
- Summary generation success rate
- Sentiment distribution
- Storage utilization

### Alerts
- Processing backlog > 1 hour
- Failed transcriptions > 5%
- Database connection failures
- NFS mount unavailable

## Maintenance

### Daily Tasks
- Monitor processing queue
- Check error logs
- Verify summary quality

### Weekly Tasks
- Review sentiment trends
- Analyze processing metrics
- Clean up temporary files

### Monthly Tasks
- Archive old summaries
- Update model if needed
- Review storage capacity

## Success Criteria

1. **Processing Speed**: All calls summarized within 1 hour
2. **Accuracy**: 95%+ transcription accuracy
3. **Availability**: 99.5% uptime during business hours
4. **User Adoption**: 80% of underwriters using summaries
5. **Dispute Resolution**: 50% reduction in escalation time

## Contact Information

- **System Owner**: [To be determined]
- **Technical Lead**: [To be determined]
- **Database Admin**: [To be determined]
- **Support Team**: [To be determined]

---

*Document Version: 1.0*  
*Last Updated: January 2025*  
*Next Review: February 2025*