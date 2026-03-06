"""
Video panel component
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QGroupBox, QComboBox,
    QFrame, QSizePolicy, QFileDialog, QMessageBox,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from pathlib import Path
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent, QIcon

from utils.file_utils import FileUtils
from src.core.video.video_loader import VideoLoader
from src.core.ffmpeg.ffmpeg_manager import FFmpegManager
from src.models.project_config import VideoPosition, LoopStrategy

class VideoPanel(QWidget):
    """Panel video để quản lý các phân đoạn video"""
    
    files_dropped = Signal(list)
    segment_changed = Signal(dict)
    segment_removed = Signal(str)
    segments_reordered = Signal(list)
    
    def __init__(self):
        super().__init__()
        self.video_segments = []
        self.ffmpeg = FFmpegManager()
        self.video_loader = VideoLoader(self.ffmpeg)
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo giao diện"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Tiêu đề
        title_label = QLabel("Phân Đoạn Video")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50;")  # Xanh đậm-xám
        
        # Vùng thả
        self.drop_area = QGroupBox("Kéo & Thả Tệp Video Vào Đây")
        self.drop_area.setAcceptDrops(True)
        drop_layout = QVBoxLayout(self.drop_area)
        
        drop_label = QLabel("Thả tệp MP4, AVI, MKV, MOV vào đây\nhoặc nhấn 'Thêm Tệp'")
        drop_label.setAlignment(Qt.AlignCenter)
        drop_label.setStyleSheet("color: #5d6d7e; font-style: italic;")  # Xám trung bình
        
        # Nút thêm tệp
        add_files_btn = QPushButton("Thêm Tệp Video")
        add_files_btn.clicked.connect(self.add_video_files)
        
        drop_layout.addStretch()
        drop_layout.addWidget(drop_label)
        drop_layout.addWidget(add_files_btn)
        drop_layout.addStretch()
        
        # Bảng phân đoạn video
        segments_group = QGroupBox("Cấu Hình Phân Đoạn Video")
        segments_layout = QVBoxLayout(segments_group)
        
        # Tạo bảng
        self.segments_table = QTableWidget()
        self.segments_table.setColumnCount(5)
        self.segments_table.setHorizontalHeaderLabels([
            "#", "Tệp", "Vị Trí", "Hành Vi Lặp", "Thời Lượng"
        ])
        
        # Cấu hình bảng - Tăng chiều cao bảng
        self.segments_table.setMinimumHeight(250)  # Tăng chiều cao tối thiểu
        self.segments_table.setRowHeight(0, 40)  # Tăng chiều cao hàng
        self.segments_table.verticalHeader().setDefaultSectionSize(40)  # Tăng chiều cao mặc định cho hàng
        
        self.segments_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.segments_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.segments_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.segments_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.segments_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.segments_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.segments_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.segments_table.setAlternatingRowColors(True)
        self.segments_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        # Kết nối tín hiệu
        self.segments_table.cellChanged.connect(self.on_cell_changed)
        
        # Nút điều khiển
        button_layout = QHBoxLayout()
        
        move_up_btn = QPushButton("Di Chuyển Lên")
        move_up_btn.clicked.connect(self.move_segment_up)
        
        move_down_btn = QPushButton("Di Chuyển Xuống")
        move_down_btn.clicked.connect(self.move_segment_down)
        
        remove_btn = QPushButton("Xóa Đã Chọn")
        remove_btn.clicked.connect(self.remove_selected_segments)
        
        clear_btn = QPushButton("Xóa Tất Cả")
        clear_btn.clicked.connect(self.clear_all_segments)
        
        button_layout.addWidget(move_up_btn)
        button_layout.addWidget(move_down_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addWidget(clear_btn)
        
        # Thông tin chiến lược
        strategy_group = QGroupBox("Chiến Lược Lặp")
        strategy_layout = QVBoxLayout(strategy_group)
        strategy_layout.setContentsMargins(10, 15, 10, 10)
        
        self.strategy_label = QLabel("Thêm tệp video để xem chiến lược lặp")
        self.strategy_label.setWordWrap(True)
        self.strategy_label.setStyleSheet("""
            color: #2c3e50; 
            font-size: 12px; 
            padding: 8px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border: 1px solid #ecf0f1;
        """)
        
        strategy_layout.addWidget(self.strategy_label)
        
        # Nhãn thông tin
        self.info_label = QLabel("Chưa có tệp video nào được thêm")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #5d6d7e; font-size: 12px;")  # Xám trung bình
        
        # Thêm widget vào layout
        segments_layout.addWidget(self.segments_table)
        segments_layout.addLayout(button_layout)
        
        layout.addWidget(title_label)
        layout.addWidget(self.drop_area)
        layout.addWidget(segments_group)
        layout.addWidget(strategy_group)
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
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-family: 'Segoe UI', 'Arial';
                gridline-color: #ecf0f1;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1a5276;
                border: 1px solid #3498db;
                border-radius: 3px;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                padding: 12px 8px;
                border: 1px solid #d5dbdb;
                color: #2c3e50;
                font-weight: bold;
                font-family: 'Segoe UI', 'Arial';
            }
            QHeaderView::section:hover {
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
                if file_type == 'video':
                    file_paths.append(file_path)
        
        if file_paths:
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
        else:
            event.ignore()
    
    @Slot()
    def add_video_files(self):
        """Thêm tệp video qua hộp thoại"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn Tệp Video",
            "",
            "Tệp Video (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm);;Tất Cả Tệp (*.*)"
        )
        
        if file_paths:
            self.files_dropped.emit(file_paths)
    
    @Slot()
    def move_segment_up(self):
        """Di chuyển phân đoạn đã chọn lên"""
        current_row = self.segments_table.currentRow()
        if current_row <= 0:
            return
        
        # Hoán đổi hàng
        self.swap_rows(current_row, current_row - 1)
        self.segments_table.setCurrentCell(current_row - 1, 0)
        self.update_segment_orders()
    
    @Slot()
    def move_segment_down(self):
        """Di chuyển phân đoạn đã chọn xuống"""
        current_row = self.segments_table.currentRow()
        if current_row < 0 or current_row >= self.segments_table.rowCount() - 1:
            return
        
        # Hoán đổi hàng
        self.swap_rows(current_row, current_row + 1)
        self.segments_table.setCurrentCell(current_row + 1, 0)
        self.update_segment_orders()
    
    @Slot()
    def remove_selected_segments(self):
        """Xóa các phân đoạn video đã chọn"""
        selected_rows = sorted(set(item.row() for item in self.segments_table.selectedItems()), reverse=True)
        
        if not selected_rows:
            return
        
        for row in selected_rows:
            file_path = self.segments_table.item(row, 1).data(Qt.UserRole)
            self.segment_removed.emit(file_path)
            self.segments_table.removeRow(row)
        
        self.update_segment_orders()
        self.update_info_label()
        self.update_strategy_info()
    
    @Slot()
    def clear_all_segments(self):
        """Xóa tất cả phân đoạn video"""
        if self.segments_table.rowCount() == 0:
            return
        
        reply = QMessageBox.question(
            self,
            "Xóa Tất Cả Phân Đoạn",
            "Bạn có chắc chắn muốn xóa tất cả phân đoạn video?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.segments_table.setRowCount(0)
            self.video_segments = []
            self.update_info_label()
            self.update_strategy_info()
    
    @Slot(int, int)
    def on_cell_changed(self, row: int, column: int):
        """Xử lý thay đổi ô (cho comboboxes)"""
        if column == 2 or column == 3:  # Cột Vị trí hoặc Hành vi lặp
            segment_data = self.get_segment_data(row)
            if segment_data:
                self.segment_changed.emit(segment_data)
                self.update_strategy_info()
    
    def swap_rows(self, row1: int, row2: int):
        """Hoán đổi hai hàng trong bảng"""
        # Tắt tín hiệu để tránh cập nhật nhiều lần
        self.segments_table.blockSignals(True)
        
        # Hoán đổi tất cả ô
        for col in range(self.segments_table.columnCount()):
            item1 = self.segments_table.takeItem(row1, col)
            item2 = self.segments_table.takeItem(row2, col)
            
            self.segments_table.setItem(row2, col, item1)
            self.segments_table.setItem(row1, col, item2)
            
            # Cập nhật số thứ tự
            if col == 0:
                if item2:
                    item2.setText(str(row1 + 1))
                if item1:
                    item1.setText(str(row2 + 1))
        
        self.segments_table.blockSignals(False)
    
    def update_segment_orders(self):
        """Cập nhật số thứ tự cho tất cả phân đoạn"""
        self.segments_table.blockSignals(True)
        
        for row in range(self.segments_table.rowCount()):
            order_item = self.segments_table.item(row, 0)
            if order_item:
                order_item.setText(str(row + 1))
        
        self.segments_table.blockSignals(False)
        
        # Phát tín hiệu sắp xếp lại
        order = list(range(self.segments_table.rowCount()))
        self.segments_reordered.emit(order)
    
    def set_video_segments(self, segments_data: list):
        """Đặt phân đoạn video từ dữ liệu"""
        self.segments_table.setRowCount(0)
        self.video_segments = []
        
        for segment_data in segments_data:
            self.add_video_segment(segment_data)
        
        self.update_info_label()
        self.update_strategy_info()
    
    def add_video_segment(self, segment_data: dict):
        """Thêm phân đoạn video vào bảng"""
        file_path = segment_data.get('file_path')
        
        # Xác thực tệp
        is_valid, error_msg = self.video_loader.validate_video_file(file_path)
        
        if not is_valid:
            QMessageBox.warning(self, "Tệp Video Không Hợp Lệ", error_msg)
            return
        
        try:
            # Lấy thông tin video
            info = self.video_loader.get_video_info(file_path)
            
            # Thêm hàng
            row = self.segments_table.rowCount()
            self.segments_table.insertRow(row)
            
            # Số thứ tự
            order_item = QTableWidgetItem(str(row + 1))
            order_item.setTextAlignment(Qt.AlignCenter)
            self.segments_table.setItem(row, 0, order_item)
            
            # Tên tệp
            file_item = QTableWidgetItem(Path(file_path).name)
            file_item.setData(Qt.UserRole, file_path)
            file_item.setToolTip(f"Đường dẫn: {file_path}\n"
                               f"Độ phân giải: {info['width']}x{info['height']}\n"
                               f"Thời lượng: {info['duration']:.2f}s")
            self.segments_table.setItem(row, 1, file_item)
            
            # Combobox vị trí
            position_combo = QComboBox()
            position_combo.addItems(["Start", "Middle", "End"])
            
            position = segment_data.get('position', 'middle')
            if position == 'start':
                position_combo.setCurrentIndex(0)
            elif position == 'end':
                position_combo.setCurrentIndex(2)
            else:
                position_combo.setCurrentIndex(1)
            
            position_combo.currentTextChanged.connect(
                lambda text, r=row: self.on_position_changed(r, text.lower())
            )
            self.segments_table.setCellWidget(row, 2, position_combo)
            
            # Combobox hành vi lặp
            loop_combo = QComboBox()
            loop_combo.addItems(["Auto", "Loop", "No Loop"])
            
            loop_behavior = segment_data.get('loop_behavior', 'auto')
            if loop_behavior == 'loop':
                loop_combo.setCurrentIndex(1)
            elif loop_behavior == 'no_loop':
                loop_combo.setCurrentIndex(2)
            else:
                loop_combo.setCurrentIndex(0)
            
            loop_combo.currentTextChanged.connect(
                lambda text, r=row: self.on_loop_changed(r, text.lower().replace(' ', '_'))
            )
            self.segments_table.setCellWidget(row, 3, loop_combo)
            
            # Thời lượng
            duration_item = QTableWidgetItem(f"{info['duration']:.2f}s")
            duration_item.setTextAlignment(Qt.AlignCenter)
            self.segments_table.setItem(row, 4, duration_item)
            
            # Lưu dữ liệu phân đoạn
            self.video_segments.append({
                'file_path': file_path,
                'info': info,
                'position': position,
                'loop_behavior': loop_behavior,
                'order': row
            })
            
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải tệp video: {str(e)}")
    
    def on_position_changed(self, row: int, position: str):
        """Xử lý thay đổi vị trí"""
        segment_data = self.get_segment_data(row)
        if segment_data:
            segment_data['position'] = position
            self.segment_changed.emit(segment_data)
            self.update_strategy_info()
    
    def on_loop_changed(self, row: int, loop_behavior: str):
        """Xử lý thay đổi hành vi lặp"""
        segment_data = self.get_segment_data(row)
        if segment_data:
            segment_data['loop_behavior'] = loop_behavior
            self.segment_changed.emit(segment_data)
            self.update_strategy_info()
    
    def get_segment_data(self, row: int) -> dict:
        """Lấy dữ liệu phân đoạn cho hàng"""
        if row < 0 or row >= self.segments_table.rowCount():
            return None
        
        file_item = self.segments_table.item(row, 1)
        if not file_item:
            return None
        
        file_path = file_item.data(Qt.UserRole)
        
        position_combo = self.segments_table.cellWidget(row, 2)
        loop_combo = self.segments_table.cellWidget(row, 3)
        
        return {
            'file_path': file_path,
            'position': position_combo.currentText().lower(),
            'loop_behavior': loop_combo.currentText().lower().replace(' ', '_'),
            'order': row
        }
    
    def update_info_label(self):
        """Cập nhật nhãn thông tin với tổng quan"""
        count = self.segments_table.rowCount()
        
        if count == 0:
            self.info_label.setText("Chưa có tệp video nào được thêm")
            return
        
        # Tính tổng thời lượng
        total_duration = 0.0
        
        for segment in self.video_segments:
            total_duration += segment['info']['duration']
        
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
            f"{count} phân đoạn video | Tổng thời lượng: {duration_str}"
        )
    
    def update_strategy_info(self):
        """Cập nhật thông tin chiến lược lặp"""
        count = self.segments_table.rowCount()
        
        if count == 0:
            self.strategy_label.setText("Thêm tệp video để xem chiến lược lặp")
            return
        
        # Tạo mô tả chiến lược dựa trên số lượng video
        if count == 1:
            strategy = (
                "Chiến Lược Một Video:\n"
                "• Video sẽ lặp để khớp thời lượng âm thanh\n"
                "• Không cần cấu hình"
            )
        elif count == 2:
            strategy = (
                "Chiến Lược Hai Video:\n"
                "• Video 1: Có thể là intro (không lặp) hoặc lặp\n"
                "• Video 2: Sẽ lặp hoặc làm outro\n"
                "• Ít nhất một video phải lặp"
            )
        else:
            strategy = (
                "Chiến Lược Nhiều Video:\n"
                "• Video đầu: Có thể là intro (không lặp)\n"
                "• Video giữa: Luôn lặp\n"
                "• Video cuối: Có thể là outro (không lặp)\n"
                "• Linh hoạt hoàn toàn cho 3+ video"
            )
        
        # Thêm thông tin cụ thể của phân đoạn
        segment_info = []
        for row in range(count):
            segment_data = self.get_segment_data(row)
            if segment_data:
                file_name = Path(segment_data['file_path']).name
                position = segment_data['position'].title()
                loop = segment_data['loop_behavior'].replace('_', ' ').title()
                segment_info.append(f"{row + 1}. {file_name} - {position} ({loop})")
        
        if segment_info:
            strategy += "\n\nCấu hình hiện tại:\n" + "\n".join(segment_info)
        
        self.strategy_label.setText(strategy)
    
    def get_video_segments(self) -> list:
        """Lấy danh sách dữ liệu phân đoạn video"""
        segments = []
        
        for row in range(self.segments_table.rowCount()):
            segment_data = self.get_segment_data(row)
            if segment_data:
                segments.append(segment_data)
        
        return segments