"""
Settings window component
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QComboBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QPushButton, QGroupBox,
    QFormLayout, QFileDialog
)
from PySide6.QtCore import Signal, Slot

from utils.config_manager import ConfigManager

class SettingsWindow(QDialog):
    """Settings window"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config = config_manager.config
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        self.setup_general_tab(general_tab)
        self.tab_widget.addTab(general_tab, "General")
        
        # FFmpeg tab
        ffmpeg_tab = QWidget()
        self.setup_ffmpeg_tab(ffmpeg_tab)
        self.tab_widget.addTab(ffmpeg_tab, "FFmpeg")
        
        # Audio/Video tab
        media_tab = QWidget()
        self.setup_media_tab(media_tab)
        self.tab_widget.addTab(media_tab, "Audio/Video")
        
        # UI tab
        ui_tab = QWidget()
        self.setup_ui_tab(ui_tab)
        self.tab_widget.addTab(ui_tab, "UI")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
    
    def setup_general_tab(self, parent: QWidget):
        """Setup general settings tab"""
        layout = QFormLayout(parent)
        
        # Default output directory
        self.output_dir_edit = QLineEdit()
        self.output_dir_browse = QPushButton("Browse...")
        self.output_dir_browse.clicked.connect(self.browse_output_dir)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.output_dir_edit)
        dir_layout.addWidget(self.output_dir_browse)
        
        layout.addRow("Default Output Directory:", dir_layout)
        
        # Default quality
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Medium", "High", "Very High", "Ultra High"])
        
        layout.addRow("Default Quality:", self.quality_combo)
        
        # Default resolution
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920x1080 (Full HD)",
            "1280x720 (HD)",
            "3840x2160 (4K)",
            "2560x1440 (2K)"
        ])
        
        layout.addRow("Default Resolution:", self.resolution_combo)
        
        # Default FPS
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(30)
        
        layout.addRow("Default FPS:", self.fps_spin)
        
        # Enable preview
        self.enable_preview_check = QCheckBox("Enable preview generation")
        layout.addRow(self.enable_preview_check)
        
        # Preview duration
        self.preview_duration_spin = QSpinBox()
        self.preview_duration_spin.setRange(10, 300)
        self.preview_duration_spin.setSuffix(" seconds")
        
        layout.addRow("Preview Duration:", self.preview_duration_spin)
    
    def setup_ffmpeg_tab(self, parent: QWidget):
        """Setup FFmpeg settings tab"""
        layout = QFormLayout(parent)
        
        # FFmpeg path
        self.ffmpeg_path_edit = QLineEdit()
        self.ffmpeg_browse = QPushButton("Browse...")
        self.ffmpeg_browse.clicked.connect(self.browse_ffmpeg_path)
        
        ffmpeg_layout = QHBoxLayout()
        ffmpeg_layout.addWidget(self.ffmpeg_path_edit)
        ffmpeg_layout.addWidget(self.ffmpeg_browse)
        
        layout.addRow("FFmpeg Path:", ffmpeg_layout)
        
        # FFprobe path
        self.ffprobe_path_edit = QLineEdit()
        self.ffprobe_browse = QPushButton("Browse...")
        self.ffprobe_browse.clicked.connect(self.browse_ffprobe_path)
        
        ffprobe_layout = QHBoxLayout()
        ffprobe_layout.addWidget(self.ffprobe_path_edit)
        ffprobe_layout.addWidget(self.ffprobe_browse)
        
        layout.addRow("FFprobe Path:", ffprobe_layout)
        
        # GPU encoding
        self.gpu_check = QCheckBox("Enable GPU encoding")
        layout.addRow(self.gpu_check)
        
        # GPU encoder
        self.gpu_encoder_combo = QComboBox()
        self.gpu_encoder_combo.addItems(["nvenc (NVIDIA)", "qsv (Intel)", "amf (AMD)"])
        
        layout.addRow("GPU Encoder:", self.gpu_encoder_combo)
        
        # Max threads
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 32)
        self.threads_spin.setSuffix(" threads")
        
        layout.addRow("Max Threads:", self.threads_spin)
    
    def setup_media_tab(self, parent: QWidget):
        """Setup media settings tab"""
        layout = QFormLayout(parent)
        
        # Audio normalization
        self.normalize_audio_check = QCheckBox("Normalize audio volume")
        layout.addRow(self.normalize_audio_check)
        
        # Fade in/out
        self.fade_in_spin = QDoubleSpinBox()
        self.fade_in_spin.setRange(0, 10)
        self.fade_in_spin.setSuffix(" seconds")
        
        self.fade_out_spin = QDoubleSpinBox()
        self.fade_out_spin.setRange(0, 10)
        self.fade_out_spin.setSuffix(" seconds")
        
        layout.addRow("Fade In Duration:", self.fade_in_spin)
        layout.addRow("Fade Out Duration:", self.fade_out_spin)
    
    def setup_ui_tab(self, parent: QWidget):
        """Setup UI settings tab"""
        layout = QFormLayout(parent)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Dark", "Light"])
        
        layout.addRow("Theme:", self.theme_combo)
        
        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Vietnamese"])
        
        layout.addRow("Language:", self.language_combo)
        
        # Window behavior
        self.maximize_check = QCheckBox("Start maximized")
        layout.addRow(self.maximize_check)
    
    def load_settings(self):
        """Load current settings"""
        # General
        self.output_dir_edit.setText(self.config.default_output_dir)
        self.quality_combo.setCurrentText(self.config.default_quality.replace("_", " ").title())

        
        # Set resolution
        resolution_map = {
            "1920x1080": "1920x1080 (Full HD)",
            "1280x720": "1280x720 (HD)",
            "3840x2160": "3840x2160 (4K)",
            "2560x1440": "2560x1440 (2K)"
        }
        self.resolution_combo.setCurrentText(
            resolution_map.get(self.config.default_resolution, "1920x1080 (Full HD)")
        )
        
        self.fps_spin.setValue(self.config.default_fps)
        self.enable_preview_check.setChecked(self.config.enable_preview)
        self.preview_duration_spin.setValue(self.config.preview_duration)
        
        # FFmpeg
        self.ffmpeg_path_edit.setText(self.config.ffmpeg_path)
        self.ffprobe_path_edit.setText(self.config.ffprobe_path)
        self.gpu_check.setChecked(self.config.use_gpu)
        
        gpu_encoder_map = {
            "nvenc": "nvenc (NVIDIA)",
            "qsv": "qsv (Intel)",
            "amf": "amf (AMD)"
        }
        self.gpu_encoder_combo.setCurrentText(
            gpu_encoder_map.get(self.config.gpu_encoder, "nvenc (NVIDIA)")
        )
        
        self.threads_spin.setValue(self.config.max_threads)
        
        # Media
        self.normalize_audio_check.setChecked(self.config.normalize_audio)
        self.fade_in_spin.setValue(self.config.fade_in_duration)
        self.fade_out_spin.setValue(self.config.fade_out_duration)
        
        # UI
        theme_map = {
            "default": "Default",
            "dark": "Dark",
            "light": "Light"
        }
        self.theme_combo.setCurrentText(theme_map.get(self.config.theme, "Default"))
        
        language_map = {
            "en": "English",
            "vi": "Vietnamese"
        }
        self.language_combo.setCurrentText(language_map.get(self.config.language, "English"))
        
        self.maximize_check.setChecked(self.config.window_maximized)
    
    @Slot()
    def browse_output_dir(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default Output Directory",
            self.output_dir_edit.text()
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
    
    @Slot()
    def browse_ffmpeg_path(self):
        """Browse for FFmpeg executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select FFmpeg Executable",
            self.ffmpeg_path_edit.text(),
            "Executables (*.exe);;All Files (*.*)"
        )
        
        if file_path:
            self.ffmpeg_path_edit.setText(file_path)
    
    @Slot()
    def browse_ffprobe_path(self):
        """Browse for FFprobe executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select FFprobe Executable",
            self.ffprobe_path_edit.text(),
            "Executables (*.exe);;All Files (*.*)"
        )
        
        if file_path:
            self.ffprobe_path_edit.setText(file_path)
    
    @Slot()
    def save_settings(self):
        """Save settings and close"""
        if self.apply_settings():
            self.accept()
    
    @Slot()
    def apply_settings(self) -> bool:
        """Apply settings without closing"""
        try:
            # Collect settings
            settings = {
                'default_output_dir': self.output_dir_edit.text(),
                'default_quality': self.quality_combo.currentText().lower(),
                'default_resolution': self.resolution_combo.currentText().split()[0],
                'default_fps': self.fps_spin.value(),
                'enable_preview': self.enable_preview_check.isChecked(),
                'preview_duration': self.preview_duration_spin.value(),
                'ffmpeg_path': self.ffmpeg_path_edit.text(),
                'ffprobe_path': self.ffprobe_path_edit.text(),
                'use_gpu': self.gpu_check.isChecked(),
                'gpu_encoder': self.gpu_encoder_combo.currentText().split()[0].lower(),
                'max_threads': self.threads_spin.value(),
                'normalize_audio': self.normalize_audio_check.isChecked(),
                'fade_in_duration': self.fade_in_spin.value(),
                'fade_out_duration': self.fade_out_spin.value(),
                'theme': self.theme_combo.currentText().lower(),
                'language': self.language_combo.currentText()[:2].lower(),
                'window_maximized': self.maximize_check.isChecked()
            }
            
            # Emit signal for main window to update config
            self.settings_changed.emit(settings)
            
            return True
            
        except Exception as e:
            print(f"Error applying settings: {e}")
            return False