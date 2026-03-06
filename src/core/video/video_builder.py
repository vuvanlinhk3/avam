"""
Video timeline builder
"""
import os
import tempfile
from typing import List, Dict, Any
from pathlib import Path
from .video_segment import VideoSegment
from .video_loop_strategy import VideoLoopStrategy
from ..ffmpeg.ffmpeg_manager import FFmpegManager
from ..ffmpeg.gpu_encoder import GPUEncoder
import logging

logger = logging.getLogger(__name__)

class VideoBuilder:
    """Build video timeline and prepare for merging"""
    
    def __init__(self, ffmpeg_manager: FFmpegManager, gpu_encoder: GPUEncoder = None):
        """
        Initialize video builder
        
        Args:
            ffmpeg_manager: FFmpegManager instance
            gpu_encoder: GPUEncoder instance (optional)
        """
        self.ffmpeg = ffmpeg_manager
        self.gpu_encoder = gpu_encoder
    
    def create_video_segments(self, video_files: List[Dict[str, Any]],
                            positions: List[str] = None,
                            loop_behaviors: List[str] = None) -> List[VideoSegment]:
        """
        Create video segments from file information
        
        Args:
            video_files: List of video information dictionaries
            positions: List of positions (start, middle, end)
            loop_behaviors: List of loop behaviors (auto, loop, no_loop)
            
        Returns:
            List of VideoSegment objects
        """
        from ...models.project_config import VideoPosition, LoopStrategy
        
        segments = []
        
        for i, video_info in enumerate(video_files):
            # Determine position
            if positions and i < len(positions):
                position = VideoPosition(positions[i])
            else:
                # Auto-determine position
                if i == 0:
                    position = VideoPosition.START
                elif i == len(video_files) - 1:
                    position = VideoPosition.END
                else:
                    position = VideoPosition.MIDDLE
            
            # Determine loop behavior
            if loop_behaviors and i < len(loop_behaviors):
                loop_behavior = LoopStrategy(loop_behaviors[i])
            else:
                loop_behavior = LoopStrategy.AUTO
            
            # Create segment
            segment = VideoSegment(
                file_path=video_info['file_path'],
                duration=video_info['duration'],
                position=position,
                loop_behavior=loop_behavior,
                order=i,
                metadata=video_info
            )
            
            segments.append(segment)
        
        return segments
    
    def build_video_concat(self, segments: List[VideoSegment],
                          audio_duration: float,
                          output_file: str = None) -> str:
        """
        Build video concat list for FFmpeg
        
        Args:
            segments: List of video segments
            audio_duration: Total audio duration
            output_file: Output concat list file (optional)
            
        Returns:
            Path to concat list file
        """
        # Create loop strategy với logic cắt ngắn mới
        loop_strategy = VideoLoopStrategy(audio_duration)
        
        # Build timeline
        timeline = loop_strategy.build_timeline(segments)
        
        # Generate concat list
        if not output_file:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            output_file = os.path.join(temp_dir, 'avam_video_concat.txt')
        
        concat_file = loop_strategy.generate_ffmpeg_concat_list(output_file)
        
        # Log summary chi tiết
        summary = loop_strategy.get_summary()
        logger.info("=== VIDEO TIMELINE SUMMARY ===")
        logger.info(f"Audio duration: {summary['audio_duration']:.2f}s ({summary['audio_duration']/60:.2f}min)")
        logger.info(f"Video duration: {summary['video_duration']:.2f}s ({summary['video_duration']/60:.2f}min)")
        logger.info(f"Difference: {summary['duration_difference']:.2f}s")
        
        if summary['has_trim']:
            trim = summary['trim_info']
            logger.info(f"TRIM APPLIED: {Path(trim['file']).name}")
            logger.info(f"  Original: {trim['original_duration']:.2f}s")
            logger.info(f"  Trimmed: {trim['trimmed_duration']:.2f}s")
            logger.info(f"  Trim amount: {trim['trim_amount']:.2f}s")
        
        for i, seg in enumerate(summary['segments']):
            logger.info(f"Segment {i+1}: {Path(seg['file']).name}")
            logger.info(f"  Loops: {seg['loops']} x {seg['duration']/seg['loops']:.2f}s = {seg['duration']:.2f}s")
            if seg['needs_trim']:
                logger.info(f"  [TRIMMED by {seg['trim_amount']:.2f}s]")
        
        logger.info(f"Generated concat list: {concat_file}")
        
        return concat_file
    
    def prepare_video_for_merge(self, concat_file: str,
                               output_resolution: str = "1920x1080",
                               output_fps: int = 30,
                               use_gpu: bool = True) -> List[str]:
        """
        Prepare FFmpeg command for video merging
        
        Args:
            concat_file: Path to concat list file
            output_resolution: Target resolution
            output_fps: Target FPS
            use_gpu: Whether to use GPU acceleration
            
        Returns:
            List of FFmpeg command arguments
        """
        cmd = [
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-r', str(output_fps)  # Output frame rate
        ]
        
        # Add scaling filter
        if use_gpu and self.gpu_encoder:
            scaling_filter = self.gpu_encoder.get_scaling_filter(
                output_resolution, 
                'nvenc'  # Default encoder type
            )
            cmd.extend(['-vf', scaling_filter])
        else:
            cmd.extend(['-vf', f'scale={output_resolution}'])
        
        # Add format specification
        cmd.extend([
            '-c:v', 'libx264',  # Default encoder
            '-pix_fmt', 'yuv420p',
            '-preset', 'fast',
            '-crf', '23'
        ])
        
        return cmd
    
    def generate_preview(self, segments: List[VideoSegment],
                        audio_duration: float,
                        output_path: str,
                        preview_duration: float = 30.0) -> str:
        """
        Generate preview video (first N seconds)
        
        Args:
            segments: List of video segments
            audio_duration: Total audio duration
            output_path: Output preview path
            preview_duration: Preview duration in seconds
            
        Returns:
            Path to preview video
        """
        # Create temporary concat for preview
        temp_concat = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        )
        
        try:
            # Build loop strategy
            loop_strategy = VideoLoopStrategy(min(audio_duration, preview_duration))
            timeline = loop_strategy.build_timeline(segments)
            
            # Write concat file for preview
            concat_lines = []
            accumulated_duration = 0.0
            
            for entry in timeline:
                segment = entry['segment']
                
                if entry['is_loop']:
                    loops_to_add = entry['loop_count']
                else:
                    loops_to_add = 1
                
                for _ in range(loops_to_add):
                    if accumulated_duration >= preview_duration:
                        break
                    
                    concat_lines.append(segment.get_ffmpeg_concat_entry())
                    accumulated_duration += segment.duration
                
                if accumulated_duration >= preview_duration:
                    break
            
            # Trim last segment if needed
            if accumulated_duration > preview_duration:
                excess = accumulated_duration - preview_duration
                # We'll handle this in FFmpeg command with -t
            
            temp_concat.write('\n'.join(concat_lines))
            temp_concat.close()
            
            # Build FFmpeg command
            cmd = [
                '-f', 'concat',
                '-safe', '0',
                '-i', temp_concat.name,
                '-t', str(preview_duration),  # Limit duration
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '28',
                '-c:a', 'aac',
                '-b:a', '128k',
                output_path
            ]
            
            return_code, stdout, stderr = self.ffmpeg.execute_command(cmd)
            
            if return_code != 0:
                raise RuntimeError(f"Preview generation failed: {stderr}")
            
            logger.info(f"Preview generated: {output_path}")
            return output_path
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_concat.name)
            except OSError:
                pass