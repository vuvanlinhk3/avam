"""
FFmpeg manager for detecting and executing FFmpeg commands
"""
import subprocess
import os
import sys
import json
import time
import tempfile
import re
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import logging
import shutil

logger = logging.getLogger(__name__)

class FFmpegManager:
    """Manage FFmpeg and FFprobe executables"""
    
    def __init__(self, ffmpeg_path: str = None, ffprobe_path: str = None):
        """
        Initialize FFmpeg manager
        
        Args:
            ffmpeg_path: Path to ffmpeg executable (auto-detect if None)
            ffprobe_path: Path to ffprobe executable (auto-detect if None)
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self._detect_ffmpeg()
        
    def _detect_ffmpeg(self):
        """Auto-detect FFmpeg and FFprobe"""
        if not self.ffmpeg_path:
            # Check common locations
            possible_paths = []
            
            # Check bundled ffmpeg
            if getattr(sys, 'frozen', False):
                app_dir = Path(sys.executable).parent
                possible_paths.append(app_dir / 'ffmpeg' / 'bin' / 'ffmpeg.exe')
                possible_paths.append(app_dir / 'ffmpeg.exe')
            
            # Check system PATH
            possible_paths.append('ffmpeg')
            possible_paths.append('ffmpeg.exe')
            
            for path in possible_paths:
                if self._check_executable(path):
                    self.ffmpeg_path = str(path)
                    logger.info(f"Found ffmpeg at: {self.ffmpeg_path}")
                    break
        
        if self.ffmpeg_path:
            ffmpeg_real = shutil.which(self.ffmpeg_path)
            if ffmpeg_real:
                ffmpeg_dir = Path(ffmpeg_real).parent
                for name in ("ffprobe.exe", "ffprobe"):
                    candidate = ffmpeg_dir / name
                    if candidate.exists():
                        self.ffprobe_path = str(candidate)
                        logger.info(f"Found ffprobe at: {self.ffprobe_path}")
                        break

            # 2️⃣ Nếu chưa có → thử gọi từ PATH
            if not self.ffprobe_path:
                self.ffprobe_path = "ffprobe"

        
        # Verify
        if not self._check_executable(self.ffmpeg_path):
            raise FileNotFoundError(f"FFmpeg not found at: {self.ffmpeg_path}")

        if not self._check_executable(self.ffprobe_path):
            logger.warning(f"FFprobe not found at: {self.ffprobe_path}")
        else:
            logger.info(f"FFprobe detected: {self.ffprobe_path}")

    
    def _check_executable(self, path: str) -> bool:
        """Check if executable works (PATH hoặc file)"""
        try:
            result = subprocess.run(
                [path, '-version'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0
        except Exception:
            return False

    
    def get_ffmpeg_version(self) -> str:
        """Get FFmpeg version"""
        result = subprocess.run(
            [self.ffmpeg_path, '-version'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        lines = result.stdout.split('\n')
        if lines:
            return lines[0].strip()
        return "Unknown"
    
    def get_hardware_acceleration(self) -> List[str]:
        """
        Get hardware acceleration parameters based on detected GPU
        
        Returns:
            List of hardware acceleration parameters
        """
        try:
            cmd = [self.ffmpeg_path, '-hide_banner', '-hwaccels']
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=5,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if 'cuda' in result.stdout.lower():
                logger.info("Detected CUDA hardware acceleration")
                return ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda']
            elif 'dxva2' in result.stdout.lower():
                logger.info("Detected DXVA2 hardware acceleration")
                return ['-hwaccel', 'dxva2']
            elif 'qsv' in result.stdout.lower():
                logger.info("Detected Intel QSV hardware acceleration")
                return ['-hwaccel', 'qsv']
            elif 'd3d11va' in result.stdout.lower():
                logger.info("Detected D3D11VA hardware acceleration")
                return ['-hwaccel', 'd3d11va']
            
        except Exception as e:
            logger.warning(f"Error detecting hardware acceleration: {e}")
        
        return []
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get media file information using ffprobe
        
        Returns:
            Dictionary with media information
        """
        cmd = [
            self.ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"FFprobe failed.\nCMD: {' '.join(cmd)}\nSTDERR: {result.stderr}"
                )

            if not result.stdout or not result.stdout.strip():
                raise RuntimeError(
                    f"FFprobe returned empty output.\nCMD: {' '.join(cmd)}"
                )

            info = json.loads(result.stdout)
            
            # Extract useful information
            media_info = {
                'duration': float(info['format'].get('duration', 0)),
                'size': int(info['format'].get('size', 0)),
                'format': info['format'].get('format_name', ''),
                'streams': []
            }
            
            for stream in info['streams']:
                stream_info = {
                    'codec_type': stream.get('codec_type', ''),
                    'codec_name': stream.get('codec_name', ''),
                    'width': stream.get('width', 0),
                    'height': stream.get('height', 0),
                    'r_frame_rate': stream.get('r_frame_rate', '0/0'),
                    'sample_rate': stream.get('sample_rate', 0),
                    'channels': stream.get('channels', 0),
                    'duration': float(stream.get('duration', 0)),
                    'bit_rate': stream.get('bit_rate', 0)
                }
                media_info['streams'].append(stream_info)
            
            return media_info
            
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get media info for {file_path}: {e}")
            raise
    
    def execute_command(self, cmd: List[str], timeout: int = None) -> Tuple[int, str, str]:
        """
        Execute FFmpeg command
        
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        full_cmd = [self.ffmpeg_path] + cmd
        
        logger.debug(f"Executing: {' '.join(full_cmd)}")
        
        try:
            result = subprocess.run(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Log errors if any
            if result.returncode != 0:
                logger.error(f"FFmpeg failed with return code {result.returncode}")
                logger.error(f"stderr: {result.stderr[:500]}")
            
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg command timeout: {' '.join(full_cmd)}")
            raise
        except subprocess.SubprocessError as e:
            logger.error(f"FFmpeg command failed: {e}")
            raise
    
    def execute_with_progress(self, cmd: List[str], 
                            progress_callback=None,
                            timeout: int = None) -> Tuple[int, str, str]:
        """
        Execute FFmpeg command with progress tracking
        
        Args:
            cmd: FFmpeg command arguments (without ffmpeg)
            progress_callback: Callback function for progress updates
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        full_cmd = [self.ffmpeg_path] + cmd
        
        logger.info(f"Executing FFmpeg with progress: {' '.join(full_cmd)}")
        
        # Use temporary files to avoid deadlock
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.stdout', delete=False) as stdout_file, \
             tempfile.NamedTemporaryFile(mode='w+', suffix='.stderr', delete=False) as stderr_file:
            
            stdout_path = stdout_file.name
            stderr_path = stderr_file.name
        
        try:
            # Start process
            process = subprocess.Popen(
                full_cmd,
                stdout=open(stdout_path, 'w'),
                stderr=open(stderr_path, 'w'),
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            start_time = time.time()
            
            while process.poll() is None:
                # Check timeout
                if timeout and (time.time() - start_time) > timeout:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    raise TimeoutError(f"FFmpeg execution timed out after {timeout} seconds")
                
                # Read stderr for progress
                try:
                    with open(stderr_path, 'r') as f:
                        stderr_content = f.read()
                        
                    if progress_callback and stderr_content:
                        lines = stderr_content.split('\n')
                        for line in lines:
                            if 'time=' in line:
                                # Extract time progress
                                time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
                                if time_match:
                                    hours = int(time_match.group(1))
                                    minutes = int(time_match.group(2))
                                    seconds = float(time_match.group(3))
                                    
                                    current_time = hours * 3600 + minutes * 60 + seconds
                                    
                                    # Try to get total duration from metadata
                                    # We'll pass current_time to callback, let pipeline handle %
                                    progress_callback(current_time)
                except Exception as e:
                    logger.warning(f"Error reading progress: {e}")
                
                # Small delay
                time.sleep(0.5)
            
            # Process finished, read outputs
            with open(stdout_path, 'r') as f:
                stdout = f.read()
            
            with open(stderr_path, 'r') as f:
                stderr = f.read()
            
            return_code = process.returncode
            
            if return_code != 0:
                logger.error(f"FFmpeg failed with return code {return_code}")
                logger.error(f"stderr: {stderr[:1000]}")
            
            return return_code, stdout, stderr
            
        finally:
            # Clean up temporary files
            try:
                os.unlink(stdout_path)
                os.unlink(stderr_path)
            except OSError as e:
                logger.warning(f"Failed to delete temp files: {e}")