"""
Progress tracking for FFmpeg operations
"""
import re
from typing import Callable, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Track progress of FFmpeg operations"""
    
    def __init__(self, total_duration: float = 0.0):
        """
        Initialize progress tracker
        
        Args:
            total_duration: Total expected duration in seconds
        """
        self.total_duration = total_duration
        self.current_time = 0.0
        self.percent_complete = 0.0
        self.speed_factor = 1.0
        self.estimated_time_remaining = 0.0
        
    def update_from_ffmpeg_output(self, line: str) -> Optional[float]:
        """
        Parse FFmpeg output line for progress information
        
        Args:
            line: FFmpeg output line
            
        Returns:
            Current time in seconds if parsed, None otherwise
        """
        # Try to parse time
        time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = float(time_match.group(3))
            
            self.current_time = hours * 3600 + minutes * 60 + seconds
            
            # Calculate percentage
            if self.total_duration > 0:
                self.percent_complete = min(100.0, (self.current_time / self.total_duration) * 100)
            
            # Try to parse speed
            speed_match = re.search(r'speed=(\d+\.?\d*)x', line)
            if speed_match:
                self.speed_factor = float(speed_match.group(1))
                
                # Estimate remaining time
                if self.speed_factor > 0 and self.total_duration > 0:
                    time_elapsed = self.current_time / self.speed_factor
                    total_estimated_time = self.total_duration / self.speed_factor
                    self.estimated_time_remaining = max(0, total_estimated_time - time_elapsed)
            
            return self.current_time
        
        return None
    
    def get_progress_dict(self) -> Dict[str, Any]:
        """Get progress information as dictionary"""
        return {
            'current_time': self.current_time,
            'total_duration': self.total_duration,
            'percent_complete': self.percent_complete,
            'speed_factor': self.speed_factor,
            'estimated_time_remaining': self.estimated_time_remaining
        }
    
    def format_time(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def get_progress_string(self) -> str:
        """Get formatted progress string"""
        if self.total_duration <= 0:
            return f"Progress: {self.percent_complete:.1f}%"
        
        current_str = self.format_time(self.current_time)
        total_str = self.format_time(self.total_duration)
        remaining_str = self.format_time(self.estimated_time_remaining)
        
        return (f"{self.percent_complete:.1f}% "
                f"({current_str} / {total_str}) "
                f"Speed: {self.speed_factor:.2f}x "
                f"ETA: {remaining_str}")