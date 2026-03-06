"""
Status bar component
"""
from PySide6.QtWidgets import (
    QStatusBar, QLabel, QProgressBar, QHBoxLayout,
    QWidget, QPushButton
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

class StatusBar(QStatusBar):
    """Custom status bar with additional features"""
    
    log_button_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setContentsMargins(6, 2, 6, 2)  # Giảm margin
        self.setFixedHeight(26)  # Cố định chiều cao thấp
        
        # Layout chính
        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Message label
        self.message_label = QLabel("Ready")
        self.message_label.setMinimumWidth(180)
        self.message_label.setMaximumWidth(300)
        
        # Progress indicator
        self.progress_indicator = QProgressBar()
        self.progress_indicator.setRange(0, 100)
        self.progress_indicator.setValue(0)
        self.progress_indicator.setFixedWidth(120)
        self.progress_indicator.setFixedHeight(14)
        self.progress_indicator.setTextVisible(False)
        self.progress_indicator.setVisible(False)
        
        # Status indicators (gọn hơn)
        self.ffmpeg_label = QLabel("FFmpeg")
        self.ffmpeg_label.setToolTip("FFmpeg status")
        self.ffmpeg_label.setFixedWidth(55)
        
        self.gpu_label = QLabel("GPU")
        self.gpu_label.setToolTip("GPU encoder status")
        self.gpu_label.setFixedWidth(60)
        
        self.memory_label = QLabel("RAM")
        self.memory_label.setToolTip("Memory usage")
        self.memory_label.setFixedWidth(60)
        
        # Log button nhỏ hơn
        self.log_button = QPushButton("Log")
        self.log_button.setFixedWidth(60)
        self.log_button.setFixedHeight(18)
        self.log_button.clicked.connect(self.log_button_clicked)
        
        # Thêm vào layout
        layout.addWidget(self.message_label)
        layout.addWidget(self.progress_indicator)
        layout.addStretch()
        layout.addWidget(self.ffmpeg_label)
        layout.addWidget(self.gpu_label)
        layout.addWidget(self.memory_label)
        layout.addWidget(self.log_button)
        
        self.addWidget(main_widget)
        
        # Set style
        self.setStyleSheet("""
            QStatusBar {
                background-color: #ecf0f1;
                border-top: 1px solid #bdc3c7;
                font-size: 10px;
            }
            QLabel {
                color: #2c3e50;
                padding: 0 1px;
                font-size: 10px;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 2px;
                background-color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 2px;
            }
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 2px;
                padding: 1px 6px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
    
    def show_message(self, message: str, timeout: int = 0):
        """Show message in status bar"""
        super().showMessage(message, timeout)
        self.message_label.setText(message)
    
    def update_progress(self, percent: int):
        """Update progress indicator"""
        self.progress_indicator.setValue(percent)
        self.progress_indicator.setVisible(percent > 0 and percent < 100)
    
    def set_ffmpeg_status(self, ok: bool, message: str = ""):
        """Set FFmpeg status"""
        if ok:
            self.ffmpeg_label.setText("FFmpeg ✓")
            self.ffmpeg_label.setStyleSheet("color: #27ae60;")
        else:
            self.ffmpeg_label.setText("FFmpeg ✗")
            self.ffmpeg_label.setStyleSheet("color: #e74c3c;")
            if message:
                self.ffmpeg_label.setToolTip(message)
    
    def set_gpu_status(self, available: bool, encoder: str = ""):
        """Set GPU status"""
        if available:
            text = encoder[:8] + "..." if len(encoder) > 8 else encoder
            self.gpu_label.setText(f"GPU: {text}" if text else "GPU ✓")
            self.gpu_label.setStyleSheet("color: #27ae60;")
        else:
            self.gpu_label.setText("GPU ✗")
            self.gpu_label.setStyleSheet("color: #e74c3c;")
    
    def update_memory_usage(self):
        """Update memory usage display"""
        try:
            import psutil
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            if memory_mb < 1024:
                self.memory_label.setText(f"RAM: {memory_mb:.0f}M")
            else:
                self.memory_label.setText(f"RAM: {memory_mb/1024:.1f}G")
        except:
            self.memory_label.setText("RAM: --")
    
    def clear_message(self):
        """Clear current message"""
        super().clearMessage()
        self.message_label.setText("Ready")