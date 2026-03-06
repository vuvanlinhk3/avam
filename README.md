AutoVideoAudioMerger/
│
├── ffmpeg/
│   └── bin/
│       ├── ffmpeg.exe
│       └── ffprobe.exe
│
├── src/
│   ├── __init__.py
│
│   ├── core/                         # LOGIC XỬ LÝ TRUNG TÂM
│   │   ├── __init__.py
│   │
│   │   ├── ffmpeg/                   # FFmpeg & Encoder
│   │   │   ├── __init__.py
│   │   │   ├── ffmpeg_manager.py     # Detect ffmpeg, ffprobe
│   │   │   ├── gpu_encoder.py        # NVENC / QSV / AMF
│   │   │   └── encoder_profiles.py   # Medium / High / Ultra
│   │
│   │   ├── audio/                    # XỬ LÝ ÂM THANH
│   │   │   ├── __init__.py
│   │   │   ├── audio_loader.py       # Load & validate audio
│   │   │   ├── audio_timeline.py     # Tổng thời lượng
│   │   │   └── audio_processor.py    # Concat / normalize / fade
│   │
│   │   ├── video/                    # XỬ LÝ VIDEO
│   │   │   ├── __init__.py
│   │   │   ├── video_loader.py       # Load metadata video
│   │   │   ├── video_segment.py      # Model video segment
│   │   │   ├── video_loop_strategy.py# LOGIC LẶP VIDEO
│   │   │   └── video_builder.py      # Build timeline video
│   │
│   │   ├── pipeline/                 # PIPELINE GHÉP
│   │   │   ├── __init__.py
│   │   │   ├── merge_pipeline.py     # Điều phối audio + video
│   │   │   └── progress_tracker.py   # Theo dõi tiến trình FFmpeg
│   │
│   │   └── project/                  # QUẢN LÝ PROJECT
│   │       ├── __init__.py
│   │       ├── project_config.py     # Toàn bộ config ghép
│   │       └── project_manager.py    # Save / Load project
│
│   ├── gui/                          # GIAO DIỆN QT5
│   │   ├── __init__.py
│   │   ├── loader_window.py          # Loader startup
│   │   ├── main_window.py            # Cửa sổ chính
│   │
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── navbar.py             # Thanh menu trên
│   │       ├── settings_window.py    # Cửa sổ setting
│   │       ├── audio_panel.py        # Panel audio
│   │       ├── video_panel.py        # Panel video
│   │       ├── config_panel.py       # Panel cấu hình
│   │       ├── control_panel.py      # Start / Stop
│   │       └── status_bar.py         # Progress + log
│
│   ├── utils/                        # TIỆN ÍCH
│   │   ├── __init__.py
│   │   ├── logger.py                 # Logging system
│   │   ├── config_manager.py         # Config app
│   │   ├── file_utils.py             # File helper
│   │   └── history_manager.py        # Lịch sử xuất video
│
│   └── models/                       # DATA MODEL
│       ├── __init__.py
│       └── project_config.py
│
├── output/                           # Video xuất ra
├── history/                          # Project & log
├── temp/                             # File tạm
├── logs/                             # Log runtime
│
├── run.py                            # Entry point
├── requirements.txt
└── README.md




--------------------------------------
3. CÁCH SỬ DỤNG CORE HỆ THỐNG
3.1. Khởi tạo cơ bản
python
from src.core.ffmpeg.ffmpeg_manager import FFmpegManager
from src.core.pipeline.merge_pipeline import MergePipeline
from src.core.project.project_manager import ProjectManager

# Khởi tạo FFmpeg
ffmpeg = FFmpegManager()

# Khởi tạo Project Manager
project_manager = ProjectManager()

# Tạo project mới
project = project_manager.new_project("My First Video")

# Thêm audio files
audio_files = ["song1.mp3", "song2.mp3"]
project_manager.add_audio_files(audio_files)

# Thêm video segments
video_segments = [
    {
        'file_path': 'intro.mp4',
        'position': 'start',
        'loop_behavior': 'no_loop'
    },
    {
        'file_path': 'loop.mp4',
        'position': 'middle',
        'loop_behavior': 'loop'
    }
]
project_manager.add_video_segments(video_segments)

# Cấu hình output
output_config = {
    'quality': 'high',
    'resolution': '1920x1080',
    'fps': 30,
    'output_path': 'output/final_video.mp4',
    'use_gpu': True
}
project_manager.set_output_config(output_config)

# Khởi tạo pipeline
pipeline = MergePipeline(ffmpeg)

# Chạy merge
output_video = pipeline.merge_project(project)
print(f"Video đã tạo: {output_video}")
3.2. Sử dụng Video Loop Strategy trực tiếp
python
from src.core.video.video_loop_strategy import VideoLoopStrategy
from src.core.video.video_segment import VideoSegment
from src.models.project_config import VideoPosition, LoopStrategy

# Tạo các video segments
segments = [
    VideoSegment(
        file_path="intro.mp4",
        duration=10.5,
        position=VideoPosition.START,
        loop_behavior=LoopStrategy.NO_LOOP
    ),
    VideoSegment(
        file_path="loop.mp4",
        duration=15.2,
        position=VideoPosition.MIDDLE,
        loop_behavior=LoopStrategy.LOOP
    )
]

# Tạo loop strategy với thời lượng audio 3600 giây (1 giờ)
loop_strategy = VideoLoopStrategy(audio_duration=3600)

# Xây dựng timeline
timeline = loop_strategy.build_timeline(segments)

# Xem summary
summary = loop_strategy.get_summary()
print(f"Số lần lặp: {summary['total_loops']}")
print(f"Tổng thời lượng video: {summary['video_duration']:.2f}s")
3.3. Xử lý audio riêng biệt
python
from src.core.audio.audio_processor import AudioProcessor
from src.core.ffmpeg.ffmpeg_manager import FFmpegManager

ffmpeg = FFmpegManager()
audio_processor = AudioProcessor(ffmpeg)

# Ghép audio files
audio_files = [
    {'file_path': 'track1.mp3'},
    {'file_path': 'track2.mp3'}
]

merged_audio = audio_processor.merge_audio_files(
    audio_files=audio_files,
    output_path='merged_audio.m4a',
    normalize=True,
    fade_in=1.0,
    fade_out=1.0
)



pyinstaller --noconsole --onefile --name AVAM run.py
