"""
Audio panel component
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QGroupBox, QScrollArea,
    QFrame, QSizePolicy, QFileDialog, QMessageBox
)
from pathlib import Path
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent, QIcon

from utils.file_utils import FileUtils
from src.core.audio.audio_loader import AudioLoader
from src.core.ffmpeg.ffmpeg_manager import FFmpegManager

class AudioPanel(QWidget):
    """Panel âm thanh để quản lý tệp âm thanh"""
    
    files_dropped = Signal(list)
    files_reordered = Signal(list)
    file_removed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.audio_files = []
        self.ffmpeg = FFmpegManager()
        self.audio_loader = AudioLoader(self.ffmpeg)
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo giao diện"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Tiêu đề
        title_label = QLabel("Tệp Âm Thanh")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50;")  # Xanh đậm-xám
        
        # Vùng thả
        self.drop_area = QGroupBox("Kéo & Thả Tệp Âm Thanh Vào Đây")
        self.drop_area.setAcceptDrops(True)
        drop_layout = QVBoxLayout(self.drop_area)
        self.drop_area.setFixedHeight(120)
        drop_label = QLabel("Thả tệp MP3, WAV, AAC vào đây\nhoặc nhấn 'Thêm Tệp'")
        drop_label.setAlignment(Qt.AlignCenter)
        drop_label.setStyleSheet("color: #5d6d7e; font-style: italic;")  # Xám trung bình
        
        # Nút thêm tệp
        add_files_btn = QPushButton("Thêm Tệp Âm Thanh")
        add_files_btn.clicked.connect(self.add_audio_files)
        
        drop_layout.addStretch()
        drop_layout.addWidget(drop_label)
        drop_layout.addWidget(add_files_btn)
        drop_layout.addStretch()
        
        # Danh sách tệp âm thanh
        files_group = QGroupBox("Danh Sách Tệp Âm Thanh")
        files_layout = QVBoxLayout(files_group)
        
        # List widget
        self.audio_list = QListWidget()
        self.audio_list.setDragDropMode(QListWidget.InternalMove)
        self.audio_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.audio_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # Nút điều khiển
        button_layout = QHBoxLayout()
        
        remove_btn = QPushButton("Xóa Đã Chọn")
        remove_btn.clicked.connect(self.remove_selected_files)
        
        clear_btn = QPushButton("Xóa Tất Cả")
        clear_btn.clicked.connect(self.clear_all_files)
        
        button_layout.addWidget(remove_btn)
        button_layout.addWidget(clear_btn)
        
        # Nhãn thông tin
        self.info_label = QLabel("Chưa có tệp âm thanh nào được thêm")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #5d6d7e; font-size: 12px;")  # Xám trung bình
        
        # Thêm widget vào layout
        files_layout.addWidget(self.audio_list)
        files_layout.addLayout(button_layout)
        
        layout.addWidget(title_label)
        layout.addWidget(self.drop_area)
        layout.addWidget(files_group)
        layout.addWidget(self.info_label)
        
        # Đặt style cho theme sáng
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
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-family: 'Segoe UI', 'Arial';
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
                color: #2c3e50;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1a5276;
                border: 1px solid #3498db;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-family: 'Segoe UI', 'Arial';
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5a7d;
                padding: 9px 15px 7px 17px;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        # Thêm style cho vùng thả
        self.drop_area.setStyleSheet("""
            QGroupBox#drop_area {
                border: 2px dashed #95a5a6;
                background-color: #f8f9fa;
                min-height: 100px;
            }
            QGroupBox#drop_area::title {
                color: #3498db;
                font-weight: bold;
            }
        """)
        self.drop_area.setObjectName("drop_area")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Xử lý sự kiện kéo vào"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Xử lý sự kiện thả"""
        urls = event.mimeData().urls()
        file_paths = []
        
        for url in urls:
            file_path = url.toLocalFile()
            if file_path:
                file_type = FileUtils.get_file_type(file_path)
                if file_type == 'audio':
                    file_paths.append(file_path)
        
        if file_paths:
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
        else:
            event.ignore()
    
    @Slot()
    def add_audio_files(self):
        """Thêm tệp âm thanh qua hộp thoại"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn Tệp Âm Thanh",
            "",
            "Tệp Âm Thanh (*.mp3 *.wav *.aac *.m4a *.flac *.ogg);;Tất Cả Tệp (*.*)"
        )
        
        if file_paths:
            self.files_dropped.emit(file_paths)
    
    @Slot()
    def remove_selected_files(self):
        """Xóa các tệp âm thanh đã chọn"""
        selected_items = self.audio_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            self.file_removed.emit(file_path)
            row = self.audio_list.row(item)
            self.audio_list.takeItem(row)
    
    @Slot()
    def clear_all_files(self):
        """Xóa tất cả tệp âm thanh"""
        if self.audio_list.count() == 0:
            return
        
        reply = QMessageBox.question(
            self,
            "Xóa Tất Cả Tệp",
            "Bạn có chắc chắn muốn xóa tất cả tệp âm thanh?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.audio_list.clear()
            self.audio_files = []
            self.update_info_label()
    
    @Slot(QListWidgetItem)
    def on_item_double_clicked(self, item):
        """Xử lý nhấp đúp vào mục"""
        file_path = item.data(Qt.UserRole)
        # TODO: Hiển thị hộp thoại thông tin tệp
    
    def set_audio_files(self, file_paths: list):
        """Đặt danh sách tệp âm thanh"""
        self.audio_list.clear()
        self.audio_files = []
        
        for file_path in file_paths:
            self.add_audio_file(file_path)
        
        self.update_info_label()
    
    def add_audio_file(self, file_path: str):
        """Thêm một tệp âm thanh vào danh sách"""
        # Xác thực tệp
        is_valid, error_msg = self.audio_loader.validate_audio_file(file_path)
        
        if not is_valid:
            QMessageBox.warning(self, "Tệp Âm Thanh Không Hợp Lệ", error_msg)
            return
        
        # Lấy thông tin tệp
        try:
            info = self.audio_loader.get_audio_info(file_path)
            
            # Tạo mục danh sách
            item = QListWidgetItem()
            item.setText(f"{Path(file_path).name} ({info['duration']:.2f}s)")
            item.setData(Qt.UserRole, file_path)
            item.setToolTip(f"Đường dẫn: {file_path}\nThời lượng: {info['duration']:.2f}s\n"
                          f"Định dạng: {info['format']}\nKích thước: {FileUtils.format_file_size(info['size'])}")
            
            self.audio_list.addItem(item)
            self.audio_files.append({
                'path': file_path,
                'info': info
            })
            
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải tệp âm thanh: {str(e)}")
    
    def update_info_label(self):
        """Cập nhật nhãn thông tin với tổng quan"""
        count = self.audio_list.count()
        
        if count == 0:
            self.info_label.setText("Chưa có tệp âm thanh nào được thêm")
            return
        
        # Tính tổng thời lượng
        total_duration = 0.0
        total_size = 0
        
        for audio_file in self.audio_files:
            total_duration += audio_file['info']['duration']
            total_size += audio_file['info']['size']
        
        # Định dạng thời lượng
        if total_duration < 60:
            duration_str = f"{total_duration:.1f} giây"
        elif total_duration < 3600:
            minutes = total_duration // 60
            seconds = total_duration % 60
            duration_str = f"{int(minutes)}ph {int(seconds)}giây"
        else:
            hours = total_duration // 3600
            minutes = (total_duration % 3600) // 60
            seconds = total_duration % 60
            duration_str = f"{int(hours)}giờ {int(minutes)}ph {int(seconds)}giây"
        
        self.info_label.setText(
            f"{count} tệp âm thanh | Tổng thời lượng: {duration_str} | "
            f"Tổng kích thước: {FileUtils.format_file_size(total_size)}"
        )
    
    def get_audio_files(self) -> list:
        """Lấy danh sách đường dẫn tệp âm thanh"""
        return [item.data(Qt.UserRole) for i in range(self.audio_list.count()) 
                for item in [self.audio_list.item(i)]]
    
    def get_audio_order(self) -> list:
        """Lấy thứ tự hiện tại của tệp âm thanh"""
        order = []
        for i in range(self.audio_list.count()):
            item = self.audio_list.item(i)
            file_path = item.data(Qt.UserRole)
            
            # Tìm chỉ mục trong danh sách gốc
            for idx, audio_file in enumerate(self.audio_files):
                if audio_file['path'] == file_path:
                    order.append(idx)
                    break
        
        return order