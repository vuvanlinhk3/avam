"""
GPU encoder management for NVENC, QSV, AMF - OPTIMIZED & FIXED
"""
import subprocess
import re
from typing import List, Optional, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class GPUEncoder:
    """Manage GPU encoders với cơ chế an toàn cho mọi đời card (Pascal to Ampere)"""
    
    def __init__(self, ffmpeg_manager):
        self.ffmpeg = ffmpeg_manager
        # Lưu danh sách filter để check scale_cuda
        self.supported_filters = self._detect_filters()
        self.available_encoders = self._detect_gpu_encoders()
    
    def _detect_filters(self) -> str:
        try:
            result = subprocess.run(
                [self.ffmpeg.ffmpeg_path, '-filters'],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.lower()
        except:
            return ""

    def _detect_gpu_encoders(self) -> Dict[str, List[str]]:
        encoders = {'nvenc': [], 'qsv': [], 'amf': [], 'vaapi': []}
        
        try:
            cmd = [self.ffmpeg.ffmpeg_path, '-encoders']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return encoders
            
            lines = result.stdout.split('\n')
            for line in lines:
                line_lower = line.lower()
                
                # FIX 1: Loại bỏ điều kiện 'and encoder' gây sót card
                # Dùng Regex để bắt chính xác tên codec ở cột thứ 2
                match = re.search(r'\s([a-z0-9_]+_(nvenc|qsv|amf|vaapi))', line_lower)
                if match:
                    codec_name = match.group(1)
                    if 'nvenc' in codec_name: encoders['nvenc'].append(codec_name)
                    elif 'qsv' in codec_name: encoders['qsv'].append(codec_name)
                    elif 'amf' in codec_name: encoders['amf'].append(codec_name)
                    elif 'vaapi' in codec_name: encoders['vaapi'].append(codec_name)
            
            logger.info(f"Detected GPU encoders: {encoders}")
            return encoders
            
        except Exception as e:
            logger.warning(f"Failed to detect GPU encoders: {e}")
            return encoders
    
    def get_encoder_params(self, encoder: str, quality_preset: str) -> List[str]:
        """
        Build bộ parameter an toàn cho cả 1050 Ti và 3060
        """
        params = []
        
        # FIX 2: Sử dụng mapping thông minh giữa tên cũ và tên mới
        # 'fast' là giá trị an toàn nhất, tự tương thích mọi đời Driver
        speed_presets = {
            'medium': 'fast',
            'high': 'fast',
            'very_high': 'medium',
            'ultra_high': 'slow'
        }
        
        # Đặc trị NVENC (Fix lỗi P1-P7 trên Driver cũ)
        if '_nvenc' in encoder:
            # Nếu là card đời mới, FFmpeg sẽ tự map 'fast' sang 'p1'/'p2'
            # Nếu là 1050 Ti, nó sẽ dùng đúng profile 'fast' truyền thống
            safe_preset = speed_presets.get(quality_preset, 'fast')
            
            params = [
                '-c:v', encoder,
                '-preset', safe_preset, 
                '-tune', 'll',           # Low latency cực quan trọng để tránh crash VRAM
                '-rc', 'vbr',            # Variable bitrate ổn định hơn
                '-cq', '24',
                '-pix_fmt', 'yuv420p',   # Ép về format chuẩn để tránh lỗi hiển thị
                '-temporal-aq', '0',     # FIX 3: Tắt AQ mặc định để 1050 Ti không bị quá tải
                '-spatial-aq', '0'
            ]
        
        elif '_qsv' in encoder:
            params = ['-c:v', encoder, '-preset', 'fast', '-global_quality', '23']
        elif '_amf' in encoder:
            params = ['-c:v', encoder, '-quality', 'speed', '-rc', 'vbr_peak']
        else:
            # Fallback tuyệt đối về CPU nếu không khớp cái nào
            params = ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23']
            
        return params
    
    def get_scaling_filter(self, target_resolution: str, encoder_type: str) -> str:
        """
        FIX 4: Kiểm tra scale_cuda trước khi dùng để tránh Crash
        """
        width, height = target_resolution.split('x')
        
        if encoder_type == 'nvenc' and 'scale_cuda' in self.supported_filters:
            # Chỉ dùng nếu FFmpeg build có hỗ trợ và máy có CUDA
            return f"scale_cuda={width}:{height}:format=yuv420p"
        
        # An toàn nhất cho mọi máy (Dùng CPU Scaling)
        return f"scale={width}:{height},format=yuv420p"

    # Các hàm bổ trợ giữ nguyên từ code cũ của bạn
    def get_best_encoder(self, codec: str = 'h264') -> Optional[str]:
        priority_order = ['nvenc', 'qsv', 'amf', 'vaapi']
        for type_ in priority_order:
            for enc in self.available_encoders.get(type_, []):
                if enc.startswith(codec): return enc
        return None

    def is_gpu_available(self) -> bool:
        return any(len(lst) > 0 for lst in self.available_encoders.values())