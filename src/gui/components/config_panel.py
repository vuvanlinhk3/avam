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
from PySide6.QtGui import QFont, QIntValidator
import os
import json
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
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #95a5a6;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #7f8c8d;
            }
        """)
        
        # Container cho cài đặt
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        settings_layout.setSpacing(15)
        
        # Nhóm thiết lập chất lượng
        quality_group = QGroupBox("Chất Lượng Đầu Ra")
        quality_layout = QVBoxLayout(quality_group)
        
        # Nút chọn chất lượng
        self.quality_buttons = QButtonGroup()
        
        ultra_fast_btn = QRadioButton("Nhanh Nhất - Tốc độ ghép tối đa")
        medium_btn = QRadioButton("Trung bình - Mã hóa nhanh nhất")
        high_btn = QRadioButton("Cao - Cân bằng chất lượng/tốc độ")
        very_high_btn = QRadioButton("Rất cao - Khuyến nghị cho YouTube")
        ultra_high_btn = QRadioButton("Cực cao - Chất lượng lưu trữ")
        
        self.quality_buttons.addButton(ultra_fast_btn, 0)
        self.quality_buttons.addButton(medium_btn, 1)
        self.quality_buttons.addButton(high_btn, 2)
        self.quality_buttons.addButton(very_high_btn, 3)
        self.quality_buttons.addButton(ultra_high_btn, 4)
        
        ultra_fast_btn.setChecked(True)

        quality_layout.addWidget(ultra_fast_btn)
        quality_layout.addWidget(medium_btn)
        quality_layout.addWidget(high_btn)
        quality_layout.addWidget(very_high_btn)
        quality_layout.addWidget(ultra_high_btn)
        
        # Nhóm thiết lập video
        video_group = QGroupBox("Cài Đặt Video")
        video_layout = QFormLayout(video_group)
        
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
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)
        self.fps_spin.setSuffix(" FPS")
        
        self.gpu_check = QCheckBox("Bật mã hóa GPU (NVENC)")
        self.gpu_check.setChecked(True)
        
        video_layout.addRow("Độ phân giải:", self.resolution_combo)
        video_layout.addRow("Tốc độ khung hình:", self.fps_spin)
        video_layout.addRow(self.gpu_check)
        
        # Nhóm thiết lập âm thanh
        audio_group = QGroupBox("Cài Đặt Âm Thanh")
        audio_layout = QFormLayout(audio_group)
        
        self.normalize_check = QCheckBox("Chuẩn hóa âm lượng âm thanh")
        self.normalize_check.setChecked(True)
        
        self.fade_in_spin = QDoubleSpinBox()
        self.fade_in_spin.setRange(0, 10)
        self.fade_in_spin.setValue(1.0)
        self.fade_in_spin.setSuffix(" giây")
        
        self.fade_out_spin = QDoubleSpinBox()
        self.fade_out_spin.setRange(0, 10)
        self.fade_out_spin.setValue(1.0)
        self.fade_out_spin.setSuffix(" giây")
        
        audio_layout.addRow(self.normalize_check)
        audio_layout.addRow("Fade In:", self.fade_in_spin)
        audio_layout.addRow("Fade Out:", self.fade_out_spin)
        
        # Nhóm thiết lập đầu ra
        output_group = QGroupBox("Cài Đặt Đầu Ra")
        output_layout = QFormLayout(output_group)
        
        output_folder_layout = QHBoxLayout()
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setPlaceholderText("Chọn thư mục đầu ra...")
        browse_folder_btn = QPushButton("Duyệt...")
        browse_folder_btn.clicked.connect(self.browse_output_folder)
        output_folder_layout.addWidget(self.output_folder_edit)
        output_folder_layout.addWidget(browse_folder_btn)
        
        output_filename_layout = QHBoxLayout()
        self.output_filename_edit = QLineEdit()
        self.output_filename_edit.setPlaceholderText("Tên file (ví dụ: video.mp4)")
        self.output_filename_edit.setText("avam_video.mp4")
        default_name_btn = QPushButton("Tự động")
        default_name_btn.clicked.connect(self.set_auto_filename)
        output_filename_layout.addWidget(self.output_filename_edit)
        output_filename_layout.addWidget(default_name_btn)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([".mp4", ".avi", ".mkv", ".mov", ".wmv"])
        self.format_combo.currentTextChanged.connect(self.update_filename_extension)
        
        output_layout.addRow("Thư mục đầu ra:", output_folder_layout)
        output_layout.addRow("Tên file:", output_filename_layout)
        output_layout.addRow("Định dạng:", self.format_combo)
        
        settings_layout.addWidget(quality_group)
        settings_layout.addWidget(video_group)
        settings_layout.addWidget(audio_group)
        settings_layout.addWidget(output_group)
        settings_layout.addStretch()
        
        scroll_area.setWidget(settings_widget)
        
        button_group = QGroupBox("Thao Tác")
        button_layout = QHBoxLayout(button_group)
        
        apply_btn = QPushButton("Áp Dụng")
        apply_btn.clicked.connect(self.apply_configuration)
        
        save_btn = QPushButton("Lưu Cấu Hình")
        save_btn.clicked.connect(self.save_configuration)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        reset_btn = QPushButton("Đặt Lại")
        reset_btn.clicked.connect(self.reset_to_default)
        
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        
        self.info_label = QLabel("Cấu hình thiết lập đầu ra và bấm 'Áp Dụng'")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #5d6d7e; font-size: 12px;")
        
        layout.addWidget(title_label)
        layout.addWidget(scroll_area)
        layout.addWidget(button_group)
        layout.addWidget(self.info_label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-weight: bold;
            }
            QLabel {
                color: #2c3e50;
            }
            QRadioButton {
                padding: 6px 0;
                color: #2c3e50;
                font-family: 'Segoe UI', 'Arial';
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #95a5a6;
            }
            QRadioButton::indicator:checked {
                background-color: #3498db;
                border: 2px solid #2980b9;
            }
            QRadioButton::indicator:hover {
                border: 2px solid #7f8c8d;
            }
            QCheckBox {
                padding: 6px 0;
                color: #2c3e50;
                font-family: 'Segoe UI', 'Arial';
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #95a5a6;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 2px solid #2980b9;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0iI2ZmZmZmZiI+PHBhdGggZD0iTTEyLjcgNS4zTDcgMTAuN0wzLjMgN2wtMS40IDEuNEw3IDEzLjVsNy4xLTcuMS0xLjQtMS40eiIvPjwvc3ZnPg==);
            }
            QCheckBox::indicator:hover {
                border: 2px solid #7f8c8d;
            }
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                background-color: #ffffff;
                color: #2c3e50;
                font-family: 'Segoe UI', 'Arial';
                selection-background-color: #3498db;
                selection-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                padding: 7px;
            }
            QLineEdit:disabled {
                background-color: #ecf0f1;
                color: #7f8c8d;
            }
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                background-color: #ffffff;
                color: #2c3e50;
                font-family: 'Segoe UI', 'Arial';
                min-height: 20px;
            }
            QComboBox:hover {
                border: 1px solid #95a5a6;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
                padding: 7px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #2c3e50;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #bdc3c7;
                background-color: white;
                selection-background-color: #3498db;
                selection-color: white;
                font-family: 'Segoe UI', 'Arial';
            }
            QSpinBox, QDoubleSpinBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                background-color: #ffffff;
                color: #2c3e50;
                font-family: 'Segoe UI', 'Arial';
                min-height: 20px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #3498db;
                padding: 7px;
            }
            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 20px;
                border: none;
                background-color: #ecf0f1;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover,
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #d5dbdb;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-family: 'Segoe UI', 'Arial';
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5a7d;
                padding: 11px 19px 9px 21px;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QFormLayout > QLabel {
                color: #34495e;
                font-weight: 500;
            }
        """)
        
        # Kết nối tín hiệu
        self.quality_buttons.buttonClicked.connect(self.on_config_changed)
        self.resolution_combo.currentTextChanged.connect(self.on_config_changed)
        self.fps_spin.valueChanged.connect(self.on_config_changed)
        self.gpu_check.stateChanged.connect(self.on_config_changed)
        self.normalize_check.stateChanged.connect(self.on_config_changed)
        self.fade_in_spin.valueChanged.connect(self.on_config_changed)
        self.fade_out_spin.valueChanged.connect(self.on_config_changed)
        self.output_folder_edit.textChanged.connect(self.on_config_changed)
        self.output_filename_edit.textChanged.connect(self.on_config_changed)
        self.format_combo.currentTextChanged.connect(self.on_config_changed)
    
    @Slot()
    def browse_output_folder(self):
        """Duyệt thư mục đầu ra"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Chọn Thư Mục Đầu Ra",
            self.output_folder_edit.text() or "output",
            QFileDialog.ShowDirsOnly
        )
        
        if folder_path:
            self.output_folder_edit.setText(folder_path)
    
    @Slot()
    def set_auto_filename(self):
        """Đặt tên file tự động với timestamp"""
        from datetime import datetime
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
        """Áp dụng cấu hình hiện tại - CHỈ ÁP DỤNG, KHÔNG LƯU"""
        config = self.get_config()
        
        # KHÔNG lưu vào file khi bấm Áp Dụng
        # Chỉ phát tín hiệu để các phần khác của ứng dụng sử dụng NGAY LẬP TỨC
        self.config_changed.emit(config)
        
        self.info_label.setText("✓ Cấu hình đã được áp dụng cho lần ghép này!")
        self.info_label.setStyleSheet("color: #27ae60; font-size: 12px;")
    
    def save_panel_config(self, config):
        """Lưu cấu hình panel vào file trong thư mục hiện tại"""
        panel_config = {
            'output_dir': config.get('output_dir', 'output'),
            'output_filename': config.get('output_filename', 'avam_video.mp4'),
            'output_format': config.get('output_format', '.mp4'),
            'quality': config.get('quality', 'high'),
            'resolution': config.get('resolution', '1920x1080'),
            'fps': config.get('fps', 30),
            'use_gpu': config.get('use_gpu', True),
            'normalize_audio': config.get('normalize_audio', True),
            'fade_in_duration': config.get('fade_in_duration', 1.0),
            'fade_out_duration': config.get('fade_out_duration', 1.0)
        }
        
        # Luôn lưu vào thư mục hiện tại của ứng dụng
        current_dir = Path.cwd()
        config_file = current_dir / 'avam_panel_config.json'
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(panel_config, f, indent=2, ensure_ascii=False)
            print(f"✓ Đã lưu cấu hình panel vào: {config_file}")
            
        except Exception as e:
            print(f"Lỗi khi lưu cấu hình panel: {e}")

    @Slot()
    def save_configuration(self):
        """Lưu cấu hình vào config_manager và file"""
        if not self.config_manager:
            self.info_label.setText("⚠ Không thể lưu cấu hình: ConfigManager không tồn tại")
            self.info_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
            return
        
        config = self.get_config()
        
        # Lưu vào config_manager
        self.config_manager.update_config(
            default_output_dir=config.get('output_dir', 'output'),
            default_quality=config.get('quality', 'high'),
            default_resolution=config.get('resolution', '1920x1080'),
            default_fps=config.get('fps', 30),
            use_gpu=config.get('use_gpu', True),
            gpu_encoder=config.get('gpu_encoder', 'nvenc'),
            normalize_audio=config.get('normalize_audio', True),
            fade_in_duration=config.get('fade_in_duration', 1.0),
            fade_out_duration=config.get('fade_out_duration', 1.0)
        )
        
        # Cũng lưu vào file panel config để lần sau khởi động tự load
        self.save_panel_config(config)
        
        self.info_label.setText("✓ Cấu hình đã được lưu thành công! Lần sau khởi động sẽ tự động tải.")
        self.info_label.setStyleSheet("color: #27ae60; font-size: 12px;")
    
    @Slot()
    def reset_to_default(self):
        """Đặt lại cấu hình mặc định"""
        default_config = {
            'quality': 'high',
            'resolution': '1920x1080',
            'fps': 30,
            'output_dir': 'output',
            'output_filename': 'avam_video.mp4',
            'output_format': '.mp4',
            'use_gpu': True,
            'gpu_encoder': 'nvenc',
            'normalize_audio': True,
            'fade_in_duration': 1.0,
            'fade_out_duration': 1.0
        }
        self.set_config(default_config)
        
        # Cập nhật file config
        self.save_panel_config(default_config)
        
        self.info_label.setText("✓ Đã đặt lại cấu hình mặc định")
        self.info_label.setStyleSheet("color: #3498db; font-size: 12px;")
    
    @Slot()
    def on_config_changed(self):
        """Xử lý thay đổi cấu hình"""
        self.info_label.setText("Cấu hình đã thay đổi - bấm 'Áp Dụng' để lưu")
        self.info_label.setStyleSheet("color: #e67e22; font-size: 12px;")
    
    def load_saved_config(self):
        """Tải cấu hình đã lưu"""
        try:
            # Ưu tiên 1: Tải từ file config trong thư mục hiện tại
            current_dir = Path.cwd()
            config_file = current_dir / 'avam_panel_config.json'
            
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        panel_config = json.load(f)
                    
                    print(f"✓ Đã tải cấu hình từ: {config_file}")
                    
                    # Ưu tiên sử dụng cấu hình từ file panel
                    config = panel_config
                    
                except Exception as e:
                    print(f"Lỗi khi đọc cấu hình panel: {e}")
                    config = self.get_default_config()
            else:
                print("⚠ Không tìm thấy file cấu hình panel, sử dụng cấu hình mặc định")
                config = self.get_default_config()
            
            # Áp dụng cấu hình vào giao diện
            self.set_config(config)
            
            # Kiểm tra và tạo thư mục đầu ra nếu chưa tồn tại
            output_dir = config.get('output_dir', 'output')
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
        except Exception as e:
            print(f"Lỗi khi tải cấu hình: {e}")
            # Sử dụng cấu hình mặc định nếu có lỗi
            self.reset_to_default()
    
    def get_default_config(self):
        """Lấy cấu hình mặc định"""
        # Ưu tiên lấy từ config_manager nếu có
        if self.app_config:
            return {
                'quality': self.app_config.default_quality,
                'resolution': self.app_config.default_resolution,
                'fps': self.app_config.default_fps,
                'output_dir': self.app_config.default_output_dir,
                'use_gpu': self.app_config.use_gpu,
                'gpu_encoder': self.app_config.gpu_encoder,
                'normalize_audio': self.app_config.normalize_audio,
                'fade_in_duration': self.app_config.fade_in_duration,
                'fade_out_duration': self.app_config.fade_out_duration,
                'output_filename': 'avam_video.mp4',
                'output_format': '.mp4'
            }
        else:
            return {
                'quality': 'ultra_fast',
                'resolution': '1920x1080',
                'fps': 30,
                'output_dir': 'output',
                'output_filename': 'avam_video.mp4',
                'output_format': '.mp4',
                'use_gpu': True,
                'gpu_encoder': 'nvenc',
                'normalize_audio': True,
                'fade_in_duration': 1.0,
                'fade_out_duration': 1.0
            }
            
    def get_config(self) -> dict:
        """Lấy cấu hình hiện tại"""
        quality_map = {
            0: "ultra_fast",
            1: "medium",
            2: "high",
            3: "very_high",
            4: "ultra_high"
        }
        quality_id = self.quality_buttons.checkedId()
        quality = quality_map.get(quality_id, "ultra_fast")
        
        resolution_text = self.resolution_combo.currentText()
        resolution = resolution_text.split()[0]
        
        output_dir = self.output_folder_edit.text() or "output"
        output_filename = self.output_filename_edit.text()
        output_format = self.format_combo.currentText()
        
        if output_filename and output_dir:
            if not output_filename.lower().endswith(tuple([fmt.lower() for fmt in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']])):
                output_filename = f"{output_filename}{output_format}"
            output_path = os.path.join(output_dir, output_filename)
        else:
            output_path = ""
        
        return {
            'quality': quality,
            'resolution': resolution,
            'fps': self.fps_spin.value(),
            'output_dir': output_dir,
            'output_filename': output_filename,
            'output_format': output_format,
            'output_path': output_path,
            'use_gpu': self.gpu_check.isChecked(),
            'gpu_encoder': 'nvenc',
            'normalize_audio': self.normalize_check.isChecked(),
            'fade_in_duration': self.fade_in_spin.value(),
            'fade_out_duration': self.fade_out_spin.value()
        }
    
    def set_config(self, config: dict):
        """Đặt cấu hình từ dict"""
        try:
            # Đặt chất lượng
            quality_map = {
                'ultra_fast': 0,
                'medium': 1,
                'high': 2,
                'very_high': 3,
                'ultra_high': 4
            }
            quality_id = quality_map.get(config.get('quality', 'ultra_fast'), 0)
            if 0 <= quality_id <= 4:
                button = self.quality_buttons.button(quality_id)
                if button:
                    button.setChecked(True)
            
            # Đặt độ phân giải
            resolution = config.get('resolution', '1920x1080')
            resolution_text = f"{resolution} ("
            if resolution == "1920x1080":
                resolution_text += "Full HD)"
            elif resolution == "1280x720":
                resolution_text += "HD)"
            elif resolution == "3840x2160":
                resolution_text += "4K)"
            elif resolution == "2560x1440":
                resolution_text += "2K)"
            else:
                resolution_text += f"{resolution})"
            
            index = self.resolution_combo.findText(resolution_text, Qt.MatchStartsWith)
            if index >= 0:
                self.resolution_combo.setCurrentIndex(index)
            
            # Đặt các giá trị video/audio
            self.fps_spin.setValue(config.get('fps', 30))
            self.gpu_check.setChecked(config.get('use_gpu', True))
            self.normalize_check.setChecked(config.get('normalize_audio', True))
            self.fade_in_spin.setValue(config.get('fade_in_duration', 1.0))
            self.fade_out_spin.setValue(config.get('fade_out_duration', 1.0))
            
            # Đặt thông tin đầu ra - ĐẢM BẢO GIÁ TRỊ TỪ CONFIG ĐƯỢC HIỂN THỊ
            output_dir = config.get('output_dir', 'output')
            output_filename = config.get('output_filename', 'avam_video.mp4')
            output_format = config.get('output_format', '.mp4')
            
            # QUAN TRỌNG: Luôn đặt giá trị từ config vào giao diện
            self.output_folder_edit.setText(output_dir)
            self.output_filename_edit.setText(output_filename)
            
            # Đặt định dạng
            index = self.format_combo.findText(output_format)
            if index >= 0:
                self.format_combo.setCurrentIndex(index)
            
            # Đảm bảo thư mục tồn tại
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            self.info_label.setText("✓ Cấu hình đã được tải")
            self.info_label.setStyleSheet("color: #27ae60; font-size: 12px;")
            
        except Exception as e:
            print(f"Lỗi khi đặt cấu hình: {e}")
            self.info_label.setText("⚠ Lỗi khi tải cấu hình")
            self.info_label.setStyleSheet("color: #e74c3c; font-size: 12px;")