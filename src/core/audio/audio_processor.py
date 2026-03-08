"""
Audio processing and merging
"""
import os
import tempfile
import shutil
import subprocess
from typing import List, Dict, Any
from pathlib import Path
from ..ffmpeg.ffmpeg_manager import FFmpegManager
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Process and merge audio files"""
    
    def __init__(self, ffmpeg_manager: FFmpegManager):
        self.ffmpeg = ffmpeg_manager
        self.temp_files = []
    
    def __del__(self):
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except OSError as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {e}")
        self.temp_files.clear()
    
    def _create_temp_file(self, suffix: str = '.tmp') -> str:
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False).name
        self.temp_files.append(temp_file)
        return temp_file
    
    def merge_audio_files(self, 
                         audio_files: List[Dict[str, Any]],
                         output_path: str,
                         normalize: bool = True,
                         fade_in: float = 0.0,
                         fade_out: float = 0.0,
                         volume: float = 1.0) -> str:
        """
        Merge multiple audio files into one, then:
        1. Apply volume and normalize (if enabled)
        2. Apply fade in/out as the final step
        """
        logger.info(f"Starting audio merge: {len(audio_files)} files to {output_path}")
        logger.info(f"Params: normalize={normalize}, fade_in={fade_in}s, fade_out={fade_out}s, volume={volume}")
        
        for i, audio_item in enumerate(audio_files):
            logger.info(f"  [{i+1}] {audio_item.get('file_path', 'Unknown')}")
        
        # Bước 1: Tạo file concat list
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding="utf-8") as f:
            concat_file = f.name
            for audio_item in audio_files:
                file_path = audio_item['file_path'].replace("\\", "/")
                file_path = file_path.replace("'", "'\\''")
                f.write(f"file '{file_path}'\n")
        
        try:
            # Bước 2: Concatenate các file audio (copy stream) -> file .mp3 tạm
            concat_output = self._create_temp_file(suffix='_concat.mp3')
            cmd_concat = [
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c:a', 'copy',
                '-y', concat_output
            ]
            logger.info(f"Concatenating audio with command: ffmpeg {' '.join(cmd_concat)}")
            return_code, stdout, stderr = self.ffmpeg.execute_command(cmd_concat)
            if return_code != 0:
                raise RuntimeError(f"Concat failed: {stderr}")
            
            # Lấy thời lượng file đã concat
            info = self.ffmpeg.get_media_info(concat_output)
            total_duration = info['duration']
            logger.info(f"Concatenated audio duration: {total_duration:.2f}s")
            
            # Bước 3: Xác định codec cho output cuối cùng
            out_ext = os.path.splitext(output_path)[1].lower()
            if out_ext == '.mp3':
                codec = 'libmp3lame'
                bitrate = '192k'
            else:
                codec = 'aac'
                bitrate = '192k'
                if out_ext not in ['.m4a', '.aac']:
                    output_path = os.path.splitext(output_path)[0] + '.m4a'
                    logger.info(f"Adjusted output path to: {output_path}")
            
            # Bước 4: Xử lý volume và normalize (nếu có) -> file tạm thứ hai
            need_volume_normalize = (volume != 1.0) or normalize
            if need_volume_normalize:
                filter_parts = []
                if volume != 1.0:
                    filter_parts.append(f'volume={volume}')
                if normalize:
                    filter_parts.append('loudnorm')
                filter_str = ",".join(filter_parts)
                
                processed_temp = self._create_temp_file(suffix='_processed.m4a')
                cmd_process = [
                    '-i', concat_output,
                    '-af', filter_str,
                    '-c:a', codec,
                    '-b:a', bitrate,
                    '-y', processed_temp
                ]
                logger.info(f"Applying volume/normalize with command: ffmpeg {' '.join(cmd_process)}")
                full_cmd = [self.ffmpeg.ffmpeg_path] + cmd_process
                result = subprocess.run(full_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if result.returncode != 0:
                    logger.error(f"Volume/normalize command failed: {result.stderr}")
                    raise RuntimeError(f"Volume/normalize failed: {result.stderr}")
                logger.info("Volume/normalize succeeded.")
                input_for_fade = processed_temp
            else:
                input_for_fade = concat_output
            
            # Bước 5: Áp dụng fade (nếu có) - là bước cuối cùng
            need_fade = (fade_in > 0) or (fade_out > 0)
            if need_fade:
                # Lấy thời lượng của file hiện tại (có thể đã được xử lý)
                if need_volume_normalize:
                    # Lấy duration từ file processed_temp
                    info_fade = self.ffmpeg.get_media_info(input_for_fade)
                    current_duration = info_fade['duration']
                else:
                    current_duration = total_duration
                
                fade_parts = []
                if fade_in > 0:
                    fade_parts.append(f'afade=t=in:st=0:d={fade_in}')
                if fade_out > 0:
                    fade_out_start = max(0, current_duration - fade_out)
                    fade_parts.append(f'afade=t=out:st={fade_out_start}:d={fade_out}')
                fade_str = ",".join(fade_parts)
                
                # Áp dụng fade lên input_for_fade, xuất thẳng ra output_path
                cmd_fade = [
                    '-i', input_for_fade,
                    '-af', fade_str,
                    '-c:a', codec,
                    '-b:a', bitrate,
                    '-y', output_path
                ]
                logger.info(f"Applying fade with command: ffmpeg {' '.join(cmd_fade)}")
                full_cmd = [self.ffmpeg.ffmpeg_path] + cmd_fade
                result = subprocess.run(full_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if result.returncode != 0:
                    logger.error(f"Fade command failed: {result.stderr}")
                    raise RuntimeError(f"Fade failed: {result.stderr}")
                logger.info("Fade succeeded.")
            else:
                # Không cần fade, copy input_for_fade đến output_path
                shutil.copy2(input_for_fade, output_path)
                logger.info("No fade, copied file directly.")
            
            # Kiểm tra file output
            if not os.path.exists(output_path):
                raise RuntimeError(f"Output file not created: {output_path}")
            
            file_size = os.path.getsize(output_path)
            logger.info(f"Audio processed and saved to: {output_path} ({file_size:,} bytes)")
            
            # Kiểm tra duration cuối
            try:
                final_info = self.ffmpeg.get_media_info(output_path)
                final_duration = final_info.get('duration', 0)
                logger.info(f"Final audio duration: {final_duration:.2f}s")
            except Exception as e:
                logger.warning(f"Could not get duration of final file: {e}")
            
            return output_path
            
        finally:
            # Dọn dẹp file concat list
            try:
                if os.path.exists(concat_file):
                    os.unlink(concat_file)
            except OSError as e:
                logger.warning(f"Failed to delete temp file {concat_file}: {e}")
            # Các file tạm khác sẽ tự xóa khi instance bị hủy
    
    # Các phương thức khác giữ nguyên (normalize_audio, apply_fade, trim_audio, convert_format)
    def normalize_audio(self, input_path: str, output_path: str) -> str:
        """Normalize audio volume using loudnorm"""
        cmd = [
            '-i', input_path,
            '-af', 'loudnorm',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-threads', '4',
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
        """Apply fade-in and fade-out to audio"""
        info = self.ffmpeg.get_media_info(input_path)
        duration = info['duration']
        fade_filters = []
        if fade_in > 0:
            fade_filters.append(f'afade=t=in:st=0:d={fade_in}')
        if fade_out > 0:
            fade_out_start = max(0, duration - fade_out)
            fade_filters.append(f'afade=t=out:st={fade_out_start}:d={fade_out}')
        if not fade_filters:
            cmd = ['-i', input_path, '-c:a', 'copy', '-y', output_path]
        else:
            filter_str = ",".join(fade_filters)
            cmd = [
                '-i', input_path,
                '-af', filter_str,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-threads', '4',
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
        """Trim audio file"""
        cmd = ['-i', input_path]
        if start_time > 0:
            cmd.extend(['-ss', str(start_time)])
        if duration:
            cmd.extend(['-t', str(duration)])
        cmd.extend(['-c:a', 'copy', '-y', output_path])
        return_code, stdout, stderr = self.ffmpeg.execute_command(cmd)
        if return_code != 0:
            raise RuntimeError(f"Audio trim failed: {stderr[:500]}")
        logger.info(f"Trimmed audio saved to: {output_path}")
        return output_path
    
    def convert_format(self, input_path: str, output_path: str,
                      target_format: str = 'aac') -> str:
        """Convert audio format"""
        format_map = {
            'aac': ['-c:a', 'aac', '-b:a', '192k'],
            'mp3': ['-c:a', 'libmp3lame', '-b:a', '192k'],
            'wav': ['-c:a', 'pcm_s16le']
        }
        cmd = ['-i', input_path]
        if target_format in format_map:
            cmd.extend(format_map[target_format])
        else:
            cmd.extend(['-c:a', 'copy'])
        cmd.extend(['-threads', '4', '-y', output_path])
        return_code, stdout, stderr = self.ffmpeg.execute_command(cmd)
        if return_code != 0:
            raise RuntimeError(f"Audio conversion failed: {stderr[:500]}")
        logger.info(f"Converted audio saved to: {output_path}")
        return output_path