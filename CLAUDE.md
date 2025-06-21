# CLAUDE.md - Project Context

## Current Project: Whisper RTX Deployment

I'm working on deploying OpenAI Whisper (large-v3-turbo) on my RTX 4090 Windows workstation for high-speed audio transcription.

### Quick Context for Claude
- **Development**: WSL2 Ubuntu at /home/ecsti
- **Deployment**: Windows 11 RTX 4090 at C:\Users\estillmane\.aria\whisper-rtx-deployment
- **GitHub**: https://github.com/followthewhiterabbitneo/whisper-rtx-deployment
- **Current Focus**: Batch transcribing audio files in wav/ folder using turbo model
- **Key Achievement**: 10-20x real-time transcription speed on RTX 4090

### System Configuration
- **GPU**: NVIDIA GeForce RTX 4090 (24GB VRAM)
- **OS**: Windows 11
- **Python**: 3.11.0
- **CUDA**: 12.9
- **Location**: C:\Users\estillmane\.aria\whisper-rtx-deployment

### Installed Components
- faster-whisper 1.1.1
- PyTorch 2.5.1+cu121
- Transformers 4.52.4
- FFmpeg 7.1 (via Chocolatey)
- Whisper large-v3-turbo model from Kaggle

### Project Structure
```
whisper-rtx-deployment/
├── models/
│   └── faster-whisper-large-v3-turbo-ct2/  # Turbo model files
├── wav/                                     # Input audio files
├── transcriptions/                          # Output transcriptions
├── downloads/                               # Kaggle downloads
└── *.py                                     # Various scripts
```

### Key Scripts
- `use_kaggle_whisper_turbo.py` - Main transcription script
- `transcribe_wav_folder_fixed.py` - Batch transcription for wav/ folder
- `fix_model_names.py` - Fix files with (1) suffix from downloads
- `rtx_4090_recon.py` - System reconnaissance
- `check_audio_deps.py` - Check audio dependencies
- `rtx_project_inventory.py` - Analyze project structure and identify cleanup opportunities
- `rtx_cleanup_helper.py` - Safely remove unnecessary files with dry-run mode

### Workflow
1. **GitHub Repo**: https://github.com/followthewhiterabbitneo/whisper-rtx-deployment
   - **SSH Remote**: git@github.com:followthewhiterabbitneo/whisper-rtx-deployment.git (required for pushing)
2. **Kaggle Dataset**: whisper-rtx-deployment (for sharing results and files between WSL2 and RTX)
3. **Model Source**: deepdml/faster-whisper-large-v3-turbo-ct2 on Kaggle

### Current Status
- ✅ Whisper turbo model installed and working
- ✅ Can transcribe audio at 10-20x real-time speed on RTX 4090
- ✅ Batch transcription script ready for wav/ folder
- 🔄 Using Kaggle as bridge to share files (can't push to GitHub from RTX)

### Common Commands
```bash
# Update from GitHub
git pull

# Transcribe single file
python use_kaggle_whisper_turbo.py audio.wav

# Batch transcribe wav/ folder
python transcribe_wav_folder_fixed.py

# Upload results to Kaggle
python upload_recon_to_kaggle.py
```

### Notes
- Using int8_float16 compute type for optimal turbo performance
- Network is restricted on RTX workstation (no external connections)
- All file sharing done via Kaggle datasets
- WSL2 Ubuntu used for development, Windows 11 RTX for deployment

### Recent Progress
- ✅ Successfully set up Whisper large-v3-turbo model from Kaggle
- ✅ Fixed duplicate file detection issue on Windows (case-insensitive)
- ✅ Created batch transcription script for wav/ folder
- ✅ Established Kaggle-based workflow for file sharing
- 🔄 Currently transcribing audio files at 10-20x real-time speed

### Next Steps
1. Run batch transcription on any pending audio files in wav/
2. Upload transcription results to Kaggle dataset
3. Consider adding post-processing or formatting options
4. Potentially integrate with downstream systems

### Deployment Checkpoints

#### ✅ MILESTONE ACHIEVED - June 21, 2025 at 17:14
Successfully transcribed first recording (Eric Rawlins) using first principles approach!

**What's Working:**
1. **SSH Access**: estillmane@s40vpsoxweb002 (passwordless)
2. **File Location**: /var/log/orkaudio.prod.nfs/audio/2025/06/20/14/20250620_145645_LOLW.wav
3. **File Transfer**: SCP copy to temp directory
4. **Transcription**: Whisper large-v3-turbo on RTX 4090
5. **Output**: Full transcript saved to test_output/

**Exact Commands to Reproduce:**
```bash
# 1. Pull latest code
git pull

# 2. Test SSH connection
python test_ssh_connection.py

# 3. Find the specific file
python quick_file_check.py

# 4. Process the recording
python process_one_recording.py
# This copies 20250620_145645_LOLW.wav and transcribes it
# Output: test_output/20250620_145645_LOLW.wav.txt
```

**Current State:**
- Can process individual recordings via SSH copy
- No database integration yet (not needed for basic transcription)
- No NFS mount required
- Model loaded successfully: models/faster-whisper-large-v3-turbo-ct2
- Processing speed confirmed: 10-20x real-time

**Next Steps to Continue:**
1. To process different file: Edit TARGET_FILE in process_one_recording.py
2. To add database: Run test_single_recording.py (includes DB query)
3. To batch process: Implement loop in scream_ssh_source.py
4. To add summaries: Extend process_one_recording.py with summary generation

**Key Configuration:**
- SSH User: estillmane
- SSH Host: s40vpsoxweb002  
- Remote Path: /var/log/orkaudio.prod.nfs
- DB Tunnel: localhost:33306 -> s40vpsoxweb002:3306
- DB Creds: root/admin @ oreka database