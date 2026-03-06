"""
Loader window - Startup window for AVAM
"""
import sys
import os
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QPushButton, QTextEdit, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QIcon, QPixmap

from utils.config_manager import ConfigManager, AppConfig
from utils.logger import setup_logger
from src.core.ffmpeg.ffmpeg_manager import FFmpegManager
from src.core.ffmpeg.gpu_encoder import GPUEncoder

class StartupWorker(QThread):
    """Worker thread for startup tasks"""
    
    progress = Signal(int, str)
    finished = Signal(bool, str)
    log_message = Signal(str)
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.success = False
        self.message = ""
    
    def run(self):
        """Run startup tasks"""
        try:
            # Task 1: Check FFmpeg
            self.progress.emit(10, "Checking FFmpeg...")
            self.log_message.emit("Checking FFmpeg installation...")
            
            ffmpeg_manager = FFmpegManager()
            version = ffmpeg_manager.get_ffmpeg_version()
            self.log_message.emit(f"FFmpeg version: {version}")
            
            # Task 2: Check GPU encoder
            self.progress.emit(30, "Checking GPU encoder...")
            self.log_message.emit("Checking GPU encoder availability...")
            
            gpu_encoder = GPUEncoder(ffmpeg_manager)
            if gpu_encoder.is_gpu_available():
                self.log_message.emit("GPU encoder detected")
                for encoder_type, codecs in gpu_encoder.available_encoders.items():
                    if codecs:
                        self.log_message.emit(f"  {encoder_type}: {', '.join(codecs)}")
            else:
                self.log_message.emit("GPU encoder not available, using software encoding")
            
            # Task 3: Create necessary directories
            self.progress.emit(50, "Creating directories...")
            self.log_message.emit("Creating application directories...")
            
            directories = ['output', 'temp', 'logs', 'history']
            for directory in directories:
                Path(directory).mkdir(exist_ok=True)
                self.log_message.emit(f"  Created: {directory}/")
            
            # Task 4: Load configuration
            self.progress.emit(70, "Loading configuration...")
            self.log_message.emit("Loading application configuration...")
            
            # Configuration is already loaded in main thread
            
            # Task 5: Final checks
            self.progress.emit(90, "Finalizing...")
            self.log_message.emit("Startup completed successfully!")
            
            self.success = True
            self.message = "Startup completed successfully"
            
        except Exception as e:
            self.log_message.emit(f"Error during startup: {str(e)}")
            self.success = False
            self.message = f"Startup failed: {str(e)}"
        
        finally:
            self.progress.emit(100, "Done")
            self.finished.emit(self.success, self.message)

class LoaderWindow(QMainWindow):
    """Loader window for application startup"""
    
    def __init__(self, config_manager: ConfigManager):  # SỬA: nhận ConfigManager
        super().__init__()
        self.config_manager = config_manager
        self.config = config_manager.config
        self.worker = None
        
        self.init_ui()
        self.start_startup_check()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("AVAM - Auto Video Audio Merger")
        self.setFixedSize(600, 400)
        
        # Center window
        self.center_window()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("AVAM")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50;")  # Dark blue-gray
        
        subtitle_label = QLabel("Auto Video Audio Merger")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #34495e;")  # Slightly lighter blue-gray
        
        # Progress group
        progress_group = QGroupBox("Application Startup")
        progress_layout = QVBoxLayout(progress_group)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Log area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))  # Changed to Consolas for better readability
        
        # Add widgets to progress layout
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(QLabel("Log:"))
        progress_layout.addWidget(self.log_text)
        
        # Cancel button (hidden by default)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_startup)
        
        # Add widgets to main layout
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addStretch()
        layout.addWidget(progress_group)
        layout.addWidget(self.cancel_button)
        layout.addStretch()
        
        # Set light theme style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
            QLabel {
                color: #2c3e50;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: #ffffff;
                color: #2c3e50;
                selection-background-color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5a7d;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
    
    def center_window(self):
        """Center window on screen"""
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
    
    def start_startup_check(self):
        """Start startup check in worker thread"""
        self.worker = StartupWorker(self.config)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.startup_finished)
        self.worker.log_message.connect(self.log_message)
        self.worker.start()
    
    @Slot(int, str)
    def update_progress(self, value: int, message: str):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    @Slot(str)
    def log_message(self, message: str):
        """Add message to log"""
        self.log_text.append(f"> {message}")
        # Scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    @Slot(bool, str)
    def startup_finished(self, success: bool, message: str):
        """Handle startup completion"""
        if success:
            self.log_message("Starting main application...")
            # Start main window - SỬA: truyền config_manager thay vì config
            from .main_window import MainWindow
            self.main_window = MainWindow(self.config_manager)
            self.main_window.show()
            self.close()
        else:
            self.status_label.setText(f"Error: {message}")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")  # Red for error
            self.log_message(f"Startup failed: {message}")
            self.cancel_button.setText("Exit")
            self.cancel_button.setVisible(True)
    
    def cancel_startup(self):
        """Cancel startup and exit"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        QApplication.quit()