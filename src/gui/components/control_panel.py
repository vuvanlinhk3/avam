"""
Control panel component
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QIcon

class ControlPanel(QWidget):
    """Panel điều khiển để bắt đầu/dừng quá trình ghép"""
    
    start_clicked = Signal()
    stop_clicked = Signal()
    open_output_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.is_processing = False
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo giao diện"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)  # Giảm margin
        layout.setSpacing(12)  # Giảm spacing
        
        # ===== BÊN TRÁI: Tiến trình và Ước tính =====
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)  # Giảm spacing
        
        # Nhóm tiến trình
        progress_group = QGroupBox("Tiến Trình")
        progress_group.setMinimumHeight(90)  # Giới hạn chiều cao
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setContentsMargins(10, 12, 10, 10)  # Giảm padding
        
        # Thanh tiến trình
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(20)  # Thấp hơn
        
        # Nhãn tiến trình
        self.progress_label = QLabel("Sẵn sàng")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setMaximumHeight(18)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        # Nhóm ước tính
        estimate_group = QGroupBox("Ước Tính")
        estimate_group.setMinimumHeight(70)  # Giới hạn chiều cao
        estimate_layout = QVBoxLayout(estimate_group)
        estimate_layout.setContentsMargins(10, 12, 10, 10)  # Giảm padding
        
        self.estimate_label = QLabel("Thời gian ước tính: --")
        self.estimate_label.setAlignment(Qt.AlignCenter)
        self.estimate_label.setMaximumHeight(18)
        
        self.size_label = QLabel("Kích thước ước tính: --")
        self.size_label.setAlignment(Qt.AlignCenter)
        self.size_label.setMaximumHeight(18)
        
        estimate_layout.addWidget(self.estimate_label)
        estimate_layout.addWidget(self.size_label)
        
        left_layout.addWidget(progress_group)
        left_layout.addWidget(estimate_group)
        
        # ===== BÊN PHẢI: Nút Điều Khiển =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)  # Giảm spacing giữa các nút
        
        control_group = QGroupBox("Điều Khiển")
        control_group.setMinimumHeight(180)  # Tổng chiều cao thấp hơn
        control_layout = QVBoxLayout(control_group)
        control_layout.setContentsMargins(12, 15, 12, 12)  # Giảm padding
        control_layout.setSpacing(8)  # Khoảng cách nhỏ hơn giữa nút
        
        # Nút bắt đầu - Ngắn hơn, rộng hơn
        self.start_button = QPushButton("BẮT ĐẦU GHÉP")
        self.start_button.setMinimumHeight(36)  # Giảm chiều cao
        self.start_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.start_button.clicked.connect(self.on_start_clicked)
        
        # Nút dừng - Ngắn hơn, rộng hơn
        self.stop_button = QPushButton("DỪNG")
        self.stop_button.setMinimumHeight(36)  # Giảm chiều cao
        self.stop_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.on_stop_clicked)
        
        # Nút mở thư mục - Ngắn hơn, rộng hơn
        self.open_output_button = QPushButton("MỞ THƯ MỤC")
        self.open_output_button.setMinimumHeight(36)  # Giảm chiều cao
        self.open_output_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.open_output_button.clicked.connect(self.on_open_output_clicked)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.open_output_button)
        
        right_layout.addWidget(control_group)
        right_layout.addStretch()
        
        # ===== THÊM VÀO LAYOUT CHÍNH =====
        layout.addWidget(left_panel, 2)  # Giảm tỷ lệ
        layout.addWidget(right_panel, 1)  # Panel phải nhỏ hơn
        
        # Set style
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #3498db;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: #ffffff;
                text-align: center;
                font-size: 11px;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 3px;
            }
            QLabel {
                color: #2c3e50;
                font-size: 11px;
            }
            QPushButton {
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 6px;
            }
            #start_button {
                background-color: #27ae60;
                color: white;
            }
            #start_button:hover { background-color: #229954; }
            #start_button:disabled { background-color: #95a5a6; }
            #stop_button {
                background-color: #e74c3c;
                color: white;
            }
            #stop_button:hover { background-color: #c0392b; }
            #stop_button:disabled { background-color: #95a5a6; }
            #open_output_button {
                background-color: #3498db;
                color: white;
            }
            #open_output_button:hover { background-color: #2980b9; }
            #open_output_button:disabled { background-color: #95a5a6; }
        """)
        
        self.start_button.setObjectName("start_button")
        self.stop_button.setObjectName("stop_button")
        self.open_output_button.setObjectName("open_output_button")
    
    @Slot()
    def on_start_clicked(self):
        """Xử lý nhấp nút bắt đầu"""
        if not self.is_processing:
            self.start_clicked.emit()
    
    @Slot()
    def on_stop_clicked(self):
        """Xử lý nhấp nút dừng"""
        if self.is_processing:
            self.stop_clicked.emit()
    
    @Slot()
    def on_open_output_clicked(self):
        """Xử lý nhấp nút mở thư mục"""
        self.open_output_clicked.emit()
    
    def update_progress(self, percent: float):
        """Cập nhật thanh tiến trình"""
        self.progress_bar.setValue(int(percent))
        if percent >= 100:
            self.progress_label.setText("✓ Hoàn thành!")
            self.set_processing(False)
        elif percent > 0:
            self.progress_label.setText(f"Đang xử lý... {percent:.1f}%")
    
    def reset_progress(self):
        """Đặt lại thanh tiến trình"""
        self.progress_bar.setValue(0)
        self.progress_label.setText("Sẵn sàng")
    
    def set_processing(self, processing: bool):
        """Đặt trạng thái xử lý"""
        self.is_processing = processing
        self.start_button.setEnabled(not processing)
        self.stop_button.setEnabled(processing)
        if processing:
            self.start_button.setText("ĐANG XỬ LÝ...")
        else:
            self.start_button.setText("BẮT ĐẦU GHÉP")
    
    def set_start_enabled(self, enabled: bool):
        """Đặt trạng thái kích hoạt cho nút bắt đầu"""
        if not self.is_processing:
            self.start_button.setEnabled(enabled)
    
    def update_estimate(self, time_minutes: float, size_gb: float):
        """Cập nhật ước tính thời gian và kích thước"""
        if time_minutes < 1:
            time_str = "< 1 phút"
        elif time_minutes < 60:
            time_str = f"{time_minutes:.0f} phút"
        else:
            time_str = f"{time_minutes/60:.1f} giờ"
        
        if size_gb < 0.1:
            size_str = f"{size_gb*1024:.0f} MB"
        elif size_gb < 1:
            size_str = f"{size_gb*1024:.1f} MB"
        else:
            size_str = f"{size_gb:.1f} GB"
        
        self.estimate_label.setText(f"Thời gian: {time_str}")
        self.size_label.setText(f"Kích thước: {size_str}")
    
    def show_message(self, message: str):
        """Hiển thị thông báo trong nhãn tiến trình"""
        self.progress_label.setText(message)