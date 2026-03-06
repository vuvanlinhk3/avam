"""
Audio processing and merging
"""
import os
import tempfile
from typing import List, Dict, Any
from pathlib import Path
from ..ffmpeg.ffmpeg_manager import FFmpegManager
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Process and merge audio files"""
    
    def __init__(self, ffmpeg_manager: FFmpegManager):
        """
        Initialize audio processor
        
        Args:
            ffmpeg_manager: FFmpegManager instance
        """
        self.ffmpeg = ffmpeg_manager
    
    def merge_audio_files(self, 
                         audio_files: List[Dict[str, Any]],
                         output_path: str,
                         normalize: bool = True,
                         fade_in: float = 0.0,
                         fade_out: float = 0.0) -> str:
        """
        Merge multiple audio files into one
        
        Args:
            audio_files: List of audio information dictionaries
            output_path: Output file path
            normalize: Whether to normalize volume
            fade_in: Fade-in duration in seconds
            fade_out: Fade-out duration in seconds
            
        Returns:
            Path to merged audio file
        """
        logger.info(f"Starting audio merge: {len(audio_files)} files to {output_path}")
        
        # Debug: Log all files being processed
        logger.info("Files to merge:")
        for i, audio_item in enumerate(audio_files):
            logger.info(f"  [{i+1}] {audio_item.get('file_path', 'Unknown')}")
        
        # Create temporary concat list
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding="utf-8") as f:
            concat_file = f.name
            for audio_item in audio_files:
                file_path = audio_item['file_path'].replace("\\", "/")
                # Escape single quotes in file path
                file_path = file_path.replace("'", "'\\''")
                f.write(f"file '{file_path}'\n")
        
        try:
            # Build FFmpeg command with parallel processing
            # Kiểm tra có cần filter không
            need_filter = normalize or fade_in > 0 or fade_out > 0
            
            if not need_filter:
                # KHÔNG CẦN FILTER → COPY AUDIO, KHÔNG RE-ENCODE
                cmd = [
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', concat_file,
                    '-c:a', 'copy',  # 🚀 COPY THAY VÌ RE-ENCODE
                    '-y', output_path
                ]
                logger.info("Audio merge: using copy (no re-encoding)")
            else:
                # CẦN FILTER → PHẢI RE-ENCODE
                cmd = [
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', concat_file,
                    '-c:a', 'aac',
                    '-b:a', '192k'
                ]
                
                # Apply filters if needed
                filter_complex = []
                
                if normalize:
                    filter_complex.append('loudnorm')
                
                if fade_in > 0:
                    filter_complex.append(f'afade=t=in:st=0:d={fade_in}')
                
                if fade_out > 0:
                    # Calculate total duration for fade-out
                    durations = []
                    
                    for audio_item in audio_files:
                        audio_path = audio_item.get("file_path")
                        if not audio_path:
                            logger.error(f"Audio object missing file_path: {audio_item}")
                            continue
                        
                        try:
                            info = self.ffmpeg.get_media_info(audio_path)
                            duration = info.get("duration", 0)
                            durations.append(duration)
                        except Exception as e:
                            logger.error(f"Error getting duration for {audio_path}: {e}")
                            durations.append(30.0)
                    
                    if durations:
                        total_duration = sum(durations)
                        fade_out_start = max(0, total_duration - fade_out)
                        filter_complex.append(f'afade=t=out:st={fade_out_start}:d={fade_out}')
                    else:
                        logger.warning("Could not calculate fade-out, no valid durations")
                
                if filter_complex:
                    cmd.extend(['-filter_complex', ','.join(filter_complex)])
                
                cmd.extend(['-y', output_path])
            
            logger.debug(f"Audio merge command: {' '.join(cmd)}")
            
            # Execute FFmpeg command
            return_code, stdout, stderr = self.ffmpeg.execute_command(cmd)
            
            if return_code != 0:
                error_msg = f"Audio merge failed: {stderr[:500]}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Verify output file
            if not os.path.exists(output_path):
                raise RuntimeError(f"Output file not created: {output_path}")
            
            file_size = os.path.getsize(output_path)
            if file_size < 1024:
                logger.warning(f"Output audio file is very small: {file_size} bytes")
            
            logger.info(f"Merged audio saved to: {output_path} ({file_size:,} bytes)")
            return output_path
            
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(concat_file):
                    os.unlink(concat_file)
            except OSError as e:
                logger.warning(f"Failed to delete temp file {concat_file}: {e}")
    
    def normalize_audio(self, input_path: str, output_path: str) -> str:
        """
        Normalize audio volume using loudnorm
        
        Args:
            input_path: Input audio file path
            output_path: Output audio file path
            
        Returns:
            Path to normalized audio file
        """
        cmd = [
            '-i', input_path,
            '-af', 'loudnorm',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-threads', '4',  # Parallel processing
            '-y',
            output_path
        ]
        
        return_code, stdout, stderr = self.ffmpeg.execute_command(cmd)
        
        if return_code != 0:
            raise RuntimeError(f"Audio normalization failed: {stderr[:500]}")
        
        logger.info(f"Normalized audio saved to: {output_path}")
        return output_path
    
    def apply_fade(self, input_path: str, output_path: str, 
                  fade_in: float = 0.0, fade_out: float = 0.0) -> str:
        """
        Apply fade-in and fade-out to audio
        
        Args:
            input_path: Input audio file path
            output_path: Output audio file path
            fade_in: Fade-in duration in seconds
            fade_out: Fade-out duration in seconds
            
        Returns:
            Path to processed audio file
        """
        # Get audio duration
        info = self.ffmpeg.get_media_info(input_path)
        duration = info['duration']
        
        # Build fade filter
        fade_filters = []
        
        if fade_in > 0:
            fade_filters.append(f'afade=t=in:st=0:d={fade_in}')
        
        if fade_out > 0:
            fade_out_start = max(0, duration - fade_out)
            fade_filters.append(f'afade=t=out:st={fade_out_start}:d={fade_out}')
        
        if not fade_filters:
            # No fade needed, just copy
            cmd = ['-i', input_path, '-c:a', 'copy', '-y', output_path]
        else:
            cmd = [
                '-i', input_path,
                '-af', ','.join(fade_filters),
                '-c:a', 'aac',
                '-b:a', '192k',
                '-threads', '4',  # Parallel processing
                '-y',
                output_path
            ]
        
        return_code, stdout, stderr = self.ffmpeg.execute_command(cmd)
        
        if return_code != 0:
            raise RuntimeError(f"Fade application failed: {stderr[:500]}")
        
        logger.info(f"Fade applied, saved to: {output_path}")
        return output_path
    
    def trim_audio(self, input_path: str, output_path: str,
                  start_time: float = 0.0, duration: float = None) -> str:
        """
        Trim audio file
        
        Args:
            input_path: Input audio file path
            output_path: Output audio file path
            start_time: Start time in seconds
            duration: Duration in seconds (None for until end)
            
        Returns:
            Path to trimmed audio file
        """
        cmd = ['-i', input_path]
        
        if start_time > 0:
            cmd.extend(['-ss', str(start_time)])
        
        if duration:
            cmd.extend(['-t', str(duration)])
        
        cmd.extend(['-c:a', 'copy', '-y', output_path])  # Copy audio stream
        
        return_code, stdout, stderr = self.ffmpeg.execute_command(cmd)
        
        if return_code != 0:
            raise RuntimeError(f"Audio trim failed: {stderr[:500]}")
        
        logger.info(f"Trimmed audio saved to: {output_path}")
        return output_path
    
    def convert_format(self, input_path: str, output_path: str,
                      target_format: str = 'aac') -> str:
        """
        Convert audio format
        
        Args:
            input_path: Input audio file path
            output_path: Output audio file path
            target_format: Target format (aac, mp3, wav)
            
        Returns:
            Path to converted audio file
        """
        format_map = {
            'aac': ['-c:a', 'aac', '-b:a', '192k'],
            'mp3': ['-c:a', 'libmp3lame', '-b:a', '192k'],
            'wav': ['-c:a', 'pcm_s16le']
        }
        
        cmd = ['-i', input_path]
        
        if target_format in format_map:
            cmd.extend(format_map[target_format])
        else:
            cmd.extend(['-c:a', 'copy'])  # Copy if format not specified
        
        cmd.extend(['-threads', '4', '-y', output_path])
        
        return_code, stdout, stderr = self.ffmpeg.execute_command(cmd)
        
        if return_code != 0:
            raise RuntimeError(f"Audio conversion failed: {stderr[:500]}")
        
        logger.info(f"Converted audio saved to: {output_path}")
        return output_path