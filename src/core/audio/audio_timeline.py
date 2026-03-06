"""
Audio timeline management
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AudioTimeline:
    """Manage audio timeline for video synchronization"""
    
    def __init__(self):
        """Initialize audio timeline"""
        self.audio_files = []
        self.total_duration = 0.0
        self.segments = []
    
    def build_timeline(self, audio_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build timeline with segments
        
        Args:
            audio_files: List of audio information dictionaries
            
        Returns:
            List of timeline segments with start/end times
        """
        self.audio_files = audio_files
        self.total_duration = 0.0
        self.segments = []
        
        current_time = 0.0
        
        for audio in audio_files:
            segment = {
                'file_path': audio['file_path'],
                'start_time': current_time,
                'end_time': current_time + audio['duration'],
                'duration': audio['duration'],
                'audio_info': audio
            }
            
            self.segments.append(segment)
            current_time += audio['duration']
        
        self.total_duration = current_time
        
        logger.info(f"Built audio timeline: {len(self.segments)} segments, "
                   f"total duration: {self.total_duration:.2f}s")
        
        return self.segments
    
    def get_segment_at_time(self, time_seconds: float) -> Dict[str, Any]:
        """
        Get audio segment at specific time
        
        Args:
            time_seconds: Time in seconds
            
        Returns:
            Segment dictionary at specified time
        """
        if time_seconds < 0 or time_seconds > self.total_duration:
            return None
        
        for segment in self.segments:
            if segment['start_time'] <= time_seconds < segment['end_time']:
                return segment
        
        # Handle edge case at exact end time
        if time_seconds == self.total_duration:
            return self.segments[-1] if self.segments else None
        
        return None
    
    def get_time_string(self, time_seconds: float) -> str:
        """
        Convert seconds to HH:MM:SS.mmm format
        
        Args:
            time_seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        hours = int(time_seconds // 3600)
        minutes = int((time_seconds % 3600) // 60)
        seconds = time_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    
    def get_duration_string(self) -> str:
        """Get total duration as formatted string"""
        return self.get_time_string(self.total_duration)
    
    def export_concat_list(self, output_file: str) -> str:
        """
        Generate FFmpeg concat list file
        
        Args:
            output_file: Path to output concat list file
            
        Returns:
            Path to concat list file
        """
        concat_lines = []
        
        for segment in self.segments:
            # Escape special characters in file path
            file_path = segment['file_path'].replace("'", "'\\''")
            concat_lines.append(f"file '{file_path}'")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(concat_lines))
        
        logger.info(f"Exported concat list to: {output_file}")
        return output_file