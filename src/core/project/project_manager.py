"""
Project manager for handling project operations
"""
import os
import shutil
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from ...models.project_config import ProjectConfig
from .project_config import ProjectConfigManager
import logging

logger = logging.getLogger(__name__)

class ProjectManager:
    """Manage project lifecycle and operations"""
    
    def __init__(self, config_manager: ProjectConfigManager = None):
        """
        Initialize project manager
        
        Args:
            config_manager: ProjectConfigManager instance
        """
        if config_manager:
            self.config_manager = config_manager
        else:
            self.config_manager = ProjectConfigManager()
        
        self.current_project = None
        self.project_history = []
    
    def new_project(self, name: str = "Untitled Project") -> ProjectConfig:
        """
        Create new project
        
        Args:
            name: Project name
            
        Returns:
            New ProjectConfig instance
        """
        self.current_project = self.config_manager.create_new_project(name)
        self.project_history.append({
            'timestamp': datetime.now(),
            'action': 'create',
            'project': self.current_project.name
        })
        
        logger.info(f"Created new project: {name}")
        return self.current_project
    
    def load_project(self, file_path: str) -> ProjectConfig:
        """
        Load project from file
        
        Args:
            file_path: Path to project file
            
        Returns:
            Loaded ProjectConfig instance
        """
        self.current_project = self.config_manager.load_project(file_path)
        self.project_history.append({
            'timestamp': datetime.now(),
            'action': 'load',
            'project': self.current_project.name,
            'file_path': file_path
        })
        
        logger.info(f"Loaded project: {file_path}")
        return self.current_project
    
    def save_project(self, file_path: str = None) -> str:
        """
        Save current project
        
        Args:
            file_path: Path to save project (optional)
            
        Returns:
            Path to saved project file
        """
        if not self.current_project:
            raise ValueError("No current project to save")
        
        saved_path = self.config_manager.save_project(self.current_project, file_path)
        
        self.project_history.append({
            'timestamp': datetime.now(),
            'action': 'save',
            'project': self.current_project.name,
            'file_path': saved_path
        })
        
        logger.info(f"Saved project: {saved_path}")
        return saved_path
    
    def save_as_template(self, template_name: str) -> str:
        """
        Save current project as template
        
        Args:
            template_name: Template name
            
        Returns:
            Path to template file
        """
        if not self.current_project:
            raise ValueError("No current project to save as template")
        
        template_path = self.config_manager.create_template(
            self.current_project, 
            template_name
        )
        
        self.project_history.append({
            'timestamp': datetime.now(),
            'action': 'save_template',
            'project': self.current_project.name,
            'template': template_name
        })
        
        logger.info(f"Saved as template: {template_name}")
        return template_path
    
    def load_template(self, template_name: str) -> ProjectConfig:
        """
        Load project from template
        
        Args:
            template_name: Template name
            
        Returns:
            New ProjectConfig from template
        """
        project = self.config_manager.load_template(template_name)
        self.current_project = project
        
        self.project_history.append({
            'timestamp': datetime.now(),
            'action': 'load_template',
            'template': template_name,
            'project': project.name
        })
        
        logger.info(f"Loaded template: {template_name}")
        return project
    
    def add_audio_files(self, file_paths: List[str]) -> List[str]:
        """
        Add audio files to current project
        
        Args:
            file_paths: List of audio file paths
            
        Returns:
            List of successfully added file paths
        """
        if not self.current_project:
            raise ValueError("No current project")
        
        added_files = []
        
        for file_path in file_paths:
            if os.path.exists(file_path) and file_path not in self.current_project.audio_config.audio_files:
                self.current_project.audio_config.audio_files.append(file_path)
                added_files.append(file_path)
        
        if added_files:
            self.project_history.append({
                'timestamp': datetime.now(),
                'action': 'add_audio',
                'files': added_files
            })
        
        logger.info(f"Added {len(added_files)} audio files")
        return added_files
    
    def add_video_segments(self, segments_data: List[Dict[str, Any]]) -> List[str]:
        """
        Add video segments to current project
        
        Args:
            segments_data: List of segment data dictionaries
            
        Returns:
            List of successfully added file paths
        """
        if not self.current_project:
            raise ValueError("No current project")
        
        from ...models.project_config import VideoSegmentConfig, VideoPosition, LoopStrategy
        
        added_segments = []
        
        for seg_data in segments_data:
            file_path = seg_data.get('file_path')
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"Video file not found: {file_path}")
                continue
            
            # Check if already added
            existing_files = [seg.file_path for seg in self.current_project.video_config.video_segments]
            if file_path in existing_files:
                logger.warning(f"Video file already added: {file_path}")
                continue
            
            # Create segment config
            segment = VideoSegmentConfig(
                file_path=file_path,
                position=VideoPosition(seg_data.get('position', 'middle')),
                loop_behavior=LoopStrategy(seg_data.get('loop_behavior', 'auto')),
                order=len(self.current_project.video_config.video_segments)
            )
            
            self.current_project.video_config.video_segments.append(segment)
            added_segments.append(file_path)
        
        if added_segments:
            self.project_history.append({
                'timestamp': datetime.now(),
                'action': 'add_video',
                'files': added_segments
            })
        
        logger.info(f"Added {len(added_segments)} video segments")
        return added_segments
    
    def remove_audio_file(self, file_path: str) -> bool:
        """
        Remove audio file from project
        
        Args:
            file_path: Path to audio file
            
        Returns:
            True if removed, False otherwise
        """
        if not self.current_project:
            return False
        
        if file_path in self.current_project.audio_config.audio_files:
            self.current_project.audio_config.audio_files.remove(file_path)
            
            self.project_history.append({
                'timestamp': datetime.now(),
                'action': 'remove_audio',
                'file': file_path
            })
            
            logger.info(f"Removed audio file: {file_path}")
            return True
        
        return False
    
    def remove_video_segment(self, file_path: str) -> bool:
        """
        Remove video segment from project
        
        Args:
            file_path: Path to video file
            
        Returns:
            True if removed, False otherwise
        """
        if not self.current_project:
            return False
        
        for i, segment in enumerate(self.current_project.video_config.video_segments):
            if segment.file_path == file_path:
                self.current_project.video_config.video_segments.pop(i)
                
                # Update order for remaining segments
                for j, seg in enumerate(self.current_project.video_config.video_segments):
                    seg.order = j
                
                self.project_history.append({
                    'timestamp': datetime.now(),
                    'action': 'remove_video',
                    'file': file_path
                })
                
                logger.info(f"Removed video segment: {file_path}")
                return True
        
        return False
    
    def reorder_video_segments(self, new_order: List[int]) -> bool:
        """
        Reorder video segments
        
        Args:
            new_order: List of indices in new order
            
        Returns:
            True if successful, False otherwise
        """
        if not self.current_project:
            return False
        
        segments = self.current_project.video_config.video_segments
        
        if len(new_order) != len(segments):
            return False
        
        # Reorder segments
        reordered_segments = [segments[i] for i in new_order]
        
        # Update order property
        for i, segment in enumerate(reordered_segments):
            segment.order = i
        
        self.current_project.video_config.video_segments = reordered_segments
        
        self.project_history.append({
            'timestamp': datetime.now(),
            'action': 'reorder_video',
            'new_order': new_order
        })
        
        logger.info(f"Reordered video segments: {new_order}")
        return True
    
    def set_output_config(self, output_config_data: Dict[str, Any]) -> bool:
        """
        Set output configuration
        
        Args:
            output_config_data: Dictionary with output configuration
            
        Returns:
            True if successful, False otherwise
        """
        if not self.current_project:
            return False
        
        from ...models.project_config import OutputConfig, OutputQuality
        
        try:
            output_config = OutputConfig(
                quality=OutputQuality(output_config_data.get('quality', 'high')),
                resolution=output_config_data.get('resolution', '1920x1080'),
                fps=output_config_data.get('fps', 30),
                output_path=output_config_data.get('output_path', ''),
                use_gpu=output_config_data.get('use_gpu', True),
                gpu_encoder=output_config_data.get('gpu_encoder', 'nvenc')
            )
            
            self.current_project.output_config = output_config
            
            self.project_history.append({
                'timestamp': datetime.now(),
                'action': 'set_output_config',
                'config': output_config_data
            })
            
            logger.info(f"Set output configuration: {output_config_data}")
            return True
            
        except ValueError as e:
            logger.error(f"Invalid output configuration: {e}")
            return False
    
    def validate_current_project(self) -> Tuple[bool, List[str]]:
        """
        Validate current project
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not self.current_project:
            return False, ["No current project"]
        
        return self.config_manager.validate_project(self.current_project)
    
    def export_project_summary(self) -> Dict[str, Any]:
        """
        Export project summary
        
        Returns:
            Dictionary with project summary
        """
        if not self.current_project:
            return {}
        
        # Calculate total audio duration
        from ..ffmpeg.ffmpeg_manager import FFmpegManager
        ffmpeg = FFmpegManager()
        
        total_audio_duration = 0.0
        for audio_file in self.current_project.audio_config.audio_files:
            try:
                info = ffmpeg.get_media_info(audio_file)
                total_audio_duration += info['duration']
            except:
                pass
        
        # Calculate total video duration
        total_video_duration = 0.0
        video_segments = []
        
        for segment in self.current_project.video_config.video_segments:
            try:
                info = ffmpeg.get_media_info(segment.file_path)
                duration = info['duration']
                total_video_duration += duration
                
                video_segments.append({
                    'file': segment.file_path,
                    'duration': duration,
                    'position': segment.position.value,
                    'loop_behavior': segment.loop_behavior.value
                })
            except:
                pass
        
        return {
            'project_name': self.current_project.name,
            'audio_files_count': len(self.current_project.audio_config.audio_files),
            'total_audio_duration': total_audio_duration,
            'video_segments_count': len(self.current_project.video_config.video_segments),
            'total_video_duration': total_video_duration,
            'output_config': self.current_project.output_config.to_dict(),
            'video_segments': video_segments,
            'estimated_size': self._estimate_output_size(total_audio_duration)
        }
    
    def _estimate_output_size(self, duration_seconds: float) -> str:
        """
        Estimate output file size
        
        Args:
            duration_seconds: Video duration in seconds
            
        Returns:
            Estimated size string (e.g., "2.5 GB")
        """
        # Bitrate estimation based on quality
        quality_bitrates = {
            'medium': 4000000,  # 4 Mbps
            'high': 8000000,    # 8 Mbps
            'very_high': 12000000,  # 12 Mbps
            'ultra_high': 25000000  # 25 Mbps
        }
        
        bitrate = quality_bitrates.get(
            self.current_project.output_config.quality.value, 
            8000000
        )
        
        # Size in bytes = bitrate (bits/sec) * duration (sec) / 8
        size_bytes = (bitrate * duration_seconds) / 8
        
        # Convert to human readable
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        
        return f"{size_bytes:.1f} TB"
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get project history"""
        return self.project_history
    
    def clear_history(self):
        """Clear project history"""
        self.project_history = []
        logger.info("Cleared project history")