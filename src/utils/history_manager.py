"""
History manager for AVAM
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class HistoryEntry:
    """History entry for exported videos"""
    timestamp: datetime
    project_name: str
    output_path: str
    audio_files_count: int
    video_segments_count: int
    total_duration: float
    output_size: int
    output_quality: str
    success: bool = True
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryEntry':
        """Create from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class HistoryManager:
    """Manage export history"""
    
    def __init__(self, history_dir: str = None):
        """
        Initialize history manager
        
        Args:
            history_dir: History directory (default: history/)
        """
        if history_dir:
            self.history_dir = Path(history_dir)
        else:
            self.history_dir = Path("history")
        
        # Create history directory if it doesn't exist
        self.history_dir.mkdir(exist_ok=True)
        
        # History file
        self.history_file = self.history_dir / 'export_history.json'
        
        # Load history
        self.history = self._load_history()
    
    def _load_history(self) -> List[HistoryEntry]:
        """
        Load history from file
        
        Returns:
            List of history entries
        """
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [HistoryEntry.from_dict(entry) for entry in data]
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_history(self) -> bool:
        """
        Save history to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                data = [entry.to_dict() for entry in self.history]
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def add_entry(self, entry: HistoryEntry) -> bool:
        """
        Add history entry
        
        Args:
            entry: History entry
            
        Returns:
            True if successful, False otherwise
        """
        self.history.append(entry)
        
        # Keep only last 100 entries
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        return self._save_history()
    
    def create_entry(self, project_name: str, output_path: str,
                    audio_files_count: int, video_segments_count: int,
                    total_duration: float, output_size: int,
                    output_quality: str, success: bool = True,
                    error_message: str = "") -> HistoryEntry:
        """
        Create and add history entry
        
        Args:
            project_name: Project name
            output_path: Output video path
            audio_files_count: Number of audio files
            video_segments_count: Number of video segments
            total_duration: Total duration in seconds
            output_size: Output file size in bytes
            output_quality: Output quality
            success: Whether export was successful
            error_message: Error message if failed
            
        Returns:
            History entry
        """
        entry = HistoryEntry(
            timestamp=datetime.now(),
            project_name=project_name,
            output_path=output_path,
            audio_files_count=audio_files_count,
            video_segments_count=video_segments_count,
            total_duration=total_duration,
            output_size=output_size,
            output_quality=output_quality,
            success=success,
            error_message=error_message
        )
        
        self.add_entry(entry)
        return entry
    
    def get_history(self, limit: int = 50) -> List[HistoryEntry]:
        """
        Get history entries
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of history entries (most recent first)
        """
        return list(reversed(self.history[-limit:]))
    
    def clear_history(self) -> bool:
        """
        Clear all history
        
        Returns:
            True if successful, False otherwise
        """
        self.history = []
        return self._save_history()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get export statistics
        
        Returns:
            Dictionary with statistics
        """
        if not self.history:
            return {}
        
        successful = [entry for entry in self.history if entry.success]
        failed = [entry for entry in self.history if not entry.success]
        
        total_duration = sum(entry.total_duration for entry in successful)
        total_size = sum(entry.output_size for entry in successful)
        
        return {
            'total_exports': len(self.history),
            'successful_exports': len(successful),
            'failed_exports': len(failed),
            'success_rate': len(successful) / len(self.history) * 100 if self.history else 0,
            'total_duration_hours': total_duration / 3600,
            'total_size_gb': total_size / (1024**3),
            'last_export': self.history[-1].timestamp if self.history else None
        }