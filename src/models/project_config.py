"""
Data models for project configuration
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
import os

class VideoPosition(Enum):
    """Position of video segment"""
    START = "start"
    MIDDLE = "middle" 
    END = "end"

class LoopStrategy(Enum):
    """Loop strategy for videos"""
    AUTO = "auto"
    LOOP = "loop"
    NO_LOOP = "no_loop"

class OutputQuality(Enum):
    """Output quality presets"""
    ULTRA_FAST = 'ultra_fast'
    MEDIUM = "medium"      # Fastest
    HIGH = "high"         # Balanced
    VERY_HIGH = "very_high"  # YouTube
    ULTRA_HIGH = "ultra_high" # Archive

@dataclass
class AudioConfig:
    """Configuration for audio processing"""
    audio_files: List[str] = field(default_factory=list)
    normalize_volume: bool = True
    fade_in_duration: float = 1.0  # seconds
    fade_out_duration: float = 1.0  # seconds
    output_audio_path: str = ""
    volume: float = 4

    def to_dict(self) -> Dict[str, Any]:
        return {
            'audio_files': self.audio_files,
            'normalize_volume': self.normalize_volume,
            'fade_in_duration': self.fade_in_duration,
            'fade_out_duration': self.fade_out_duration,
            'output_audio_path': self.output_audio_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioConfig':
        return cls(**data)

@dataclass
class VideoSegmentConfig:
    """Configuration for a single video segment"""
    file_path: str
    position: VideoPosition = VideoPosition.MIDDLE
    loop_behavior: LoopStrategy = LoopStrategy.AUTO
    order: int = 0
    mute_audio: bool = False          # 🆕 Tắt âm thanh của video này
    audio_volume: float = 1.0          # 🆕 Âm lượng nếu không tắt (0.0 - 2.0)
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'position': self.position.value,
            'loop_behavior': self.loop_behavior.value,
            'order': self.order
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoSegmentConfig':
        data = data.copy()
        data['position'] = VideoPosition(data['position'])
        data['loop_behavior'] = LoopStrategy(data['loop_behavior'])
        return cls(**data)

@dataclass
class VideoConfig:
    """Configuration for video processing"""
    video_segments: List[VideoSegmentConfig] = field(default_factory=list)
    output_video_path: str = ""
    audio_volume: float = 1.0  # 🆕 Global volume cho video audio (nếu không mute)
    def to_dict(self) -> Dict[str, Any]:
        return {
            'video_segments': [seg.to_dict() for seg in self.video_segments],
            'output_video_path': self.output_video_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoConfig':
        video_segments = [
            VideoSegmentConfig.from_dict(seg) for seg in data['video_segments']
        ]
        return cls(
            video_segments=video_segments,
            output_video_path=data['output_video_path']
        )

@dataclass
class OutputConfig:
    """Configuration for output video"""
    quality: OutputQuality = OutputQuality.HIGH
    resolution: str = "1920x1080"  # Width x Height
    fps: int = 30
    output_path: str = ""
    use_gpu: bool = True
    gpu_encoder: str = "nvenc"  # nvenc, qsv, amf
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'quality': self.quality.value,
            'resolution': self.resolution,
            'fps': self.fps,
            'output_path': self.output_path,
            'use_gpu': self.use_gpu,
            'gpu_encoder': self.gpu_encoder
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OutputConfig':
        data = data.copy()
        data['quality'] = OutputQuality(data['quality'])
        return cls(**data)

@dataclass
class ProjectConfig:
    """Complete project configuration"""
    name: str = "Untitled Project"
    audio_config: AudioConfig = field(default_factory=AudioConfig)
    video_config: VideoConfig = field(default_factory=VideoConfig)
    output_config: OutputConfig = field(default_factory=OutputConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'audio_config': self.audio_config.to_dict(),
            'video_config': self.video_config.to_dict(),
            'output_config': self.output_config.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        return cls(
            name=data['name'],
            audio_config=AudioConfig.from_dict(data['audio_config']),
            video_config=VideoConfig.from_dict(data['video_config']),
            output_config=OutputConfig.from_dict(data['output_config'])
        )
    
    def save(self, file_path: str):
        """Save project to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, file_path: str) -> 'ProjectConfig':
        """Load project from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)