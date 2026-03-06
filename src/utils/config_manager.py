"""
Configuration manager for AVAM
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class AppConfig:
    """Application configuration"""
    # Window settings
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    
    # FFmpeg settings
    ffmpeg_path: str = ""
    ffprobe_path: str = ""
    
    # GPU settings
    use_gpu: bool = True
    gpu_encoder: str = "nvenc"  # nvenc, qsv, amf
    
    # Output settings
    default_output_dir: str = "output"
    default_quality: str = "high"
    default_resolution: str = "1920x1080"
    default_fps: int = 30
    
    # Audio settings
    normalize_audio: bool = True
    fade_in_duration: float = 1.0
    fade_out_duration: float = 1.0
    
    # Recent files
    recent_projects: list = field(default_factory=list)
    recent_audio_files: list = field(default_factory=list)
    recent_video_files: list = field(default_factory=list)
    
    # UI settings
    theme: str = "default"  # default, dark, light
    language: str = "vi"  # vi, en
    
    # Performance
    enable_preview: bool = True
    preview_duration: int = 30  # seconds
    max_threads: int = 4
    
    # Output panel configuration
    output_panel_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create from dictionary"""
        return cls(**data)

class ConfigManager:
    """Manage application configuration"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Configuration directory (default: ~/.avam)
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / '.avam'
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Config file path
        self.config_file = self.config_dir / 'config.json'
        
        # Default configuration
        self.default_config = AppConfig()
        
        # Current configuration
        self.config = self.default_config
        
    def load_config(self) -> AppConfig:
        """
        Load configuration from file
        
        Returns:
            AppConfig instance
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = AppConfig.from_dict(data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}, using defaults")
                self.config = self.default_config
                self.save_config()
        else:
            # Create default config file
            self.config = self.default_config
            self.save_config()
        
        return self.config
    
    def save_config(self) -> bool:
        """
        Save configuration to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def update_config(self, **kwargs) -> bool:
        """
        Update configuration
        
        Args:
            **kwargs: Configuration parameters to update
            
        Returns:
            True if successful, False otherwise
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                print(f"Warning: Unknown config key: {key}")
        
        return self.save_config()
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return getattr(self.config, key, default)
    
    def add_recent_project(self, project_path: str) -> bool:
        """
        Add project to recent list
        
        Args:
            project_path: Path to project file
            
        Returns:
            True if successful, False otherwise
        """
        if not project_path:
            return False
        
        # Convert to absolute path
        project_path = str(Path(project_path).absolute())
        
        # Remove if already exists
        if project_path in self.config.recent_projects:
            self.config.recent_projects.remove(project_path)
        
        # Add to beginning
        self.config.recent_projects.insert(0, project_path)
        
        # Keep only last 10
        self.config.recent_projects = self.config.recent_projects[:10]
        
        return self.save_config()
    
    def add_recent_audio_file(self, file_path: str) -> bool:
        """
        Add audio file to recent list
        
        Args:
            file_path: Path to audio file
            
        Returns:
            True if successful, False otherwise
        """
        if not file_path:
            return False
        
        file_path = str(Path(file_path).absolute())
        
        if file_path in self.config.recent_audio_files:
            self.config.recent_audio_files.remove(file_path)
        
        self.config.recent_audio_files.insert(0, file_path)
        self.config.recent_audio_files = self.config.recent_audio_files[:20]
        
        return self.save_config()
    
    def add_recent_video_file(self, file_path: str) -> bool:
        """
        Add video file to recent list
        
        Args:
            file_path: Path to video file
            
        Returns:
            True if successful, False otherwise
        """
        if not file_path:
            return False
        
        file_path = str(Path(file_path).absolute())
        
        if file_path in self.config.recent_video_files:
            self.config.recent_video_files.remove(file_path)
        
        self.config.recent_video_files.insert(0, file_path)
        self.config.recent_video_files = self.config.recent_video_files[:20]
        
        return self.save_config()
    
    def get_config_path(self, *args) -> Path:
        """
        Get path in config directory
        
        Args:
            *args: Path components
            
        Returns:
            Path object
        """
        return self.config_dir.joinpath(*args)