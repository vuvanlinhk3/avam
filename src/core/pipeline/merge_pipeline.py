"""
Main pipeline for merging audio and video
"""
import os
import tempfile
import json
import random
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from ..ffmpeg.ffmpeg_manager import FFmpegManager
from ..ffmpeg.gpu_encoder import GPUEncoder
from ..ffmpeg.encoder_profiles import EncoderProfiles
from ..audio.audio_processor import AudioProcessor
from ..video.video_builder import VideoBuilder
from ..video.video_loader import VideoLoader
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
    5. Save merge info
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
    
    def _save_merge_info(self, project_config: ProjectConfig, output_path: str):
        """
        Lưu thông tin merge vào file txt
        
        Args:
            project_config: Project configuration
            output_path: Path to output video
        """
        try:
            info = project_config.generate_merge_info()
            info['output_file'] = output_path
            
            # Lấy thông tin file output
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                info['output_size'] = file_size
                info['output_size_formatted'] = self._format_size(file_size)
            
            # Tạo tên file info
            output_dir = Path(output_path).parent
            output_name = Path(output_path).stem
            info_file = output_dir / f"{output_name}_info.txt"
            
            # Ghi file info
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write(f"AVAM - Auto Video Audio Merger\n")
                f.write(f"Thông tin xuất video\n")
                f.write("="*60 + "\n\n")
                
                f.write(f"Ngày xuất: {info['timestamp']}\n")
                f.write(f"Tên project: {info['project_name']}\n")
                f.write(f"File đầu ra: {info['output_file']}\n")
                f.write(f"Kích thước: {info.get('output_size_formatted', 'N/A')}\n\n")
                
                f.write("-"*40 + "\n")
                f.write("CẤU HÌNH GHÉP:\n")
                f.write("-"*40 + "\n")
                f.write(f"• Tắt âm thanh video: {'Có' if info['settings']['mute_video_audio'] else 'Không'}\n")
                if not info['settings']['mute_video_audio']:
                    f.write(f"• Âm lượng video: {info['settings']['video_volume']}x\n")
                f.write(f"• Âm lượng audio: {info['settings']['audio_volume']}x\n")
                f.write(f"• Chuẩn hóa âm lượng: {'Có' if info['settings']['normalize_audio'] else 'Không'}\n")
                f.write(f"• Fade in: {info['settings']['fade_in']}s\n")
                f.write(f"• Fade out: {info['settings']['fade_out']}s\n")
                f.write(f"• Xáo trộn audio: {'Có' if info['settings']['shuffle_audio'] else 'Không'}\n")
                f.write(f"• Độ phân giải: {info['settings']['resolution']}\n")
                f.write(f"• FPS: {info['settings']['fps']}\n")
                f.write(f"• Chất lượng: {info['settings']['quality']}\n\n")
                
                f.write("-"*40 + "\n")
                f.write("FILE ÂM THANH (THEO THỨ TỰ GHÉP):\n")
                f.write("-"*40 + "\n")
                
                # Xác định danh sách audio files để hiển thị
                if info.get('shuffle_info') and info['shuffle_info'].get('shuffled_order'):
                    # Nếu có xáo trộn, hiển thị theo thứ tự đã xáo trộn
                    audio_files = info['shuffle_info']['shuffled_order']
                    f.write(f"(Đã xáo trộn {len(audio_files)} file)\n\n")
                else:
                    # Không xáo trộn, hiển thị theo thứ tự gốc
                    audio_files = info['audio_files']
                    f.write(f"({len(audio_files)} file)\n\n")
                
                # Hiển thị danh sách file
                for i, file_path in enumerate(audio_files, 1):
                    file_name = Path(file_path).name
                    # Thử lấy thời lượng file nếu có thể
                    try:
                        file_info = self.ffmpeg.get_media_info(file_path)
                        duration = file_info.get('duration', 0)
                        duration_str = f" ({duration:.1f}s)" if duration > 0 else ""
                    except:
                        duration_str = ""
                    f.write(f"{i:2d}. {file_name}{duration_str}\n")
                
                # Hiển thị thông tin xáo trộn chi tiết nếu có
                if info.get('shuffle_info'):
                    f.write("\n" + "-"*40 + "\n")
                    f.write("THÔNG TIN XÁO TRỘN CHI TIẾT:\n")
                    f.write("-"*40 + "\n")
                    
                    if info['shuffle_info'].get('original_order'):
                        f.write("\nThứ tự gốc:\n")
                        for i, file_path in enumerate(info['shuffle_info']['original_order'], 1):
                            file_name = Path(file_path).name
                            f.write(f"   {i:2d}. {file_name}\n")
                    
                    f.write(f"\nĐã xáo trộn {len(info['shuffle_info'].get('original_order', []))} file\n")
                
                f.write("\n" + "-"*40 + "\n")
                f.write("FILE VIDEO (THEO THỨ TỰ):\n")
                f.write("-"*40 + "\n")
                for i, file_path in enumerate(info['video_segments'], 1):
                    file_name = Path(file_path).name
                    # Thử lấy thời lượng file nếu có thể
                    try:
                        file_info = self.ffmpeg.get_media_info(file_path)
                        duration = file_info.get('duration', 0)
                        resolution = f"{file_info.get('width', 0)}x{file_info.get('height', 0)}"
                        details = f" [{resolution}, {duration:.1f}s]" if duration > 0 else ""
                    except:
                        details = ""
                    f.write(f"{i:2d}. {file_name}{details}\n")
                
                f.write("\n" + "="*60 + "\n")
                f.write("="*60 + "\n")
            
            logger.info(f"Saved merge info to: {info_file}")
            
        except Exception as e:
            logger.error(f"Failed to save merge info: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/1024**2:.1f} MB"
        else:
            return f"{size_bytes/1024**3:.1f} GB"
    
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
            
            # Áp dụng xáo trộn nếu có
            if project_config.audio_config.shuffle_audio and len(project_config.audio_config.audio_files) >= 3:
                self._apply_shuffle(project_config)
            
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
            
            # STEP 4: Save merge info
            if progress_callback:
                progress_callback(95, "Saving merge information...")
            
            self._save_merge_info(project_config, output_video)
            
            # STEP 5: Clean up
            if progress_callback:
                progress_callback(98, "Cleaning up temporary files...")
            
            self.cleanup()
            
            if progress_callback:
                progress_callback(100, f"Merge completed: {output_video}")
            
            logger.info(f"Pipeline completed successfully: {output_video}")
            return output_video
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            self.cleanup()
            raise
    
    def _apply_shuffle(self, project_config: ProjectConfig):
        """
        Áp dụng xáo trộn cho audio files
        
        Args:
            project_config: Project configuration
        """
        audio_files = project_config.audio_config.audio_files.copy()
        
        # Lưu thứ tự gốc
        project_config.audio_config.original_audio_order = audio_files.copy()
        
        # Xáo trộn
        shuffled = audio_files.copy()
        random.shuffle(shuffled)
        
        # Lưu thứ tự sau xáo trộn
        project_config.audio_config.shuffled_order = shuffled.copy()
        
        # Cập nhật audio_files với thứ tự đã xáo trộn
        project_config.audio_config.audio_files = shuffled
        
        logger.info(f"Applied shuffle to {len(audio_files)} audio files")
        logger.info(f"Original order: {[Path(f).name for f in project_config.audio_config.original_audio_order]}")
        logger.info(f"Shuffled order: {[Path(f).name for f in project_config.audio_config.shuffled_order]}")
    
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
        
        # Merge audio files với volume từ config
        logger.info(f"Merging {len(audio_config.audio_files)} audio files")
        logger.info(f"Audio volume: {audio_config.volume}x")
        
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
        
        # Get audio duration
        audio_info = self.ffmpeg.get_media_info(merged_audio_path)
        audio_duration = audio_info['duration']
        
        # Store audio duration in config
        project_config.audio_config.output_audio_path = merged_audio_path
        logger.info(f"Audio processed: {merged_audio_path}, duration: {audio_duration:.2f}s")
        
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
        
        # Tạo segments với thông tin mute và volume từ project config
        segments = []
        for i, video_info in enumerate(video_files):
            # Tạo segment với thông tin từ config
            segment = self.video_builder.create_video_segments(
                video_files=[video_info],
                positions=[project_config.video_config.video_segments[i].position.value],
                loop_behaviors=[project_config.video_config.video_segments[i].loop_behavior.value]
            )[0]
            
            # Thêm thông tin audio từ config
            segment.mute_audio = project_config.video_config.mute_all_video_audio
            segment.audio_volume = project_config.video_config.global_video_volume
            
            segments.append(segment)
        
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
        
        # Xác định có âm thanh video không
        any_video_audio = not project_config.video_config.mute_all_video_audio
        video_audio_volume = project_config.video_config.global_video_volume
        
        # Build filter complex: KHÔNG áp dụng volume lại cho audio files vì đã xử lý trong audio_processor
        if any_video_audio:
            # Có âm thanh video: mix với audio files (đã xử lý volume trong audio_processor)
            filter_complex = (
                f'[0:a:0]volume={video_audio_volume}[a0]; '
                f'[1:a:0]anull[a1]; '
                f'[a0][a1]amix=inputs=2:duration=longest:weights=1 1,'
                f'alimiter=limit=1:level=1[aout]'
            )
            logger.info(f"Video audio volume: {video_audio_volume}x (applied to video audio)")
        else:
            # Không có âm thanh video: chỉ dùng audio files, không cần volume lại
            filter_complex = '[1:a:0]alimiter=limit=1:level=1[aout]'
            logger.info("No video audio, using only external audio files")
        
        logger.info(f"Using filter_complex: {filter_complex}")
        
        # Build FFmpeg command
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
        
        # Execute FFmpeg command with progress tracking
        def progress_wrapper(current_time):
            if total_duration > 0 and progress_callback:
                progress = 50 + (current_time / total_duration) * 40
                status = f"Encoding... {current_time:.1f}/{total_duration:.1f}s"
                progress_callback(min(progress, 99), status)
        
        return_code, stdout, stderr = self.ffmpeg.execute_with_progress(
            cmd, 
            progress_callback=progress_wrapper,
            timeout=3600
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
        """Build FFmpeg command for merging"""
        cmd = []
        
        # Add hardware acceleration for decoding
        if output_config.use_gpu and self.gpu_encoder.is_gpu_available():
            cmd.extend(['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'])
        
        # Video input (concat)
        cmd.extend([
            '-f', 'concat',
            '-safe', '0',
            '-threads', '4',
            '-i', video_concat_path
        ])
        
        # Audio input
        cmd.extend(['-i', audio_path])
        
        # Add filter complex
        if filter_complex:
            cmd.extend(['-filter_complex', filter_complex])
            cmd.extend(['-map', '0:v:0', '-map', '[aout]'])
        else:
            cmd.extend(['-map', '0:v:0', '-map', '1:a?'])
        
        # Video encoding
        if output_config.use_gpu and self.gpu_encoder.is_gpu_available():
            encoder = self.gpu_encoder.get_best_encoder('h264')
            if encoder:
                quality_str = output_config.quality.value
                encoder_params = self.gpu_encoder.get_encoder_params(encoder, quality_str)
                cmd.extend(encoder_params)
            else:
                cmd.extend(self._get_software_encoder_params(output_config))
        else:
            cmd.extend(self._get_software_encoder_params(output_config))
        
        # Audio encoding
        quality_profile = EncoderProfiles.get_profile(output_config.quality)
        audio_bitrate = quality_profile.get('audio_bitrate', '192k')
        cmd.extend(['-c:a', 'aac', '-b:a', audio_bitrate])
        
        # Output settings
        cmd.extend([
            '-movflags', '+faststart',
            '-y',
            output_config.output_path
        ])
        
        return cmd
    
    def _build_gpu_optimized_command(self, audio_path: str,
                                     video_concat_path: str,
                                     output_config,
                                     filter_complex: str = None,
                                     any_video_audio: bool = True) -> List[str]:
        """Build GPU optimized command for ultra-fast encoding"""
        cmd = [
            '-hwaccel', 'cuda',
            '-hwaccel_output_format', 'cuda',
            '-f', 'concat',
            '-safe', '0',
            '-i', video_concat_path,
            '-i', audio_path,
        ]
        
        if filter_complex:
            cmd.extend(['-filter_complex', filter_complex])
            cmd.extend(['-map', '0:v:0', '-map', '[aout]'])
        else:
            cmd.extend(['-map', '0:v:0', '-map', '1:a?'])
        
        # Video encoding settings (NVENC)
        cmd.extend([
            '-c:v', 'h264_nvenc',
            '-preset', 'p1',
            '-tune', 'll',
            '-rc', 'cbr',
            '-b:v', '8M',
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
        """Get software encoder parameters"""
        quality_profile = EncoderProfiles.get_profile(output_config.quality, use_gpu=False)
        
        return [
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '23',
            '-profile:v', 'main',
            '-tune', 'fastdecode',
            '-pix_fmt', 'yuv420p',
            '-threads', '0'
        ]