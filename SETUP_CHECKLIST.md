# SCREAM Enterprise Setup Checklist

## Pre-Flight Check

Before running `test_single_recording.py`, ensure:

### 1. Python Dependencies
```bash
pip install pymysql faster-whisper
```

### 2. Database Access
Test connection from RTX workstation:
```bash
mysql -h s40vpsoxweb002 -u root -padmin oreka -e "SELECT COUNT(*) FROM orksegment"
```

### 3. NFS Mount
Mount the recordings directory:
```bash
# Linux/WSL
sudo mkdir -p /var/log/orkaudio.nfs.prod
sudo mount -t nfs -o ro s40vpsoxweb002:/var/log/orkaudio.nfs.prod /var/log/orkaudio.nfs.prod

# Windows (if running on RTX directly)
# Map network drive to \\s40vpsoxweb002\orkaudio.nfs.prod
```

### 4. Model Files
Ensure Whisper model is downloaded:
```bash
# Check if model exists
ls -la models/faster-whisper-large-v3-turbo-ct2/

# If not, run bootstrap
python download_model.py
```

### 5. GPU Check
```bash
nvidia-smi
# Should show RTX 4090 with available memory
```

## Running the Test

```bash
python test_single_recording.py
```

## Expected Output

```
==============================================================
SCREAM Single Recording Test
==============================================================

1. DATABASE CONNECTION
------------------------------
✓ PyMySQL available
  Host: s40vpsoxweb002
  Database: oreka
  User: root
✓ Connected to database

2. FINDING A TEST RECORDING
------------------------------
✓ Found recording:
  ID: 20250121_143052_7823
  Date: 2025-01-21 14:30:52
  Duration: 514 seconds
  Local: 3135551234
  Remote: 2485559876
  File: /audio/2025/01/21/14/20250121_143052_7823.wav

3. FILE ACCESS CHECK
------------------------------
  Full path: /var/log/orkaudio.nfs.prod/audio/2025/01/21/14/20250121_143052_7823.wav
✓ File accessible: 8,224,044 bytes

[... continues with transcription ...]
```

## Troubleshooting

### Database Connection Failed
- Check firewall between RTX and s40vpsoxweb002
- Verify MariaDB is listening on port 3306
- Test with telnet: `telnet s40vpsoxweb002 3306`

### NFS Mount Failed
- Check if NFS service is running on s40vpsoxweb002
- Verify export permissions: `showmount -e s40vpsoxweb002`
- Try manual mount with verbose: `mount -v -t nfs ...`

### File Not Found
- Verify the path structure in the database matches NFS mount
- Check if recording exists: `ls -la /var/log/orkaudio.nfs.prod/audio/2025/`
- Ensure mount is read-only but accessible

### GPU/CUDA Issues
- Verify CUDA is installed: `nvcc --version`
- Check PyTorch CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
- Ensure faster-whisper has CUDA support

## Next Steps

Once test succeeds:
1. Create read-only database user
2. Implement full MariaDB source for SCREAM
3. Add legal-brief summary formatting
4. Set up batch processing