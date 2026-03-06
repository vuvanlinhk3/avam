"""
Video loop strategy - CORE LOGIC of AVAM
"""
from typing import List, Tuple, Dict, Any
from .video_segment import VideoSegment
from ...models.project_config import VideoPosition, LoopStrategy
import logging

logger = logging.getLogger(__name__)

class VideoLoopStrategy:
    """
    Smart video loop strategy
    
    This is the HEART of AVAM system
    """
    
    def __init__(self, audio_duration: float):
        """
        Initialize loop strategy
        
        Args:
            audio_duration: Total audio duration in seconds
        """
        self.audio_duration = audio_duration
        self.video_segments = []
        self.timeline = []
        self.trim_info = None  # Thông tin cắt ngắn đoạn cuối
    
    def build_timeline(self, video_segments: List[VideoSegment]) -> List[Dict[str, Any]]:
        """
        Build video timeline based on segments and audio duration
        
        Args:
            video_segments: List of video segments
            
        Returns:
            Timeline with video segments and loop counts
        """
        self.video_segments = sorted(video_segments, key=lambda x: x.order)
        
        # Validate we have at least one segment
        if not self.video_segments:
            raise ValueError("No video segments provided")
        
        # Apply loop strategy based on number of videos
        self._apply_loop_strategy()
        
        # Build timeline với cơ chế cắt ngắn
        self.timeline, self.trim_info = self._calculate_loops_with_trim()
        
        # Log thông tin cắt ngắn
        if self.trim_info:
            segment = self.trim_info['segment']
            trim_amount = self.trim_info['trim_amount']
            logger.info(f"Will trim last loop of segment: {segment.file_path}")
            logger.info(f"Trim amount: {trim_amount:.2f}s (from {segment.duration:.2f}s to {segment.duration - trim_amount:.2f}s)")
        
        total_video_duration = self._calculate_total_video_duration()
        logger.info(f"Built video timeline: {len(self.timeline)} entries")
        logger.info(f"Audio duration: {self.audio_duration:.2f}s, Video duration: {total_video_duration:.2f}s")
        logger.info(f"Difference: {abs(total_video_duration - self.audio_duration):.2f}s")
        
        return self.timeline
    
    def _apply_loop_strategy(self):
        """Apply loop strategy based on number of videos"""
        num_segments = len(self.video_segments)
        
        if num_segments == 1:
            # CASE 1: Only 1 video - MUST loop
            self.video_segments[0].position = VideoPosition.MIDDLE
            self.video_segments[0].loop_behavior = LoopStrategy.LOOP
            logger.info("Single video: Forced to loop")
            
        elif num_segments == 2:
            # CASE 2: 2 videos - User chooses strategy
            if (self.video_segments[0].loop_behavior == LoopStrategy.NO_LOOP and
                self.video_segments[1].loop_behavior == LoopStrategy.NO_LOOP):
                self.video_segments[1].loop_behavior = LoopStrategy.LOOP
                logger.warning("Two videos both set to no loop - forcing second to loop")
            
            # Set positions
            self.video_segments[0].position = VideoPosition.START
            self.video_segments[1].position = VideoPosition.END
            
        else:
            # CASE 3: 3+ videos - Full flexibility
            for i, segment in enumerate(self.video_segments):
                if i == 0 and segment.position == VideoPosition.MIDDLE:
                    segment.position = VideoPosition.START
                elif i == len(self.video_segments) - 1 and segment.position == VideoPosition.MIDDLE:
                    segment.position = VideoPosition.END
                elif segment.position == VideoPosition.MIDDLE:
                    segment.position = VideoPosition.MIDDLE
            
            # Middle segments must loop if set to AUTO
            for i, segment in enumerate(self.video_segments):
                if (segment.position == VideoPosition.MIDDLE and 
                    segment.loop_behavior == LoopStrategy.AUTO):
                    segment.loop_behavior = LoopStrategy.LOOP
        
        # Log final configuration
        for segment in self.video_segments:
            logger.debug(f"Segment config: {segment}")
    
    def _calculate_loops_with_trim(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Calculate loop counts with trim for perfect audio match
        
        Returns:
            Tuple of (timeline, trim_info)
        """
        timeline = []
        remaining_time = self.audio_duration
        
        # Bước 1: Thêm các segment KHÔNG lặp
        non_looping_segments = [s for s in self.video_segments if not s.should_loop]
        for segment in non_looping_segments:
            if remaining_time <= 0:
                break
                
            if segment.duration <= remaining_time:
                timeline.append({
                    'segment': segment,
                    'loop_count': 1,
                    'total_duration': segment.duration,
                    'is_loop': False,
                    'needs_trim': False
                })
                remaining_time -= segment.duration
            else:
                # Segment quá dài, cần cắt bớt
                timeline.append({
                    'segment': segment,
                    'loop_count': 1,
                    'total_duration': remaining_time,
                    'is_loop': False,
                    'needs_trim': True,
                    'trim_amount': segment.duration - remaining_time
                })
                remaining_time = 0
                break
        
        # Bước 2: Xử lý các segment CÓ lặp
        looping_segments = [s for s in self.video_segments if s.should_loop]
        
        if looping_segments and remaining_time > 0:
            # Tìm segment lặp cuối cùng để cắt ngắn (ưu tiên segment ở cuối danh sách)
            last_looping_segment = looping_segments[-1]
            
            for i, segment in enumerate(looping_segments):
                if remaining_time <= 0:
                    break
                
                is_last_looping = (i == len(looping_segments) - 1)
                
                if is_last_looping:
                    # Segment lặp cuối cùng - tính toán chính xác
                    loop_count = int(remaining_time // segment.duration)
                    last_loop_duration = remaining_time % segment.duration
                    
                    if loop_count > 0:
                        # Thêm các vòng lặp đầy đủ
                        for _ in range(loop_count - 1):
                            timeline.append({
                                'segment': segment,
                                'loop_count': 1,
                                'total_duration': segment.duration,
                                'is_loop': True,
                                'needs_trim': False
                            })
                            remaining_time -= segment.duration
                        
                        # Thêm vòng lặp cuối cùng (có thể cần cắt)
                        if last_loop_duration > 0:
                            timeline.append({
                                'segment': segment,
                                'loop_count': 1,
                                'total_duration': last_loop_duration,
                                'is_loop': True,
                                'needs_trim': True,
                                'trim_amount': segment.duration - last_loop_duration
                            })
                            trim_info = {
                                'segment': segment,
                                'trim_amount': segment.duration - last_loop_duration,
                                'original_duration': segment.duration,
                                'trimmed_duration': last_loop_duration
                            }
                            remaining_time = 0
                        else:
                            # Vòng lặp cuối cùng đầy đủ
                            timeline.append({
                                'segment': segment,
                                'loop_count': 1,
                                'total_duration': segment.duration,
                                'is_loop': True,
                                'needs_trim': False
                            })
                            remaining_time -= segment.duration
                    else:
                        # Không đủ thời gian cho một vòng lặp đầy đủ
                        timeline.append({
                            'segment': segment,
                            'loop_count': 1,
                            'total_duration': remaining_time,
                            'is_loop': True,
                            'needs_trim': True,
                            'trim_amount': segment.duration - remaining_time
                        })
                        trim_info = {
                            'segment': segment,
                            'trim_amount': segment.duration - remaining_time,
                            'original_duration': segment.duration,
                            'trimmed_duration': remaining_time
                        }
                        remaining_time = 0
                else:
                    # Segment lặp không phải cuối cùng - dùng số lần lặp nguyên
                    loop_count = int(remaining_time // segment.duration)
                    if loop_count < 1:
                        loop_count = 1
                    
                    timeline.append({
                        'segment': segment,
                        'loop_count': loop_count,
                        'total_duration': segment.duration * loop_count,
                        'is_loop': True,
                        'needs_trim': False
                    })
                    remaining_time -= segment.duration * loop_count
        
        # Sắp xếp timeline theo thứ tự ban đầu
        timeline.sort(key=lambda x: x['segment'].order)
        
        # Tính tổng thời lượng video
        total_video_duration = sum(entry['total_duration'] for entry in timeline)
        
        # Tìm thông tin cắt ngắn (nếu có)
        trim_info = None
        for entry in reversed(timeline):
            if entry.get('needs_trim', False):
                trim_info = {
                    'segment': entry['segment'],
                    'trim_amount': entry.get('trim_amount', 0),
                    'original_duration': entry['segment'].duration,
                    'trimmed_duration': entry['total_duration']
                }
                break
        
        logger.info(f"Audio duration: {self.audio_duration:.2f}s")
        logger.info(f"Video duration: {total_video_duration:.2f}s")
        logger.info(f"Remaining audio time: {remaining_time:.2f}s")
        
        return timeline, trim_info
    
    def _calculate_total_video_duration(self) -> float:
        """Calculate total duration of video timeline"""
        if not self.timeline:
            return 0.0
        return sum(entry['total_duration'] for entry in self.timeline)
    
    def generate_ffmpeg_concat_list(self, output_file: str) -> str:
        """
        Generate FFmpeg concat list file with trim support
        
        Args:
            output_file: Path to output concat list
            
        Returns:
            Path to concat list file
        """
        concat_lines = []
        
        for entry in self.timeline:
            segment = entry['segment']
            
            if entry.get('needs_trim', False):
                # Đoạn cần cắt - tạo entry với thời lượng cụ thể
                trimmed_duration = entry['total_duration']
                concat_lines.append(f"file '{segment.file_path}'")
                concat_lines.append(f"duration {trimmed_duration}")
                concat_lines.append(f"inpoint 0")
                concat_lines.append(f"outpoint {trimmed_duration}")
            else:
                # Đoạn đầy đủ - lặp lại đủ số lần
                for _ in range(entry['loop_count']):
                    concat_lines.append(segment.get_ffmpeg_concat_entry())
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(concat_lines))
        
        logger.info(f"Generated concat list with {len(concat_lines)} entries")
        if self.trim_info:
            logger.info(f"Last segment trimmed by {self.trim_info['trim_amount']:.2f}s")
        
        return output_file
    
    def get_summary(self) -> Dict[str, Any]:
        """Get timeline summary"""
        total_video_duration = self._calculate_total_video_duration()
        
        summary = {
            'audio_duration': self.audio_duration,
            'video_duration': total_video_duration,
            'duration_difference': abs(total_video_duration - self.audio_duration),
            'segment_count': len(self.timeline),
            'total_loops': sum(entry['loop_count'] for entry in self.timeline),
            'has_trim': self.trim_info is not None,
            'segments': []
        }
        
        if self.trim_info:
            summary['trim_info'] = {
                'file': self.trim_info['segment'].file_path,
                'trim_amount': self.trim_info['trim_amount'],
                'original_duration': self.trim_info['original_duration'],
                'trimmed_duration': self.trim_info['trimmed_duration']
            }
        
        for entry in self.timeline:
            segment = entry['segment']
            summary['segments'].append({
                'file': segment.file_path,
                'loops': entry['loop_count'],
                'duration': entry['total_duration'],
                'is_loop': entry['is_loop'],
                'needs_trim': entry.get('needs_trim', False),
                'trim_amount': entry.get('trim_amount', 0) if entry.get('needs_trim', False) else 0
            })
        
        return summary