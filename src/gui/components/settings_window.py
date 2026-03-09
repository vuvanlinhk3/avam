"""
Settings window component
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QComboBox, QCheckBox,
    QSpinBox, QPushButton, QGroupBox,
    QFormLayout, QFileDialog, QMessageBox
)
from PySide6.QtCore import Signal, Slot
import os
import json
from pathlib import Path

class SettingsWindow(QDialog):
    """Settings window - Quản lý cài đặt hệ thống"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_file = Path.cwd() / 'avam_settings.json'
        self.settings = self.load_settings()
        self.init_ui()
        self.load_settings_to_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Cài Đặt Hệ Thống")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        self.setup_general_tab(general_tab)
        self.tab_widget.addTab(general_tab, "Cài Đặt Chung")
        
        # FFmpeg tab
        ffmpeg_tab = QWidget()
        self.setup_ffmpeg_tab(ffmpeg_tab)
        self.tab_widget.addTab(ffmpeg_tab, "FFmpeg")
        
        # GPU tab
        gpu_tab = QWidget()
        self.setup_gpu_tab(gpu_tab)
        self.tab_widget.addTab(gpu_tab, "GPU")
        
        # UI tab
        ui_tab = QWidget()
        self.setup_ui_tab(ui_tab)
        self.tab_widget.addTab(ui_tab, "Giao Diện")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 Lưu Cài Đặt")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        
        self.cancel_button = QPushButton("❌ Hủy")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        
        self.reset_button = QPushButton("🔄 Mặc Định")
        self.reset_button.clicked.connect(self.reset_to_default)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #e67e22; }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def setup_general_tab(self, parent: QWidget):
        """Setup general settings tab"""
        layout = QFormLayout(parent)
        layout.setSpacing(15)
        
        # Default output directory
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Chọn thư mục đầu ra mặc định...")
        self.output_dir_browse = QPushButton("📁 Duyệt...")
        self.output_dir_browse.clicked.connect(self.browse_output_dir)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.output_dir_edit)
        dir_layout.addWidget(self.output_dir_browse)
        
        layout.addRow("Thư mục đầu ra mặc định:", dir_layout)
        
        # Auto save project
        self.auto_save_check = QCheckBox("Tự động lưu project khi ghép")
        layout.addRow(self.auto_save_check)
        
        # ===== THÊM CHECKBOX MỚI =====
        # Create info file after merge
        self.create_info_check = QCheckBox("Tạo file thông tin sau khi ghép (info.txt)")
        self.create_info_check.setChecked(True)  # Mặc định bật
        layout.addRow(self.create_info_check)
    
    def setup_ffmpeg_tab(self, parent: QWidget):
        """Setup FFmpeg settings tab"""
        layout = QFormLayout(parent)
        layout.setSpacing(15)
        
        # FFmpeg path
        self.ffmpeg_path_edit = QLineEdit()
        self.ffmpeg_path_edit.setPlaceholderText("Đường dẫn đến ffmpeg.exe...")
        self.ffmpeg_browse = QPushButton("📁 Duyệt...")
        self.ffmpeg_browse.clicked.connect(self.browse_ffmpeg_path)
        
        ffmpeg_layout = QHBoxLayout()
        ffmpeg_layout.addWidget(self.ffmpeg_path_edit)
        ffmpeg_layout.addWidget(self.ffmpeg_browse)
        
        layout.addRow("FFmpeg:", ffmpeg_layout)
        
        # FFprobe path
        self.ffprobe_path_edit = QLineEdit()
        self.ffprobe_path_edit.setPlaceholderText("Đường dẫn đến ffprobe.exe...")
        self.ffprobe_browse = QPushButton("📁 Duyệt...")
        self.ffprobe_browse.clicked.connect(self.browse_ffprobe_path)
        
        ffprobe_layout = QHBoxLayout()
        ffprobe_layout.addWidget(self.ffprobe_path_edit)
        ffprobe_layout.addWidget(self.ffprobe_browse)
        
        layout.addRow("FFprobe:", ffprobe_layout)
        
        # Max threads
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 32)
        self.threads_spin.setValue(4)
        self.threads_spin.setSuffix(" luồng")
        layout.addRow("Số luồng tối đa:", self.threads_spin)
    
    def setup_gpu_tab(self, parent: QWidget):
        """Setup GPU settings tab"""
        layout = QFormLayout(parent)
        layout.setSpacing(15)
        
        # GPU encoding
        self.gpu_check = QCheckBox("Bật mã hóa GPU")
        self.gpu_check.setChecked(True)
        self.gpu_check.toggled.connect(self.on_gpu_toggled)
        layout.addRow(self.gpu_check)
        
        # GPU encoder
        self.gpu_encoder_combo = QComboBox()
        self.gpu_encoder_combo.addItems(["nvenc (NVIDIA)", "qsv (Intel)", "amf (AMD)"])
        layout.addRow("Bộ mã hóa GPU:", self.gpu_encoder_combo)
        
        # GPU device
        self.gpu_device_spin = QSpinBox()
        self.gpu_device_spin.setRange(0, 8)
        self.gpu_device_spin.setValue(0)
        self.gpu_device_spin.setSuffix(" (GPU 0 = mặc định)")
        layout.addRow("Thiết bị GPU:", self.gpu_device_spin)
    
    def setup_ui_tab(self, parent: QWidget):
        """Setup UI settings tab"""
        layout = QFormLayout(parent)
        layout.setSpacing(15)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Sáng", "Tối", "Hệ thống"])
        layout.addRow("Giao diện:", self.theme_combo)
        
        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Tiếng Việt", "English"])
        layout.addRow("Ngôn ngữ:", self.language_combo)
        
        # Window behavior
        self.maximize_check = QCheckBox("Khởi động ở chế độ toàn màn hình")
        layout.addRow(self.maximize_check)
        
        # Show tooltips
        self.tooltips_check = QCheckBox("Hiển thị gợi ý")
        self.tooltips_check.setChecked(True)
        layout.addRow(self.tooltips_check)
    
    def on_gpu_toggled(self, checked):
        """Handle GPU toggle"""
        self.gpu_encoder_combo.setEnabled(checked)
        self.gpu_device_spin.setEnabled(checked)
    
    def browse_output_dir(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Chọn Thư Mục Đầu Ra Mặc Định",
            self.output_dir_edit.text() or str(Path.home())
        )
        if directory:
            self.output_dir_edit.setText(directory)
    
    def browse_ffmpeg_path(self):
        """Browse for FFmpeg executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn FFmpeg Executable",
            self.ffmpeg_path_edit.text() or "C:\\",
            "Executables (*.exe);;All Files (*.*)"
        )
        if file_path:
            self.ffmpeg_path_edit.setText(file_path)
    
    def browse_ffprobe_path(self):
        """Browse for FFprobe executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn FFprobe Executable",
            self.ffprobe_path_edit.text() or "C:\\",
            "Executables (*.exe);;All Files (*.*)"
        )
        if file_path:
            self.ffprobe_path_edit.setText(file_path)
    
    def load_settings(self) -> dict:
        """Load settings from file"""
        default_settings = {
            # General
            'output_dir': str(Path.cwd() / 'output'),
            'auto_save': True,
            'create_info_file': True,   # <-- Mặc định True
            
            # FFmpeg
            'ffmpeg_path': '',
            'ffprobe_path': '',
            'max_threads': 4,
            
            # GPU
            'use_gpu': True,
            'gpu_encoder': 'nvenc',
            'gpu_device': 0,
            
            # UI
            'theme': 'light',
            'language': 'vi',
            'window_maximized': False,
            'show_tooltips': True
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_settings.update(loaded)
                print(f"✅ Đã tải settings từ: {self.settings_file}")
            except Exception as e:
                print(f"❌ Lỗi đọc settings: {e}")
        
        return default_settings
    
    def load_settings_to_ui(self):
        """Load settings to UI"""
        # General
        self.output_dir_edit.setText(self.settings.get('output_dir', ''))
        self.auto_save_check.setChecked(self.settings.get('auto_save', True))
        self.create_info_check.setChecked(self.settings.get('create_info_file', True))  # <-- Load trạng thái
        
        # FFmpeg
        self.ffmpeg_path_edit.setText(self.settings.get('ffmpeg_path', ''))
        self.ffprobe_path_edit.setText(self.settings.get('ffprobe_path', ''))
        self.threads_spin.setValue(self.settings.get('max_threads', 4))
        
        # GPU
        self.gpu_check.setChecked(self.settings.get('use_gpu', True))
        
        gpu_map = {
            'nvenc': 0,
            'qsv': 1,
            'amf': 2
        }
        gpu_idx = gpu_map.get(self.settings.get('gpu_encoder', 'nvenc'), 0)
        self.gpu_encoder_combo.setCurrentIndex(gpu_idx)
        
        self.gpu_device_spin.setValue(self.settings.get('gpu_device', 0))
        
        # UI
        theme_map = {
            'light': 0,
            'dark': 1,
            'system': 2
        }
        theme_idx = theme_map.get(self.settings.get('theme', 'light'), 0)
        self.theme_combo.setCurrentIndex(theme_idx)
        
        lang_map = {
            'vi': 0,
            'en': 1
        }
        lang_idx = lang_map.get(self.settings.get('language', 'vi'), 0)
        self.language_combo.setCurrentIndex(lang_idx)
        
        self.maximize_check.setChecked(self.settings.get('window_maximized', False))
        self.tooltips_check.setChecked(self.settings.get('show_tooltips', True))
    
    def get_settings_from_ui(self) -> dict:
        """Get settings from UI"""
        # GPU mapping
        gpu_map = {
            0: 'nvenc',
            1: 'qsv',
            2: 'amf'
        }
        
        # Theme mapping
        theme_map = {
            0: 'light',
            1: 'dark',
            2: 'system'
        }
        
        # Language mapping
        lang_map = {
            0: 'vi',
            1: 'en'
        }
        
        return {
            # General
            'output_dir': self.output_dir_edit.text(),
            'auto_save': self.auto_save_check.isChecked(),
            'create_info_file': self.create_info_check.isChecked(),   # <-- Lấy giá trị từ UI
            
            # FFmpeg
            'ffmpeg_path': self.ffmpeg_path_edit.text(),
            'ffprobe_path': self.ffprobe_path_edit.text(),
            'max_threads': self.threads_spin.value(),
            
            # GPU
            'use_gpu': self.gpu_check.isChecked(),
            'gpu_encoder': gpu_map.get(self.gpu_encoder_combo.currentIndex(), 'nvenc'),
            'gpu_device': self.gpu_device_spin.value(),
            
            # UI
            'theme': theme_map.get(self.theme_combo.currentIndex(), 'light'),
            'language': lang_map.get(self.language_combo.currentIndex(), 'vi'),
            'window_maximized': self.maximize_check.isChecked(),
            'show_tooltips': self.tooltips_check.isChecked()
        }
    
    def save_settings(self):
        """Save settings to file"""
        try:
            settings = self.get_settings_from_ui()
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Đã lưu settings vào: {self.settings_file}")
            
            # Emit signal for main window
            self.settings_changed.emit(settings)
            
            QMessageBox.information(self, "Thành công", "Đã lưu cài đặt thành công!")
            self.accept()
            
        except Exception as e:
            print(f"❌ Lỗi lưu settings: {e}")
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu cài đặt: {str(e)}")
    
    def reset_to_default(self):
        """Reset to default settings"""
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc muốn đặt lại cài đặt mặc định?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Xóa file settings
            if self.settings_file.exists():
                self.settings_file.unlink()
            
            # Load defaults
            self.settings = self.load_settings()
            self.load_settings_to_ui()
            
            QMessageBox.information(self, "Thành công", "Đã đặt lại cài đặt mặc định!")