"""
Audio file loader and validator
"""
import os
from typing import List, Tuple, Dict, Any
from pathlib import Path
from ..ffmpeg.ffmpeg_manager import FFmpegManager
import logging

logger = logging.getLogger(__name__)

class AudioLoader:
    """Load and validate audio files"""
    
    SUPPORTED_FORMATS = {'.mp3', '.wav', '.aac', '.m4a', '.flac', '.ogg'}
    
    def __init__(self, ffmpeg_manager: FFmpegManager):
        """
        Initialize audio loader
        
        Args:
            ffmpeg_manager: FFmpegManager instance
        """
        self.ffmpeg = ffmpeg_manager
    
    def validate_audio_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate an audio file
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, f"File does not exist: {file_path}"
            
            # Check file extension
            ext = Path(file_path).suffix.lower()
            if ext not in self.SUPPORTED_FORMATS:
                return False, f"Unsupported audio format: {ext}"
            
            # Get file info using ffprobe
            info = self.ffmpeg.get_media_info(file_path)
            
            # Check if it has audio stream
            has_audio = any(
                stream['codec_type'] == 'audio' 
                for stream in info['streams']
            )
            
            if not has_audio:
                return False, f"No audio stream found in: {file_path}"
            
            # Check duration
            if info['duration'] <= 0:
                return False, f"Invalid duration: {file_path}"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, f"Empty file: {file_path}"
            
            return True, "Valid audio file"
            
        except Exception as e:
            logger.error(f"Error validating audio file {file_path}: {e}")
            return False, f"Error validating file: {str(e)}"
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed audio information
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio information
        """
        try:
            info = self.ffmpeg.get_media_info(file_path)
            
            # Find audio stream
            audio_stream = None
            for stream in info['streams']:
                if stream['codec_type'] == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise ValueError(f"No audio stream found in {file_path}")
            
            return {
                'file_path': file_path,
                'duration': info['duration'],
                'size': info['size'],
                'format': info['format'],
                'codec': audio_stream.get('codec_name', 'unknown'),
                'sample_rate': audio_stream.get('sample_rate', 0),
                'channels': audio_stream.get('channels', 0),
                'bit_rate': audio_stream.get('bit_rate', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting audio info for {file_path}: {e}")
            raise
    
    def load_multiple_audio_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Load and validate multiple audio files
        
        Args:
            file_paths: List of audio file paths
            
        Returns:
            List of audio information dictionaries
        """
        audio_files = []
        errors = []
        
        for file_path in file_paths:
            is_valid, error_msg = self.validate_audio_file(file_path)
            
            if is_valid:
                try:
                    info = self.get_audio_info(file_path)
                    audio_files.append(info)
                    logger.info(f"Loaded audio: {file_path} ({info['duration']:.2f}s)")
                except Exception as e:
                    errors.append(f"Error loading {file_path}: {str(e)}")
            else:
                errors.append(f"Invalid audio file {file_path}: {error_msg}")
        
        if errors:
            logger.warning(f"Audio loading errors: {errors}")
        
        return audio_files, errors
    
    def get_total_duration(self, audio_files: List[Dict[str, Any]]) -> float:
        """
        Calculate total duration of audio files
        
        Args:
            audio_files: List of audio information dictionaries
            
        Returns:
            Total duration in seconds
        """
        total = 0.0
        for audio in audio_files:
            total += audio['duration']
        return total
    
    def sort_audio_files(self, audio_files: List[Dict[str, Any]], 
                        order: List[int]) -> List[Dict[str, Any]]:
        """
        Sort audio files according to specified order
        
        Args:
            audio_files: List of audio information dictionaries
            order: List of indices specifying the order
            
        Returns:
            Sorted list of audio files
        """
        if len(order) != len(audio_files):
            raise ValueError("Order list must have same length as audio files")
        
        # Create mapping from original index to file
        files_by_index = {i: audio_files[i] for i in range(len(audio_files))}
        
        # Reorder according to specified order
        sorted_files = []
        for idx in order:
            if idx in files_by_index:
                sorted_files.append(files_by_index[idx])
            else:
                raise ValueError(f"Invalid index in order list: {idx}")
        
        return sorted_files