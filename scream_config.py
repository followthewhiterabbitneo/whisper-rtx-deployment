#!/usr/bin/env python3
"""
SCREAM Configuration System
Handles configuration from multiple sources with proper precedence
"""

import os
import json
import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class SourceConfig:
    """Configuration for audio source"""
    type: str = "directory"
    path: str = "wav"
    formats: List[str] = None
    watch_interval: int = 5
    recursive: bool = False
    
    def __post_init__(self):
        if self.formats is None:
            self.formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']


@dataclass
class EngineConfig:
    """Configuration for transcription engine"""
    type: str = "whisper"
    model_path: str = "models/faster-whisper-large-v3-turbo-ct2"
    device: str = "cuda"
    compute_type: str = "int8_float16"
    beam_size: int = 5
    language: Optional[str] = None
    batch_size: int = 1
    num_workers: int = 1


@dataclass
class SinkConfig:
    """Configuration for output sink"""
    type: str = "file"
    path: str = "transcriptions"
    format: str = "txt"
    include_timestamps: bool = False
    include_metadata: bool = False


@dataclass
class PipelineConfig:
    """Main pipeline configuration"""
    source: SourceConfig
    engine: EngineConfig
    sink: SinkConfig
    continuous: bool = False
    log_level: str = "INFO"
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create config from dictionary"""
        return cls(
            source=SourceConfig(**data.get('source', {})),
            engine=EngineConfig(**data.get('engine', {})),
            sink=SinkConfig(**data.get('sink', {})),
            continuous=data.get('continuous', False),
            log_level=data.get('log_level', 'INFO')
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'source': asdict(self.source),
            'engine': asdict(self.engine),
            'sink': asdict(self.sink),
            'continuous': self.continuous,
            'log_level': self.log_level
        }


class ConfigLoader:
    """Load configuration from multiple sources"""
    
    DEFAULT_CONFIG_NAMES = ['scream.yaml', 'scream.json', '.scream']
    
    def __init__(self):
        self.config = None
        
    def load(self, config_file: Optional[str] = None) -> PipelineConfig:
        """Load configuration with proper precedence"""
        
        # 1. Start with defaults
        config_dict = self._get_defaults()
        
        # 2. Load from file
        if config_file:
            file_config = self._load_file(config_file)
            config_dict = self._merge_configs(config_dict, file_config)
        else:
            # Look for default config files
            for name in self.DEFAULT_CONFIG_NAMES:
                if Path(name).exists():
                    file_config = self._load_file(name)
                    config_dict = self._merge_configs(config_dict, file_config)
                    break
        
        # 3. Apply environment variables
        env_config = self._load_env()
        config_dict = self._merge_configs(config_dict, env_config)
        
        # 4. Create config object
        self.config = PipelineConfig.from_dict(config_dict)
        return self.config
        
    def _get_defaults(self) -> dict:
        """Get default configuration"""
        return {
            'source': {
                'type': 'directory',
                'path': 'wav',
                'formats': ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
            },
            'engine': {
                'type': 'whisper',
                'model_path': 'models/faster-whisper-large-v3-turbo-ct2',
                'device': 'cuda',
                'compute_type': 'int8_float16'
            },
            'sink': {
                'type': 'file',
                'path': 'transcriptions',
                'format': 'txt'
            },
            'continuous': False,
            'log_level': 'INFO'
        }
        
    def _load_file(self, filepath: str) -> dict:
        """Load configuration from file"""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
            
        with open(path, 'r') as f:
            if path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif path.suffix == '.json':
                return json.load(f)
            else:
                # Try to parse as YAML first, then JSON
                content = f.read()
                try:
                    return yaml.safe_load(content)
                except:
                    return json.loads(content)
                    
    def _load_env(self) -> dict:
        """Load configuration from environment variables"""
        config = {}
        
        # Map environment variables to config paths
        env_map = {
            'SCREAM_SOURCE_PATH': ('source', 'path'),
            'SCREAM_SOURCE_FORMATS': ('source', 'formats'),
            'SCREAM_ENGINE_DEVICE': ('engine', 'device'),
            'SCREAM_ENGINE_MODEL': ('engine', 'model_path'),
            'SCREAM_SINK_PATH': ('sink', 'path'),
            'SCREAM_SINK_FORMAT': ('sink', 'format'),
            'SCREAM_CONTINUOUS': ('continuous',),
            'SCREAM_LOG_LEVEL': ('log_level',)
        }
        
        for env_var, path in env_map.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert value type
                if env_var == 'SCREAM_SOURCE_FORMATS':
                    value = value.split(',')
                elif env_var == 'SCREAM_CONTINUOUS':
                    value = value.lower() in ['true', '1', 'yes']
                    
                # Set in config dict
                self._set_nested(config, path, value)
                
        return config
        
    def _merge_configs(self, base: dict, override: dict) -> dict:
        """Merge two config dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def _set_nested(self, d: dict, path: tuple, value: Any):
        """Set nested dictionary value"""
        for key in path[:-1]:
            if key not in d:
                d[key] = {}
            d = d[key]
        d[path[-1]] = value
        
    def save(self, filepath: str, config: Optional[PipelineConfig] = None):
        """Save configuration to file"""
        config = config or self.config
        if not config:
            raise ValueError("No configuration to save")
            
        path = Path(filepath)
        config_dict = config.to_dict()
        
        with open(path, 'w') as f:
            if path.suffix in ['.yaml', '.yml']:
                yaml.dump(config_dict, f, default_flow_style=False)
            else:
                json.dump(config_dict, f, indent=2)
                
        print(f"Configuration saved to: {filepath}")


def create_example_config():
    """Create an example configuration file"""
    
    example = {
        'source': {
            'type': 'directory',
            'path': 'wav',
            'formats': ['.wav', '.mp3', '.m4a'],
            'recursive': True
        },
        'engine': {
            'type': 'whisper',
            'model_path': 'models/faster-whisper-large-v3-turbo-ct2',
            'device': 'cuda',
            'compute_type': 'int8_float16',
            'beam_size': 5,
            'num_workers': 2
        },
        'sink': {
            'type': 'file',
            'path': 'transcriptions',
            'format': 'json',
            'include_timestamps': True,
            'include_metadata': True
        },
        'continuous': False,
        'log_level': 'INFO'
    }
    
    with open('scream.yaml.example', 'w') as f:
        yaml.dump(example, f, default_flow_style=False)
        
    print("Example configuration saved to: scream.yaml.example")


if __name__ == "__main__":
    # Test configuration loading
    loader = ConfigLoader()
    
    # Create example config
    create_example_config()
    
    # Load config
    config = loader.load()
    
    # Print loaded config
    print("Loaded configuration:")
    print(yaml.dump(config.to_dict(), default_flow_style=False))