"""
Main pipeline for merging audio and video
"""
import os
import tempfile
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from ..ffmpeg.ffmpeg_manager import FFmpegManager
from ..ffmpeg.gpu_encoder import GPUEncoder
from ..ffmpeg.encoder_profiles import EncoderProfiles
from ..audio.audio_processor import AudioProcessor
from ..video.video_builder import VideoBuilder
from ..video.video_loader import VideoLoader
from ..video.video_loop_strategy import VideoLoopStrategy
from ...models.project_config import ProjectConfig, OutputQuality
import logging

logger = logging.getLogger(__name__)

class MergePipeline:
    """
    Main pipeline for merging audio and video
    
    This orchestrates the entire process:
    1. Process audio
    2. Build video timeline
    3. Merge audio and video
    4. Apply encoding settings
    """
    
    def __init__(self, ffmpeg_manager: FFmpegManager):
        """
        Initialize merge pipeline
        
        Args:
            ffmpeg_manager: FFmpegManager instance
        """
        self.ffmpeg = ffmpeg_manager
        self.gpu_encoder = GPUEncoder(ffmpeg_manager)
        self.audio_processor = AudioProcessor(ffmpeg_manager)
        self.video_builder = VideoBuilder(ffmpeg_manager, self.gpu_encoder)
        
        # Temporary files
        self.temp_files = []
    
    def __del__(self):
        """Clean up temporary files"""
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except OSError as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {e}")
        self.temp_files.clear()
    
    def _create_temp_file(self, suffix: str = '.tmp') -> str:
        """Create temporary file and track it"""
        temp_file = tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ).name
        self.temp_files.append(temp_file)
        return temp_file
    
    def merge_project(self, project_config: ProjectConfig,
                     progress_callback: Optional[Callable[[float, str], None]] = None) -> str:
        """
        Merge audio and video based on project configuration
        
        Args:
            project_config: Project configuration
            progress_callback: Callback for progress updates
            
        Returns:
            Path to output video file
        """
        try:
            # Update progress
            if progress_callback:
                progress_callback(0, "Starting merge process...")
            
            # STEP 1: Process audio
            if progress_callback:
                progress_callback(10, "Processing audio files...")
            
            merged_audio = self._process_audio(project_config)
            
            # STEP 2: Build video timeline
            if progress_callback:
                progress_callback(30, "Building video timeline...")
            
            video_concat = self._build_video_timeline(project_config, merged_audio)
            
            # STEP 3: Merge audio and video
            if progress_callback:
                progress_callback(50, "Merging audio and video...")
            
            output_video = self._merge_audio_video(
                merged_audio, 
                video_concat, 
                project_config,
                progress_callback
            )
            
            # STEP 4: Clean up
            if progress_callback:
                progress_callback(90, "Cleaning up temporary files...")
            
            self.cleanup()
            
            if progress_callback:
                progress_callback(100, f"Merge completed: {output_video}")
            
            logger.info(f"Pipeline completed successfully: {output_video}")
            return output_video
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            self.cleanup()
            raise
    
    def _process_audio(self, project_config: ProjectConfig) -> str:
        """
        Process and merge audio files
        
        Args:
            project_config: Project configuration
            
        Returns:
            Path to merged audio file
        """
        audio_config = project_config.audio_config
        output_config = project_config.output_config
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_config.output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create temporary merged audio file
        merged_audio_path = self._create_temp_file(suffix='.m4a')
        
        # Merge audio files
        logger.info(f"Merging {len(audio_config.audio_files)} audio files")
        merged_audio_path = self.audio_processor.merge_audio_files(
            audio_files=[{'file_path': path} for path in audio_config.audio_files],
            output_path=merged_audio_path,
            normalize=audio_config.normalize_volume,
            fade_in=audio_config.fade_in_duration,
            fade_out=audio_config.fade_out_duration,
            volume=audio_config.volume
        )
        
        # Verify the merged audio file
        if not os.path.exists(merged_audio_path):
            raise RuntimeError(f"Merged audio file not created: {merged_audio_path}")
        
        file_size = os.path.getsize(merged_audio_path)
        if file_size < 1024:
            logger.warning(f"Merged audio file is very small: {file_size} bytes")
        
        # Get audio duration for video loop calculation
        audio_info = self.ffmpeg.get_media_info(merged_audio_path)
        audio_duration = audio_info['duration']
        
        # Store audio duration in config for later use
        project_config.audio_config.output_audio_path = merged_audio_path
        logger.info(f"Audio processed: {merged_audio_path}, duration: {audio_duration:.2f}s, size: {file_size:,} bytes")
        
        return merged_audio_path
    
    def _build_video_timeline(self, project_config: ProjectConfig, 
                             merged_audio_path: str) -> str:
        """
        Build video timeline with loop strategy
        
        Args:
            project_config: Project configuration
            merged_audio_path: Path to merged audio file
            
        Returns:
            Path to video concat list file
        """
        # Get audio duration
        audio_info = self.ffmpeg.get_media_info(merged_audio_path)
        audio_duration = audio_info['duration']
        
        # Load video files info
        video_loader = VideoLoader(self.ffmpeg)
        video_paths = [seg.file_path for seg in project_config.video_config.video_segments]
        video_files, errors = video_loader.load_multiple_video_files(video_paths)
        
        if errors:
            logger.warning(f"Video loading errors: {errors}")
        
        # Create video segments
        segments = self.video_builder.create_video_segments(
            video_files=video_files,
            positions=[seg.position.value for seg in project_config.video_config.video_segments],
            loop_behaviors=[seg.loop_behavior.value for seg in project_config.video_config.video_segments]
        )
        
        # Build video concat list
        video_concat_path = self._create_temp_file(suffix='_video_concat.txt')
        
        concat_file = self.video_builder.build_video_concat(
            segments=segments,
            audio_duration=audio_duration,
            output_file=video_concat_path
        )
        
        logger.info(f"Video timeline built: {concat_file}")
        return concat_file
    
    def _merge_audio_video(self, merged_audio_path: str, 
                          video_concat_path: str,
                          project_config: ProjectConfig,
                          progress_callback: Optional[Callable[[float, str], None]] = None) -> str:
        """
        Merge audio and video streams
        
        Args:
            merged_audio_path: Path to merged audio file
            video_concat_path: Path to video concat list
            project_config: Project configuration
            
        Returns:
            Path to output video file
        """
        output_config = project_config.output_config
        
        # Get output path
        if not output_config.output_path:
            # Generate output path
            output_dir = Path.cwd() / 'output'
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"output_{os.getpid()}.mp4"
            output_config.output_path = str(output_path)
        
        # Ensure output directory exists
        output_dir = Path(output_config.output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get audio duration for progress calculation
        audio_info = self.ffmpeg.get_media_info(merged_audio_path)
        total_duration = audio_info['duration']
        
        # 🆕 Tính toán filter_complex dựa trên cấu hình âm lượng và mute
        any_video_audio = any(not seg.mute_audio for seg in project_config.video_config.video_segments)
        video_audio_volume = project_config.video_config.audio_volume
        audio_files_volume = project_config.audio_config.volume
        
        if any_video_audio:
            # Có âm thanh từ video
            filter_complex = (
                f'[0:a:0]volume={video_audio_volume} [a0];'
                f'[1:a:0]volume={audio_files_volume} [a1];'
                f'[a0][a1]amix=inputs=2:duration=longest:weights=1 1 [a_mix];'
                f'[a_mix]alimiter=limit=1:level=1 [aout]'
            )
        else:
            # Tất cả video đều mute, chỉ có audio files
            filter_complex = (
                f'[1:a:0]volume={audio_files_volume} [a1];'
                f'[a1]alimiter=limit=1:level=1 [aout]'
            )
        
        # Build FFmpeg command, truyền filter_complex
        if output_config.quality == OutputQuality.ULTRA_FAST:
            cmd = self._build_gpu_optimized_command(
                merged_audio_path, 
                video_concat_path, 
                output_config,
                filter_complex=filter_complex,
                any_video_audio=any_video_audio
            )
        else:
            cmd = self._build_ffmpeg_command(
                merged_audio_path, 
                video_concat_path, 
                output_config,
                filter_complex=filter_complex,
                any_video_audio=any_video_audio
            )
        
        logger.info(f"Final FFmpeg command: {' '.join(cmd)}")
        logger.info(f"Total audio duration: {total_duration:.2f}s")
        
        # Execute FFmpeg command with progress tracking
        def progress_wrapper(current_time):
            if total_duration > 0 and progress_callback:
                progress = 50 + (current_time / total_duration) * 40
                status = f"Encoding... {current_time:.1f}/{total_duration:.1f}s"
                progress_callback(min(progress, 99), status)
        
        return_code, stdout, stderr = self.ffmpeg.execute_with_progress(
            cmd, 
            progress_callback=progress_wrapper,
            timeout=3600  # 1 hour timeout
        )
        
        if return_code != 0:
            error_msg = f"FFmpeg merge failed with code {return_code}\n"
            error_msg += f"Last 500 chars of stderr: {stderr[-500:] if stderr else 'No stderr'}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Verify output file
        if not os.path.exists(output_config.output_path):
            raise RuntimeError(f"Output video file not created: {output_config.output_path}")
        
        output_size = os.path.getsize(output_config.output_path)
        logger.info(f"Merge completed: {output_config.output_path} ({output_size:,} bytes)")
        
        return output_config.output_path
    
    def _build_ffmpeg_command(self, audio_path: str, 
                             video_concat_path: str,
                             output_config,
                             filter_complex: str = None,
                             any_video_audio: bool = True) -> List[str]:
        """
        Build FFmpeg command for merging
        
        Args:
            audio_path: Path to audio file
            video_concat_path: Path to video concat list
            output_config: Output configuration
            filter_complex: Custom filter_complex string
            any_video_audio: Whether any video segment has audio enabled
            
        Returns:
            List of FFmpeg command arguments
        """
        cmd = []
        
        # Add hardware acceleration for decoding
        if output_config.use_gpu and self.gpu_encoder.is_gpu_available():
            cmd.extend(['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'])
        
        # Video input (concat)
        cmd.extend([
            '-f', 'concat',
            '-safe', '0',
            '-threads', '4',  # Parallel processing
            '-i', video_concat_path
        ])
        
        # Audio input
        cmd.extend(['-i', audio_path])
        
        # Sử dụng filter_complex được truyền vào
        if filter_complex:
            cmd.extend(['-filter_complex', filter_complex])
        else:
            # Fallback (giữ logic cũ nếu không có filter_complex)
            cmd.extend([
                '-filter_complex',
                '[0:a:0][1:a:0]amix=inputs=2:duration=longest[aout]'
            ])
        
        # Map streams
        cmd.extend(['-map', '0:v:0'])  # Luôn lấy video từ input đầu
        
        # Map audio dựa trên filter_complex
        if filter_complex and 'aout' in filter_complex:
            cmd.extend(['-map', '[aout]'])
        else:
            # Fallback: map tất cả audio streams
            cmd.extend(['-map', '0:a?', '-map', '1:a?'])
        
        # Video encoding settings - OPTIMIZED FOR SPEED
        if output_config.use_gpu and self.gpu_encoder.is_gpu_available():
            encoder = self.gpu_encoder.get_best_encoder('h264')
            
            if encoder and ('_nvenc' in encoder or '_qsv' in encoder or '_amf' in encoder):
                quality_str = output_config.quality.value.lower()
                
                # SPECIAL OPTIMIZATION FOR NVIDIA GPU
                if '_nvenc' in encoder and self.gpu_encoder.is_nvidia_gpu():
                    # Ultra-fast NVENC settings
                    cmd.extend([
                        '-c:v', encoder,
                        '-preset', 'p1',  # Fastest NVENC preset
                        '-tune', 'll',    # Low latency for speed
                        '-profile:v', 'main',
                        '-rc', 'vbr',
                        '-cq', '23',
                        '-b:v', '0',
                        '-maxrate', '10M',
                        '-bufsize', '20M',
                        '-g', '120',  # Short GOP for speed
                        '-bf', '2',
                        '-temporal-aq', '1',
                        '-spatial-aq', '1'
                    ])
                    logger.info(f"Using NVIDIA NVENC with ultra-fast preset")
                else:
                    # Other GPU encoders
                    encoder_params = self.gpu_encoder.get_encoder_params(encoder, quality_str)
                    cmd.extend(encoder_params)
                    logger.info(f"Using GPU encoder: {encoder} with quality: {quality_str}")
            else:
                cmd.extend(self._get_software_encoder_params(output_config))
                logger.warning("No hardware encoder available, using software")
        else:
            cmd.extend(self._get_software_encoder_params(output_config))
        
        # Audio encoding
        quality_profile = EncoderProfiles.get_profile(output_config.quality)
        audio_bitrate = quality_profile.get('audio_bitrate', '192k')
        cmd.extend(['-c:a', 'aac', '-b:a', audio_bitrate])
        
        # Output settings
        cmd.extend([
            '-movflags', '+faststart',  # For web playback
            '-y'  # Overwrite output file
        ])
        
        # Output file
        cmd.append(output_config.output_path)
        
        logger.debug(f"Built FFmpeg command: {' '.join(cmd)}")
        return cmd
    
    def _build_gpu_optimized_command(self, audio_path: str,
                                     video_concat_path: str,
                                     output_config,
                                     filter_complex: str = None,
                                     any_video_audio: bool = True) -> List[str]:
        """
        Build GPU optimized command for ultra-fast encoding
        
        Args:
            audio_path: Path to audio file
            video_concat_path: Path to video concat list
            output_config: Output configuration
            filter_complex: Custom filter_complex string
            any_video_audio: Whether any video segment has audio enabled
            
        Returns:
            List of FFmpeg command arguments
        """
        cmd = [
            '-hwaccel', 'cuda',              # Hardware acceleration cho decoding
            '-hwaccel_output_format', 'cuda', # Output format cho GPU
            '-f', 'concat',
            '-safe', '0',
            '-i', video_concat_path,
            '-i', audio_path,
        ]
        
        # Sử dụng filter_complex được truyền vào
        if filter_complex:
            cmd.extend(['-filter_complex', filter_complex])
        else:
            # Fallback
            cmd.extend(['-filter_complex', '[0:a:0][1:a:0]amix=inputs=2:duration=longest[aout]'])
        
        # Map streams
        cmd.extend(['-map', '0:v:0'])
        if filter_complex and 'aout' in filter_complex:
            cmd.extend(['-map', '[aout]'])
        else:
            cmd.extend(['-map', '1:a?'])
        
        # Video encoding settings (NVENC)
        cmd.extend([
            '-c:v', 'h264_nvenc',
            '-preset', 'p1',                # Fastest preset
            '-tune', 'll',                  # Low latency
            '-rc', 'cbr',                    # Constant bitrate
            '-b:v', '8M',                    # 8 Mbps
        ])
        
        # Audio encoding
        quality_profile = EncoderProfiles.get_profile(output_config.quality)
        audio_bitrate = quality_profile.get('audio_bitrate', '192k')
        cmd.extend(['-c:a', 'aac', '-b:a', audio_bitrate])
        
        # Output settings
        cmd.extend([
            '-movflags', '+faststart',
            '-threads', '0',
            '-y',
            output_config.output_path
        ])
        
        return cmd
    
    def _get_software_encoder_params(self, output_config) -> List[str]:
        """
        Get software encoder parameters - OPTIMIZED FOR SPEED
        
        Args:
            output_config: Output configuration
            
        Returns:
            List of encoder parameters
        """
        quality_profile = EncoderProfiles.get_profile(output_config.quality, use_gpu=False)
        
        # Use fastest settings for software encoding
        return [
            '-c:v', 'libx264',
            '-preset', 'ultrafast',  # Fastest software preset
            '-crf', '23',
            '-profile:v', 'main',
            '-tune', 'fastdecode',   # Optimize for fast decoding
            '-pix_fmt', 'yuv420p',
            '-threads', '0'  # Use all available CPU threads
        ]
    
    def estimate_processing_time(self, project_config: ProjectConfig) -> float:
        """
        Estimate processing time in minutes
        
        Args:
            project_config: Project configuration
            
        Returns:
            Estimated time in minutes
        """
        # Simple estimation based on audio duration and quality
        audio_duration = 0
        for path in project_config.audio_config.audio_files:
            try:
                info = self.ffmpeg.get_media_info(path)
                audio_duration += info['duration']
            except:
                pass
        
        # Quality factor
        quality_factor = {
            OutputQuality.ULTRA_FAST: 0.2,
            OutputQuality.MEDIUM: 1.0,
            OutputQuality.HIGH: 1.5,
            OutputQuality.VERY_HIGH: 2.0,
            OutputQuality.ULTRA_HIGH: 3.0
        }.get(project_config.output_config.quality, 1.5)
        
        # GPU acceleration factor
        gpu_factor = 0.3 if project_config.output_config.use_gpu else 1.0
        
        # Estimated minutes
        estimated_minutes = (audio_duration / 3600) * 60 * quality_factor * gpu_factor
        
        # Minimum 0.5 minute, maximum 5 minutes for estimation
        return max(0.5, min(5.0, estimated_minutes))