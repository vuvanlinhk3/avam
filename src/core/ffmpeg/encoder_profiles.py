"""
Encoder profiles for different quality levels
"""
from typing import Dict, List, Any
from ...models.project_config import OutputQuality
import logging

logger = logging.getLogger(__name__)

class EncoderProfiles:
    """Encoder profiles for different quality presets"""
    
    @staticmethod
    def get_profile(quality: OutputQuality, use_gpu: bool = True) -> Dict[str, Any]:
        """
        Get encoder profile for quality level
        
        Args:
            quality: Output quality level
            use_gpu: Whether to use GPU encoding
            
        Returns:
            Dictionary with encoder settings
        """
        profiles = {
            OutputQuality.ULTRA_FAST: {  # 🆕 THÊM MỚI - CẤU HÌNH CỰC NHANH
                'description': 'Fastest possible encoding',
                'video_bitrate': '8000k',
                'audio_bitrate': '128k',
                'crf': 0,  # 0 = tắt CRF, dùng bitrate cố định
                'preset': 'p1' if use_gpu else 'ultrafast',
                'tune': 'fastdecode',
                'gpu_preset': 'p1' if use_gpu else None,
                'optimize_for': 'maximum_speed'
            },
            OutputQuality.MEDIUM: {
                'description': 'Fastest encoding',
                'video_bitrate': '4000k',
                'audio_bitrate': '128k',
                'crf': 23,
                'preset': 'fast' if not use_gpu else 'medium',
                'tune': 'fastdecode',
                'gpu_preset': 'p1' if use_gpu else None,
                'optimize_for': 'speed'
            },
            OutputQuality.HIGH: {
                'description': 'Balanced quality/speed',
                'video_bitrate': '8000k',
                'audio_bitrate': '192k',
                'crf': 21,
                'preset': 'medium',
                'tune': 'film',
                'gpu_preset': 'p4' if use_gpu else None,
                'optimize_for': 'quality'
            },
            OutputQuality.VERY_HIGH: {
                'description': 'YouTube recommended',
                'video_bitrate': '12000k',
                'audio_bitrate': '256k',
                'crf': 18,
                'preset': 'slow',
                'tune': 'film',
                'gpu_preset': 'p7' if use_gpu else None,
                'optimize_for': 'quality'
            },
            OutputQuality.ULTRA_HIGH: {
                'description': 'Archive quality',
                'video_bitrate': '25000k',
                'audio_bitrate': '320k',
                'crf': 16,
                'preset': 'veryslow',
                'tune': 'film',
                'gpu_preset': 'p7' if use_gpu else None,
                'optimize_for': 'maximum_quality'
            }
        }
        
        return profiles.get(quality, profiles[OutputQuality.HIGH])
    
    @staticmethod
    def get_output_extension(codec: str = 'h264') -> str:
        """
        Get appropriate file extension for codec
        
        Args:
            codec: Video codec
            
        Returns:
            File extension
        """
        extensions = {
            'h264': '.mp4',
            'hevc': '.mp4',
            'av1': '.mp4',
            'vp9': '.webm',
            'prores': '.mov'
        }
        return extensions.get(codec, '.mp4')
    
    @staticmethod
    def get_audio_codec(quality: OutputQuality) -> str:
        """
        Get audio codec for quality level
        
        Args:
            quality: Output quality level
            
        Returns:
            Audio codec name
        """
        codecs = {
            OutputQuality.ULTRA_FAST: 'copy',
            OutputQuality.MEDIUM: 'aac',
            OutputQuality.HIGH: 'aac',
            OutputQuality.VERY_HIGH: 'aac',
            OutputQuality.ULTRA_HIGH: 'flac'
        }
        return codecs.get(quality, 'aac')