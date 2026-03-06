"""
GPU encoder management for NVENC, QSV, AMF
"""
import subprocess
import re
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class GPUEncoder:
    """Manage GPU encoders"""
    
    def __init__(self, ffmpeg_manager):
        """
        Initialize GPU encoder
        
        Args:
            ffmpeg_manager: FFmpegManager instance
        """
        self.ffmpeg = ffmpeg_manager
        self.available_encoders = self._detect_gpu_encoders()
    
    def _detect_gpu_encoders(self) -> Dict[str, List[str]]:
        """
        Detect available GPU encoders
        
        Returns:
            Dictionary with encoder types and their codecs
        """
        encoders = {
            'nvenc': [],
            'qsv': [],
            'amf': [],
            'vaapi': []
        }
        
        try:
            # Get list of available encoders
            cmd = [self.ffmpeg.ffmpeg_path, '-encoders']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return encoders
            
            # Parse encoder list
            lines = result.stdout.split('\n')
            for line in lines:
                line_lower = line.lower()
                
                # Check for GPU encoders
                if 'nvenc' in line_lower and 'encoder' in line_lower:
                    # Extract codec name (e.g., h264_nvenc)
                    match = re.search(r'(\w+_nvenc)', line_lower)
                    if match:
                        encoders['nvenc'].append(match.group(1))
                
                elif 'qsv' in line_lower and 'encoder' in line_lower:
                    match = re.search(r'(\w+_qsv)', line_lower)
                    if match:
                        encoders['qsv'].append(match.group(1))
                
                elif 'amf' in line_lower and 'encoder' in line_lower:
                    match = re.search(r'(\w+_amf)', line_lower)
                    if match:
                        encoders['amf'].append(match.group(1))
                
                elif 'vaapi' in line_lower and 'encoder' in line_lower:
                    match = re.search(r'(\w+_vaapi)', line_lower)
                    if match:
                        encoders['vaapi'].append(match.group(1))
            
            logger.info(f"Detected GPU encoders: {encoders}")
            return encoders
            
        except subprocess.SubprocessError as e:
            logger.warning(f"Failed to detect GPU encoders: {e}")
            return encoders
    
    def get_best_encoder(self, codec: str = 'h264') -> Optional[str]:
        """
        Get the best available GPU encoder for a codec
        
        Args:
            codec: Target codec (h264, hevc, av1)
            
        Returns:
            Encoder name or None if not available
        """
        # Priority order: NVENC > QSV > AMF > VAAPI
        priority_order = ['nvenc', 'qsv', 'amf', 'vaapi']
        
        target_encoders = {
            'h264': f'{codec}_',
            'hevc': f'{codec}_',
            'av1': f'{codec}_'
        }
        
        prefix = target_encoders.get(codec, f'{codec}_')
        
        for encoder_type in priority_order:
            for available_encoder in self.available_encoders.get(encoder_type, []):
                if available_encoder.startswith(prefix):
                    return available_encoder
        
        return None
    
    def is_gpu_available(self) -> bool:
        """Check if any GPU encoder is available"""
        for encoder_list in self.available_encoders.values():
            if encoder_list:
                return True
        return False
    
    def get_encoder_params(self, encoder: str, quality_preset: str) -> List[str]:
        """
        Get encoder parameters based on encoder and quality preset
        
        Args:
            encoder: Encoder name (e.g., h264_nvenc)
            quality_preset: Quality preset (medium, high, very_high, ultra_high)
            
        Returns:
            List of FFmpeg parameters
        """
        params = []
        
        # Use fastest presets for speed optimization
        speed_presets = {
            'medium': 'p1',
            'high': 'p1',  # Use fastest preset for speed
            'very_high': 'p2',
            'ultra_high': 'p3'
        }
        # 🆕 THÊM CẤU HÌNH CHO ULTRA_FAST
        if quality_preset == 'ultra_fast' and '_nvenc' in encoder:
            return [
                '-c:v', encoder,
                '-preset', 'p1',           # Fastest NVENC preset
                '-tune', 'll',             # Low latency
                '-rc', 'cbr',              # Constant bitrate (nhanh hơn VBR)
                '-b:v', '8M',              # Bitrate cố định 8Mbps
                '-gpu', '0',              # Sử dụng GPU 0
                '-bf', '0',                # No B-frames
                '-refs', '1',              # Giảm reference frames
                '-strict_gop', '0',
                '-spatial-aq', '0',
                '-temporal-aq', '0',
                '-cq', '0',               # Tắt quality-based rate control
                '-multipass', '0'         # Single pass
            ]
        # Common parameters for all encoders
        common_params = {
            'medium': {
                'preset': 'fast',
                'tune': 'll',  # Low latency for speed
                'profile': 'main'
            },
            'high': {
                'preset': 'fast',  # Faster preset
                'tune': 'll',
                'profile': 'main'
            },
            'very_high': {
                'preset': 'medium',
                'tune': 'll',
                'profile': 'high'
            },
            'ultra_high': {
                'preset': 'slow',
                'tune': 'hq',
                'profile': 'high'
            }
        }
        
        preset_config = common_params.get(quality_preset, common_params['high'])
        
        # Encoder-specific parameters - OPTIMIZED FOR SPEED
        if '_nvenc' in encoder:
            nvenc_preset = speed_presets.get(quality_preset, 'p1')
            
            params = [
                '-c:v', encoder,
                '-preset', nvenc_preset,  # Fastest NVENC preset
                '-profile:v', preset_config['profile'],
                '-tune:v', 'll',  # Low latency mode for speed
                '-rc', 'vbr',
                '-cq', '23' if quality_preset in ['medium', 'high'] else '21',
                '-b:v', '0',
                '-maxrate', '15M' if quality_preset in ['very_high', 'ultra_high'] else '8M',
                '-bufsize', '20M',
                '-g', '120',  # Shorter GOP for faster encoding
                '-bf', '2',   # B-frames
                '-temporal-aq', '1',
                '-spatial-aq', '1'
            ]
        
        elif '_qsv' in encoder:
            qsv_preset = speed_presets.get(quality_preset, 'fast')
            params = [
                '-c:v', encoder,
                '-preset', qsv_preset,
                '-profile:v', preset_config['profile'],
                '-global_quality', '23' if quality_preset in ['medium', 'high'] else '21',
                '-look_ahead', '0'  # Disable lookahead for speed
            ]
        
        elif '_amf' in encoder:
            params = [
                '-c:v', encoder,
                '-quality', 'speed',  # Fastest quality preset
                '-profile', preset_config['profile'],
                '-rc', 'vbr_peak',
                '-qp_i', '23' if quality_preset in ['medium', 'high'] else '21',
                '-qp_p', '23' if quality_preset in ['medium', 'high'] else '21',
                '-qp_b', '23' if quality_preset in ['medium', 'high'] else '21',
                '-preanalysis', '0'  # Disable preanalysis for speed
            ]
        
        else:
            # Fallback to software encoding with speed optimizations
            params = [
                '-c:v', 'libx264' if '264' in encoder else 'libx265',
                '-preset', 'ultrafast',  # Fastest software preset
                '-crf', '23' if quality_preset in ['medium', 'high'] else '21',
                '-profile:v', preset_config['profile'],
                '-tune', 'fastdecode',  # Fast decode for speed
                '-threads', '0'  # Use all available threads
            ]
        
        return params
    
    def get_scaling_filter(self, target_resolution: str, encoder_type: str) -> str:
        """
        Get scaling filter optimized for GPU
        
        Args:
            target_resolution: Target resolution (e.g., "1920x1080")
            encoder_type: Encoder type (nvenc, qsv, amf, vaapi)
            
        Returns:
            Scaling filter string
        """
        if encoder_type == 'nvenc':
            # NVENC supports GPU scaling
            return f"scale_cuda={target_resolution}:format=yuv420p"
        
        elif encoder_type == 'qsv':
            # QSV supports GPU scaling
            return f"scale_qsv={target_resolution}:format=nv12"
        
        elif encoder_type == 'amf':
            # AMF supports GPU scaling
            return f"scale_amf={target_resolution}"
        
        elif encoder_type == 'vaapi':
            # VAAPI supports GPU scaling
            return f"scale_vaapi={target_resolution}:format=nv12"
        
        else:
            # CPU scaling with faster algorithm
            return f"scale={target_resolution}:flags=fast_bilinear"
    
    def is_nvidia_gpu(self) -> bool:
        """Check if NVIDIA GPU is available"""
        return any('_nvenc' in encoder for encoder in self.available_encoders.get('nvenc', []))