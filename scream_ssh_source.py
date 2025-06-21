#!/usr/bin/env python3
"""
SCREAM SSH Source - Transfers WAV files via SSH before processing
Handles the flow: Database → SSH Copy → Local Processing → Cleanup
"""

import os
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Iterator, Optional
import pymysql

from scream_engine import Source, AudioFile

logger = logging.getLogger("SCREAM.SSHSource")


class SSHFileTransfer:
    """Handles secure file transfer from remote server"""
    
    def __init__(self, ssh_user: str, ssh_host: str, remote_base: str):
        self.ssh_user = ssh_user
        self.ssh_host = ssh_host
        self.remote_base = remote_base
        self.temp_dir = Path(tempfile.mkdtemp(prefix="scream_wav_"))
        logger.info(f"Created temp directory: {self.temp_dir}")
        
    def copy_file(self, remote_path: str) -> Optional[Path]:
        """Copy a file from remote server to local temp directory"""
        # Construct full remote path
        if remote_path.startswith('/'):
            full_remote = self.remote_base + remote_path
        else:
            full_remote = os.path.join(self.remote_base, remote_path)
            
        # Local filename
        local_file = self.temp_dir / Path(remote_path).name
        
        # SCP command
        scp_cmd = [
            'scp',
            '-q',  # Quiet mode
            f'{self.ssh_user}@{self.ssh_host}:{full_remote}',
            str(local_file)
        ]
        
        try:
            logger.info(f"Copying {Path(remote_path).name} via SSH...")
            result = subprocess.run(scp_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and local_file.exists():
                file_size = local_file.stat().st_size
                logger.info(f"✓ Copied successfully: {file_size:,} bytes")
                return local_file
            else:
                logger.error(f"✗ Copy failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"✗ SCP error: {e}")
            return None
            
    def cleanup_file(self, local_path: Path):
        """Remove local copy after processing"""
        try:
            if local_path.exists():
                local_path.unlink()
                logger.debug(f"Cleaned up: {local_path.name}")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
            
    def cleanup_all(self):
        """Remove temp directory and all files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"Removed temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to remove temp directory: {e}")


class MariaDBSSHSource(Source):
    """Source that queries MariaDB and transfers files via SSH"""
    
    def __init__(self, db_config: dict, ssh_config: dict, 
                 min_duration: int = 120, hours_back: int = 24):
        self.db_config = db_config
        self.ssh_config = ssh_config
        self.min_duration = min_duration
        self.hours_back = hours_back
        self.file_transfer = SSHFileTransfer(
            ssh_config['user'],
            ssh_config['host'],
            ssh_config['remote_base']
        )
        self.processed_calls = set()
        
    def discover(self) -> Iterator[AudioFile]:
        """Query database and yield audio files"""
        
        # Get calls to process
        calls = self._query_calls()
        logger.info(f"Found {len(calls)} calls to process")
        
        for call in calls:
            # Skip if already processed
            if call['orkuid'] in self.processed_calls:
                continue
                
            # Copy file via SSH
            local_path = self.file_transfer.copy_file(call['filename'])
            
            if local_path:
                # Create AudioFile object
                audio = AudioFile(
                    path=local_path,
                    size=local_path.stat().st_size,
                    format=local_path.suffix,
                    metadata={
                        'orkuid': call['orkuid'],
                        'remote_path': call['filename'],
                        'underwriter': call.get('underwriter_name', 'Unknown'),
                        'timestamp': str(call['timestamp']),
                        'duration': call['duration'],
                        'local_party': call['localparty'],
                        'remote_party': call['remoteparty'],
                        'temp_file': True  # Mark for cleanup
                    }
                )
                
                self.processed_calls.add(call['orkuid'])
                yield audio
            else:
                logger.error(f"Failed to transfer: {call['orkuid']}")
                
    def _query_calls(self) -> list:
        """Query database for calls to process"""
        query = """
        SELECT 
            s.orkuid,
            s.timestamp,
            s.duration,
            s.localparty,
            s.remoteparty,
            s.orkuser_id,
            t.filename,
            u.name as underwriter_name
        FROM orksegment s
        INNER JOIN orktape t ON s.orkuid = t.orkuid
        LEFT JOIN orkuser u ON s.orkuser_id = u.orkuser_id
        WHERE s.duration >= %s
            AND t.filename IS NOT NULL
            AND s.timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        ORDER BY s.timestamp DESC
        LIMIT 100
        """
        
        try:
            connection = pymysql.connect(**self.db_config)
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, (self.min_duration, self.hours_back))
                results = cursor.fetchall()
            connection.close()
            return results
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return []
            
    def cleanup(self):
        """Clean up all temporary files"""
        self.file_transfer.cleanup_all()


class SSHAwareFileSink(FileSink):
    """Extended sink that cleans up temp files after processing"""
    
    def deliver(self, result):
        """Save transcription and clean up temp file"""
        # Call parent to save results
        super().deliver(result)
        
        # Clean up temp file if marked
        if result.source.metadata.get('temp_file'):
            temp_path = result.source.path
            if temp_path.exists():
                temp_path.unlink()
                logger.debug(f"Cleaned up temp file: {temp_path.name}")


# Example usage
if __name__ == "__main__":
    # Configuration
    db_config = {
        'host': 'localhost',  # Via SSH tunnel
        'port': 33306,
        'user': 'root',
        'password': 'admin',
        'database': 'oreka'
    }
    
    ssh_config = {
        'user': 'estillmane',
        'host': 's40vpsoxweb002',
        'remote_base': '/var/log/orkaudio.prod.nfs'
    }
    
    # Create source
    source = MariaDBSSHSource(db_config, ssh_config)
    
    # Process one file
    for audio in source.discover():
        print(f"Got audio file: {audio.path}")
        print(f"  Size: {audio.size:,} bytes")
        print(f"  Metadata: {audio.metadata}")
        break  # Just test one
        
    # Cleanup
    source.cleanup()