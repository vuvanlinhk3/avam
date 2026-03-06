"""
Video file loader and metadata extractor
"""
import os
from typing import List, Tuple, Dict, Any
from pathlib import Path
from ..ffmpeg.ffmpeg_manager import FFmpegManager
import logging

logger = logging.getLogger(__name__)

class VideoLoader:
    """Load and analyze video files"""
    
    SUPPORTED_FORMATS = {
        '.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv',
        '.wmv', '.m4v', '.mpg', '.mpeg', '.ts', '.mts'
    }
    
    def __init__(self, ffmpeg_manager: FFmpegManager):
        """
        Initialize video loader
        
        Args:
            ffmpeg_manager: FFmpegManager instance
        """
        self.ffmpeg = ffmpeg_manager
    
    def validate_video_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate a video file
        
        Args:
            file_path: Path to video file
            
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
                return False, f"Unsupported video format: {ext}"
            
            # Get file info using ffprobe
            info = self.ffmpeg.get_media_info(file_path)
            
            # Check if it has video stream
            has_video = any(
                stream['codec_type'] == 'video' 
                for stream in info['streams']
            )
            
            if not has_video:
                return False, f"No video stream found in: {file_path}"
            
            # Check duration
            if info['duration'] <= 0:
                return False, f"Invalid duration: {file_path}"
            
            # Check resolution
            video_stream = next(
                (s for s in info['streams'] if s['codec_type'] == 'video'),
                None
            )
            
            if not video_stream:
                return False, f"No video stream metadata: {file_path}"
            
            width = video_stream.get('width', 0)
            height = video_stream.get('height', 0)
            
            if width <= 0 or height <= 0:
                return False, f"Invalid resolution: {width}x{height}"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, f"Empty file: {file_path}"
            
            return True, "Valid video file"
            
        except Exception as e:
            logger.error(f"Error validating video file {file_path}: {e}")
            return False, f"Error validating file: {str(e)}"
    
    def get_video_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed video information
        
        Args:
            file_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        try:
            info = self.ffmpeg.get_media_info(file_path)
            
            # Find video and audio streams
            video_stream = None
            audio_stream = None
            
            for stream in info['streams']:
                if stream['codec_type'] == 'video' and not video_stream:
                    video_stream = stream
                elif stream['codec_type'] == 'audio' and not audio_stream:
                    audio_stream = stream
            
            if not video_stream:
                raise ValueError(f"No video stream found in {file_path}")
            
            # Parse frame rate
            frame_rate = '30/1'  # Default
            if 'r_frame_rate' in video_stream:
                r_frame_rate = video_stream['r_frame_rate']
                try:
                    num, den = map(int, r_frame_rate.split('/'))
                    if den != 0:
                        frame_rate = f"{num}/{den}"
                except (ValueError, ZeroDivisionError):
                    frame_rate = r_frame_rate
            
            return {
                'file_path': file_path,
                'duration': info['duration'],
                'size': info['size'],
                'format': info['format'],
                
                # Video stream info
                'video_codec': video_stream.get('codec_name', 'unknown'),
                'width': video_stream.get('width', 0),
                'height': video_stream.get('height', 0),
                'frame_rate': frame_rate,
                'video_bitrate': video_stream.get('bit_rate', 0),
                'pix_fmt': video_stream.get('pix_fmt', 'yuv420p'),
                
                # Audio stream info (if exists)
                'has_audio': audio_stream is not None,
                'audio_codec': audio_stream.get('codec_name', '') if audio_stream else '',
                'audio_sample_rate': audio_stream.get('sample_rate', 0) if audio_stream else 0,
                'audio_channels': audio_stream.get('channels', 0) if audio_stream else 0,
                'audio_bitrate': audio_stream.get('bit_rate', 0) if audio_stream else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting video info for {file_path}: {e}")
            raise
    
    def load_multiple_video_files(self, file_paths: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Load and validate multiple video files
        
        Args:
            file_paths: List of video file paths
            
        Returns:
            Tuple of (video_files, errors)
        """
        video_files = []
        errors = []
        
        for file_path in file_paths:
            is_valid, error_msg = self.validate_video_file(file_path)
            
            if is_valid:
                try:
                    info = self.get_video_info(file_path)
                    video_files.append(info)
                    logger.info(f"Loaded video: {file_path} "
                               f"({info['duration']:.2f}s, "
                               f"{info['width']}x{info['height']})")
                except Exception as e:
                    errors.append(f"Error loading {file_path}: {str(e)}")
            else:
                errors.append(f"Invalid video file {file_path}: {error_msg}")
        
        return video_files, errors
    
    def get_video_resolution(self, file_path: str) -> Tuple[int, int]:
        """
        Get video resolution
        
        Args:
            file_path: Path to video file
            
        Returns:
            Tuple of (width, height)
        """
        info = self.get_video_info(file_path)
        return info['width'], info['height']
    
    def get_video_duration(self, file_path: str) -> float:
        """
        Get video duration in seconds
        
        Args:
            file_path: Path to video file
            
        Returns:
            Duration in seconds
        """
        info = self.get_video_info(file_path)
        return info['duration']
    
    def extract_audio_stream(self, video_path: str, audio_output_path: str) -> str:
        """
        Extract audio stream from video
        
        Args:
            video_path: Path to video file
            audio_output_path: Output audio file path
            
        Returns:
            Path to extracted audio file
        """
        cmd = [
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'copy',
            audio_output_path
        ]
        
        return_code, stdout, stderr = self.ffmpeg.execute_command(cmd)
        
        if return_code != 0:
            raise RuntimeError(f"Audio extraction failed: {stderr}")
        
        logger.info(f"Extracted audio to: {audio_output_path}")
        return audio_output_path
    
    def create_thumbnail(self, video_path: str, output_path: str,
                        time_seconds: float = 1.0) -> str:
        """
        Create thumbnail from video
        
        Args:
            video_path: Path to video file
            output_path: Output thumbnail path
            time_seconds: Time to capture thumbnail
            
        Returns:
            Path to thumbnail file
        """
        cmd = [
            '-i', video_path,
            '-ss', str(time_seconds),
            '-vframes', '1',
            '-vf', 'scale=320:-1',
            '-q:v', '2',
            output_path
        ]
        
        return_code, stdout, stderr = self.ffmpeg.execute_command(cmd)
        
        if return_code != 0:
            raise RuntimeError(f"Thumbnail creation failed: {stderr}")
        
        logger.info(f"Created thumbnail: {output_path}")
        return output_path