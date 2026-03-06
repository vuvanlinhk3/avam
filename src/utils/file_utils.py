"""
File utility functions for AVAM
"""
import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import mimetypes

class FileUtils:
    """File utility class"""
    
    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = 'md5') -> str:
        """
        Calculate file hash
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm (md5, sha1, sha256)
            
        Returns:
            File hash string
        """
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human readable format
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        
        while size_bytes >= 1024 and unit_index < len(units) - 1:
            size_bytes /= 1024
            unit_index += 1
        
        return f"{size_bytes:.2f} {units[unit_index]}"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in human readable format
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.0f}s"
    
    @staticmethod
    def get_file_type(file_path: str) -> str:
        """
        Get file type (audio, video, image, etc.)
        
        Args:
            file_path: Path to file
            
        Returns:
            File type string
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if mime_type:
            if mime_type.startswith('audio/'):
                return 'audio'
            elif mime_type.startswith('video/'):
                return 'video'
            elif mime_type.startswith('image/'):
                return 'image'
            elif mime_type.startswith('text/'):
                return 'text'
        
        # Fallback based on extension
        ext = Path(file_path).suffix.lower()
        
        audio_extensions = {'.mp3', '.wav', '.aac', '.flac', '.m4a', '.ogg', '.wma'}
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.mts', '.m2ts'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        
        if ext in audio_extensions:
            return 'audio'
        elif ext in video_extensions:
            return 'video'
        elif ext in image_extensions:
            return 'image'
        
        return 'unknown'
    
    @staticmethod
    def find_files(directory: str, extensions: List[str]) -> List[str]:
        """
        Find files with specific extensions in directory
        
        Args:
            directory: Directory to search
            extensions: List of file extensions (with dot)
            
        Returns:
            List of file paths
        """
        files = []
        
        for ext in extensions:
            pattern = f"*{ext}"
            found_files = Path(directory).glob(pattern)
            files.extend([str(f) for f in found_files])
        
        return sorted(files)
    
    @staticmethod
    def safe_delete(file_path: str) -> bool:
        """
        Safely delete file
        
        Args:
            file_path: Path to file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                return True
        except OSError:
            pass
        
        return False
    
    @staticmethod
    def safe_copy(src: str, dst: str) -> bool:
        """
        Safely copy file
        
        Args:
            src: Source file path
            dst: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            shutil.copy2(src, dst)
            return True
        except (shutil.Error, IOError):
            return False
    
    @staticmethod
    def create_directory(directory: str) -> bool:
        """
        Create directory if it doesn't exist
        
        Args:
            directory: Directory path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except OSError:
            return False
    
    @staticmethod
    def get_unique_filename(file_path: str) -> str:
        """
        Get unique filename if file already exists
        
        Args:
            file_path: Desired file path
            
        Returns:
            Unique file path
        """
        path = Path(file_path)
        
        if not path.exists():
            return file_path
        
        # Try adding (1), (2), etc.
        counter = 1
        while True:
            new_path = path.parent / f"{path.stem} ({counter}){path.suffix}"
            if not new_path.exists():
                return str(new_path)
            counter += 1
    
    @staticmethod
    def validate_media_file(file_path: str, expected_type: str = None) -> Tuple[bool, str]:
        """
        Validate media file
        
        Args:
            file_path: Path to media file
            expected_type: Expected file type (audio, video)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
        
        if not os.path.isfile(file_path):
            return False, f"Not a file: {file_path}"
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, f"Empty file: {file_path}"
        
        if expected_type:
            file_type = FileUtils.get_file_type(file_path)
            if file_type != expected_type:
                return False, f"Expected {expected_type} file, got {file_type}"
        
        return True, "Valid file"