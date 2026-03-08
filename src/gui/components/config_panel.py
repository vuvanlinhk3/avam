"""
Configuration panel component
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QLineEdit, QPushButton, QFormLayout, QFileDialog,
    QRadioButton, QButtonGroup, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QIntValidator, QPalette
import os
import json
import random
from datetime import datetime
from pathlib import Path
from utils.config_manager import ConfigManager

class ConfigPanel(QWidget):
    """Panel cấu hình cho thiết lập đầu ra"""
    
    config_changed = Signal(dict)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.app_config = config_manager.config if config_manager else None
        self.init_ui()
        self.load_saved_config()
    
    def init_ui(self):
        """Khởi tạo giao diện"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Tiêu đề
        title_label = QLabel("Cấu Hình Đầu Ra")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50;")
        
        # Tạo vùng cuộn cho cài đặt
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Container cho cài đặt
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        settings_layout.setSpacing(15)
        
        # ===== NHÓM CÀI ĐẶT VIDEO =====
        video_group = QGroupBox("Cài Đặt Video")
        video_layout = QFormLayout(video_group)
        
        # Xóa âm thanh video - Cải thiện style
        self.mute_video_check = QCheckBox("Xóa âm thanh khỏi video")
        self.mute_video_check.setChecked(False)
        self.mute_video_check.toggled.connect(self.on_video_audio_toggled)
        self.mute_video_check.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #3498db;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0iI2ZmZmZmZiI+PHBhdGggZD0iTTEyLjcgNS4zTDcgMTAuN0wzLjMgN2wtMS40IDEuNEw3IDEzLjVsNy4xLTcuMS0xLjQtMS40eiIvPjwvc3ZnPg==);
            }
            QCheckBox::indicator:hover {
                border: 2px solid #2980b9;
                background-color: #ecf0f1;
            }
        """)
        
        # Âm lượng video (chỉ enabled khi không mute)
        self.video_volume_spin = QDoubleSpinBox()
        self.video_volume_spin.setRange(0.0, 10.0)
        self.video_volume_spin.setValue(1.0)
        self.video_volume_spin.setSingleStep(0.1)
        self.video_volume_spin.setSuffix("x")
        self.video_volume_spin.setToolTip("0.0 = Tắt tiếng, 1.0 = Âm lượng gốc, >1.0 = Tăng âm lượng")
        self.video_volume_spin.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                min-height: 25px;
                font-weight: bold;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #3498db;
            }
        """)
        
        video_layout.addRow(self.mute_video_check)
        video_layout.addRow("Âm lượng video:", self.video_volume_spin)
        
        # Độ phân giải
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920x1080 (Full HD)",
            "1280x720 (HD)",
            "3840x2160 (4K)",
            "2560x1440 (2K)",
            "854x480 (480p)",
            "640x360 (360p)"
        ])
        self.resolution_combo.setCurrentText("1920x1080 (Full HD)")
        self.resolution_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                min-height: 25px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #2c3e50;
                margin-right: 5px;
            }
        """)
        
        # FPS
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)
        self.fps_spin.setSuffix(" FPS")
        self.fps_spin.setStyleSheet("""
            QSpinBox {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                min-height: 25px;
            }
            QSpinBox:focus {
                border: 2px solid #3498db;
            }
        """)
        
        video_layout.addRow("Độ phân giải:", self.resolution_combo)
        video_layout.addRow("Tốc độ khung hình:", self.fps_spin)
        
        # ===== NHÓM CÀI ĐẶT ÂM THANH NGOÀI =====
        audio_group = QGroupBox("Cài Đặt Âm Thanh")
        audio_layout = QFormLayout(audio_group)
        
        # Âm lượng
        self.audio_volume_spin = QDoubleSpinBox()
        self.audio_volume_spin.setRange(0.0, 10.0)
        self.audio_volume_spin.setValue(1.0)
        self.audio_volume_spin.setSingleStep(0.1)
        self.audio_volume_spin.setSuffix("x")
        self.audio_volume_spin.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                min-height: 25px;
                font-weight: bold;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #3498db;
            }
        """)
        
        audio_layout.addRow("Âm lượng:", self.audio_volume_spin)
        
        # Chuẩn hóa âm lượng
        self.normalize_check = QCheckBox("Chuẩn hóa âm lượng")
        self.normalize_check.setChecked(True)
        self.normalize_check.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #3498db;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0iI2ZmZmZmZiI+PHBhdGggZD0iTTEyLjcgNS4zTDcgMTAuN0wzLjMgN2wtMS40IDEuNEw3IDEzLjVsNy4xLTcuMS0xLjQtMS40eiIvPjwvc3ZnPg==);
            }
            QCheckBox::indicator:hover {
                border: 2px solid #2980b9;
                background-color: #ecf0f1;
            }
        """)
        
        # Fade In/Out
        self.fade_in_spin = QDoubleSpinBox()
        self.fade_in_spin.setRange(0, 10)
        self.fade_in_spin.setValue(1.0)
        self.fade_in_spin.setSuffix(" giây")
        self.fade_in_spin.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                min-height: 25px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #3498db;
            }
        """)
        
        self.fade_out_spin = QDoubleSpinBox()
        self.fade_out_spin.setRange(0, 10)
        self.fade_out_spin.setValue(1.0)
        self.fade_out_spin.setSuffix(" giây")
        self.fade_out_spin.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                min-height: 25px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #3498db;
            }
        """)
        
        audio_layout.addRow(self.normalize_check)
        audio_layout.addRow("Fade In:", self.fade_in_spin)
        audio_layout.addRow("Fade Out:", self.fade_out_spin)
        
        # ===== TÙY CHỌN XÁO TRỘN =====
        shuffle_group = QGroupBox("Xáo Trộn File Âm Thanh")
        shuffle_layout = QVBoxLayout(shuffle_group)
        
        self.shuffle_check = QCheckBox("Xáo trộn ngẫu nhiên file âm thanh")
        self.shuffle_check.setChecked(False)
        self.shuffle_check.toggled.connect(self.on_shuffle_toggled)
        self.shuffle_check.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border: 2px solid #e67e22;
                border-radius: 5px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #e67e22;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0iI2ZmZmZmZiI+PHBhdGggZD0iTTEyLjcgNS4zTDcgMTAuN0wzLjMgN2wtMS40IDEuNEw3IDEzLjVsNy4xLTcuMS0xLjQtMS40eiIvPjwvc3ZnPg==);
            }
            QCheckBox::indicator:hover {
                border: 2px solid #d35400;
                background-color: #fef5e7;
            }
        """)
        
        self.shuffle_info_label = QLabel("(Áp dụng khi có 3 file trở lên)")
        self.shuffle_info_label.setStyleSheet("color: #e67e22; font-size: 11px; font-style: italic; padding-left: 30px;")
        self.shuffle_info_label.setVisible(False)
        
        shuffle_layout.addWidget(self.shuffle_check)
        shuffle_layout.addWidget(self.shuffle_info_label)
        
        # ===== CÀI ĐẶT ĐẦU RA =====
        output_group = QGroupBox("Cài Đặt Đầu Ra")
        output_layout = QFormLayout(output_group)
        
        output_folder_layout = QHBoxLayout()
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setPlaceholderText("Chọn thư mục đầu ra...")
        self.output_folder_edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                min-height: 25px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        browse_folder_btn = QPushButton("📁 Duyệt...")
        browse_folder_btn.clicked.connect(self.browse_output_folder)
        browse_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        output_folder_layout.addWidget(self.output_folder_edit)
        output_folder_layout.addWidget(browse_folder_btn)
        
        output_filename_layout = QHBoxLayout()
        self.output_filename_edit = QLineEdit()
        self.output_filename_edit.setPlaceholderText("Tên file (ví dụ: video.mp4)")
        self.output_filename_edit.setText("avam_video.mp4")
        self.output_filename_edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                min-height: 25px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        default_name_btn = QPushButton("🔄 Tự động")
        default_name_btn.clicked.connect(self.set_auto_filename)
        default_name_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        output_filename_layout.addWidget(self.output_filename_edit)
        output_filename_layout.addWidget(default_name_btn)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([".mp4", ".avi", ".mkv", ".mov", ".wmv"])
        self.format_combo.setCurrentText(".mp4")
        self.format_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                min-height: 25px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
            }
        """)
        self.format_combo.currentTextChanged.connect(self.update_filename_extension)
        
        output_layout.addRow("Thư mục đầu ra:", output_folder_layout)
        output_layout.addRow("Tên file:", output_filename_layout)
        output_layout.addRow("Định dạng:", self.format_combo)
        
        # ===== GPU =====
        gpu_group = QGroupBox("Mã Hóa")
        gpu_layout = QFormLayout(gpu_group)
        
        self.gpu_check = QCheckBox("Bật mã hóa GPU (NVENC)")
        self.gpu_check.setChecked(True)
        self.gpu_check.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #9b59b6;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #9b59b6;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0iI2ZmZmZmZiI+PHBhdGggZD0iTTEyLjcgNS4zTDcgMTAuN0wzLjMgN2wtMS40IDEuNEw3IDEzLjVsNy4xLTcuMS0xLjQtMS40eiIvPjwvc3ZnPg==);
            }
            QCheckBox::indicator:hover {
                border: 2px solid #8e44ad;
                background-color: #f4ecf7;
            }
        """)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Ultra Fast", "Medium", "High", "Very High", "Ultra High"])
        self.quality_combo.setCurrentText("High")
        self.quality_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                min-height: 25px;
            }
            QComboBox:focus {
                border: 2px solid #9b59b6;
            }
        """)
        
        gpu_layout.addRow(self.gpu_check)
        gpu_layout.addRow("Chất lượng:", self.quality_combo)
        
        # Thêm tất cả nhóm vào layout
        settings_layout.addWidget(video_group)
        settings_layout.addWidget(audio_group)
        settings_layout.addWidget(shuffle_group)
        settings_layout.addWidget(output_group)
        settings_layout.addWidget(gpu_group)
        settings_layout.addStretch()
        
        scroll_area.setWidget(settings_widget)
        
        # ===== NÚT ĐIỀU KHIỂN =====
        button_group = QGroupBox("Thao Tác")
        button_layout = QHBoxLayout(button_group)
        
        apply_btn = QPushButton("✅ Áp Dụng")
        apply_btn.clicked.connect(self.apply_configuration)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        save_btn = QPushButton("💾 Lưu Cấu Hình")
        save_btn.clicked.connect(self.save_configuration)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        reset_btn = QPushButton("🔄 Đặt Lại")
        reset_btn.clicked.connect(self.reset_to_default)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        
        self.info_label = QLabel("⚙️ Cấu hình thiết lập đầu ra và bấm 'Áp Dụng'")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #3498db; font-size: 12px; font-weight: bold; padding: 5px;")
        
        layout.addWidget(title_label)
        layout.addWidget(scroll_area)
        layout.addWidget(button_group)
        layout.addWidget(self.info_label)
        
        # Style chung
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
                background-color: #f8f9fa;
            }
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
            QFormLayout > QLabel {
                font-weight: bold;
                color: #34495e;
            }
        """)
        
        # Kết nối tín hiệu
        self.mute_video_check.toggled.connect(self.on_video_audio_toggled)
        self.video_volume_spin.valueChanged.connect(self.on_config_changed)
        self.resolution_combo.currentTextChanged.connect(self.on_config_changed)
        self.fps_spin.valueChanged.connect(self.on_config_changed)
        self.audio_volume_spin.valueChanged.connect(self.on_config_changed)
        self.normalize_check.stateChanged.connect(self.on_config_changed)
        self.fade_in_spin.valueChanged.connect(self.on_config_changed)
        self.fade_out_spin.valueChanged.connect(self.on_config_changed)
        self.shuffle_check.toggled.connect(self.on_config_changed)
        self.gpu_check.stateChanged.connect(self.on_config_changed)
        self.quality_combo.currentTextChanged.connect(self.on_config_changed)
        self.output_folder_edit.textChanged.connect(self.on_config_changed)
        self.output_filename_edit.textChanged.connect(self.on_config_changed)
        self.format_combo.currentTextChanged.connect(self.on_config_changed)
    
    def on_video_audio_toggled(self, checked):
        """Xử lý khi toggle xóa âm thanh video"""
        self.video_volume_spin.setEnabled(not checked)
        self.on_config_changed()
    
    def on_shuffle_toggled(self, checked):
        """Xử lý khi toggle xáo trộn"""
        self.shuffle_info_label.setVisible(checked)
        self.on_config_changed()
    
    @Slot()
    def browse_output_folder(self):
        """Duyệt thư mục đầu ra"""
        # Mặc định là thư mục 'output' trong thư mục hiện tại
        default_dir = self.output_folder_edit.text() or os.path.join(os.getcwd(), 'output')
        
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Chọn Thư Mục Đầu Ra",
            default_dir
        )
        if folder_path:
            self.output_folder_edit.setText(folder_path)
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(folder_path, exist_ok=True)
    
    @Slot()
    def set_auto_filename(self):
        """Đặt tên file tự động với timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"avam_video_{timestamp}{self.format_combo.currentText()}"
        self.output_filename_edit.setText(filename)
    
    @Slot(str)
    def update_filename_extension(self, new_extension):
        """Cập nhật phần mở rộng của filename khi đổi định dạng"""
        current_filename = self.output_filename_edit.text()
        if current_filename:
            base_name = os.path.splitext(current_filename)[0]
            new_filename = f"{base_name}{new_extension}"
            self.output_filename_edit.setText(new_filename)
    
    @Slot()
    def apply_configuration(self):
        """Áp dụng cấu hình hiện tại"""
        config = self.get_config()
        self.config_changed.emit(config)
        self.info_label.setText("✅ Cấu hình đã được áp dụng cho lần ghép này!")
        self.info_label.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold; padding: 5px;")
    
    @Slot()
    def save_configuration(self):
        """Lưu cấu hình vào file"""
        config = self.get_config()
        self.save_panel_config(config)
        self.info_label.setText("✅ Cấu hình đã được lưu thành công!")
        self.info_label.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold; padding: 5px;")
    
    @Slot()
    def reset_to_default(self):
        """Đặt lại cấu hình mặc định"""
        # Tạo thư mục output mặc định
        default_output_dir = os.path.join(os.getcwd(), 'output')
        os.makedirs(default_output_dir, exist_ok=True)
        
        default_config = {
            'mute_video_audio': False,
            'video_volume': 1.0,
            'audio_volume': 1.0,
            'resolution': '1920x1080',
            'fps': 30,
            'normalize_audio': True,
            'fade_in_duration': 1.0,
            'fade_out_duration': 1.0,
            'shuffle_audio': False,
            'output_dir': default_output_dir,
            'output_filename': 'avam_video.mp4',
            'output_format': '.mp4',
            'use_gpu': True,
            'quality': 'high'
        }
        self.set_config(default_config)
        self.save_panel_config(default_config)
        self.info_label.setText("✅ Đã đặt lại cấu hình mặc định")
        self.info_label.setStyleSheet("color: #3498db; font-size: 12px; font-weight: bold; padding: 5px;")
    
    @Slot()
    def on_config_changed(self):
        """Xử lý thay đổi cấu hình"""
        self.info_label.setText("⚡ Cấu hình đã thay đổi - bấm 'Áp Dụng' để sử dụng")
        self.info_label.setStyleSheet("color: #e67e22; font-size: 12px; font-weight: bold; padding: 5px;")
    
    def save_panel_config(self, config):
        """Lưu cấu hình panel vào file"""
        current_dir = Path.cwd()
        config_file = current_dir / 'avam_panel_config.json'
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ Đã lưu cấu hình vào: {config_file}")
        except Exception as e:
            print(f"❌ Lỗi khi lưu cấu hình: {e}")
    
    def load_saved_config(self):
        """Tải cấu hình đã lưu"""
        try:
            current_dir = Path.cwd()
            config_file = current_dir / 'avam_panel_config.json'
            
            # Tạo thư mục output mặc định
            default_output_dir = os.path.join(os.getcwd(), 'output')
            os.makedirs(default_output_dir, exist_ok=True)
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Đảm bảo output_dir tồn tại
                if 'output_dir' in config and config['output_dir']:
                    os.makedirs(config['output_dir'], exist_ok=True)
                self.set_config(config)
                print(f"✅ Đã tải cấu hình từ: {config_file}")
            else:
                # Tạo cấu hình mặc định với thư mục output
                default_config = {
                    'mute_video_audio': False,
                    'video_volume': 1.0,
                    'audio_volume': 1.0,
                    'resolution': '1920x1080',
                    'fps': 30,
                    'normalize_audio': True,
                    'fade_in_duration': 1.0,
                    'fade_out_duration': 1.0,
                    'shuffle_audio': False,
                    'output_dir': default_output_dir,
                    'output_filename': 'avam_video.mp4',
                    'output_format': '.mp4',
                    'use_gpu': True,
                    'quality': 'high'
                }
                self.set_config(default_config)
                self.save_panel_config(default_config)
                
        except Exception as e:
            print(f"❌ Lỗi khi tải cấu hình: {e}")
            self.reset_to_default()
    
    def get_config(self) -> dict:
        """Lấy cấu hình hiện tại"""
        resolution_text = self.resolution_combo.currentText()
        resolution = resolution_text.split()[0]
        
        output_dir = self.output_folder_edit.text()
        if not output_dir:
            output_dir = os.path.join(os.getcwd(), 'output')
            self.output_folder_edit.setText(output_dir)
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(output_dir, exist_ok=True)
        
        output_filename = self.output_filename_edit.text()
        if not output_filename:
            output_filename = "avam_video.mp4"
            self.output_filename_edit.setText(output_filename)
        
        output_format = self.format_combo.currentText()
        
        if not output_filename.lower().endswith(output_format.lower()):
            output_filename = f"{os.path.splitext(output_filename)[0]}{output_format}"
            self.output_filename_edit.setText(output_filename)
        
        output_path = os.path.join(output_dir, output_filename)
        
        # Map quality
        quality_map = {
            "Ultra Fast": "ultra_fast",
            "Medium": "medium",
            "High": "high",
            "Very High": "very_high",
            "Ultra High": "ultra_high"
        }
        
        return {
            'mute_video_audio': self.mute_video_check.isChecked(),
            'video_volume': self.video_volume_spin.value(),
            'audio_volume': self.audio_volume_spin.value(),
            'resolution': resolution,
            'fps': self.fps_spin.value(),
            'normalize_audio': self.normalize_check.isChecked(),
            'fade_in_duration': self.fade_in_spin.value(),
            'fade_out_duration': self.fade_out_spin.value(),
            'shuffle_audio': self.shuffle_check.isChecked(),
            'output_dir': output_dir,
            'output_filename': output_filename,
            'output_format': output_format,
            'output_path': output_path,
            'use_gpu': self.gpu_check.isChecked(),
            'quality': quality_map.get(self.quality_combo.currentText(), 'high')
        }
    
    def set_config(self, config: dict):
        """Đặt cấu hình từ dict"""
        try:
            # Video settings
            self.mute_video_check.setChecked(config.get('mute_video_audio', False))
            self.video_volume_spin.setValue(config.get('video_volume', 1.0))
            
            # Resolution
            resolution = config.get('resolution', '1920x1080')
            for i in range(self.resolution_combo.count()):
                item = self.resolution_combo.itemText(i)
                if item.startswith(resolution):
                    self.resolution_combo.setCurrentIndex(i)
                    break
            
            self.fps_spin.setValue(config.get('fps', 30))
            
            # Audio settings
            self.audio_volume_spin.setValue(config.get('audio_volume', 1.0))
            self.normalize_check.setChecked(config.get('normalize_audio', True))
            self.fade_in_spin.setValue(config.get('fade_in_duration', 1.0))
            self.fade_out_spin.setValue(config.get('fade_out_duration', 1.0))
            
            # Shuffle
            self.shuffle_check.setChecked(config.get('shuffle_audio', False))
            
            # Output settings
            output_dir = config.get('output_dir', os.path.join(os.getcwd(), 'output'))
            os.makedirs(output_dir, exist_ok=True)
            self.output_folder_edit.setText(output_dir)
            
            output_filename = config.get('output_filename', 'avam_video.mp4')
            self.output_filename_edit.setText(output_filename)
            
            # Format
            output_format = config.get('output_format', '.mp4')
            for i in range(self.format_combo.count()):
                if self.format_combo.itemText(i) == output_format:
                    self.format_combo.setCurrentIndex(i)
                    break
            
            # GPU & Quality
            self.gpu_check.setChecked(config.get('use_gpu', True))
            
            quality = config.get('quality', 'high')
            quality_map = {
                'ultra_fast': "Ultra Fast",
                'medium': "Medium",
                'high': "High",
                'very_high': "Very High",
                'ultra_high': "Ultra High"
            }
            self.quality_combo.setCurrentText(quality_map.get(quality, "High"))
            
        except Exception as e:
            print(f"❌ Lỗi khi đặt cấu hình: {e}")