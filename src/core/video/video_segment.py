"""
Video segment model and operations
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from ...models.project_config import VideoPosition, LoopStrategy
import logging

logger = logging.getLogger(__name__)

@dataclass
class VideoSegment:
    """Represents a video segment in the timeline"""
    
    file_path: str
    duration: float
    position: VideoPosition = VideoPosition.MIDDLE
    loop_behavior: LoopStrategy = LoopStrategy.AUTO
    order: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate segment after initialization"""
        if self.duration <= 0:
            raise ValueError(f"Invalid duration for segment: {self.duration}")
    
    @property
    def should_loop(self) -> bool:
        """Determine if this segment should loop"""
        if self.loop_behavior == LoopStrategy.AUTO:
            # Auto logic based on position
            if self.position == VideoPosition.MIDDLE:
                return True
            elif self.position == VideoPosition.START:
                # Start segments may or may not loop depending on strategy
                return False  # Default to no loop for start
            elif self.position == VideoPosition.END:
                return False  # End segments typically don't loop
        elif self.loop_behavior == LoopStrategy.LOOP:
            return True
        elif self.loop_behavior == LoopStrategy.NO_LOOP:
            return False
        
        return False  # Default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert segment to dictionary"""
        return {
            'file_path': self.file_path,
            'duration': self.duration,
            'position': self.position.value,
            'loop_behavior': self.loop_behavior.value,
            'order': self.order,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoSegment':
        """Create segment from dictionary"""
        return cls(
            file_path=data['file_path'],
            duration=data['duration'],
            position=VideoPosition(data['position']),
            loop_behavior=LoopStrategy(data['loop_behavior']),
            order=data.get('order', 0),
            metadata=data.get('metadata', {})
        )
    
    def get_ffmpeg_concat_entry(self) -> str:
        """
        Get FFmpeg concat demuxer entry for this segment
        
        Returns:
            FFmpeg concat entry string
        """
        # Escape single quotes in file path
        escaped_path = self.file_path.replace("'", "'\\''")
        return f"file '{escaped_path}'"
    
    def __str__(self) -> str:
        """String representation"""
        loop_status = "LOOP" if self.should_loop else "NO LOOP"
        return (f"VideoSegment(file={self.file_path}, "
                f"duration={self.duration:.2f}s, "
                f"position={self.position.value}, "
                f"behavior={loop_status})")