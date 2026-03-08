"""
Main window for AVAM application
"""
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QMessageBox, QFileDialog, QMenu, QStatusBar
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QAction, QIcon, QCloseEvent, QPalette, QColor

from utils.config_manager import ConfigManager, AppConfig
from utils.logger import get_logger
from src.core.project.project_manager import ProjectManager
from src.core.pipeline.merge_pipeline import MergePipeline
from src.core.ffmpeg.ffmpeg_manager import FFmpegManager

from .components.navbar import Navbar
from .components.audio_panel import AudioPanel
from .components.video_panel import VideoPanel
from .components.config_panel import ConfigPanel
from .components.control_panel import ControlPanel
from .components.status_bar import StatusBar
from .components.settings_window import SettingsWindow

class MergeWorker(QThread):
    """Worker thread for video merging"""
    
    progress = Signal(float, str)
    finished = Signal(bool, str)
    log_message = Signal(str)
    
    def __init__(self, project_manager: ProjectManager, 
                 pipeline: MergePipeline):
        super().__init__()
        self.project_manager = project_manager
        self.pipeline = pipeline
        self.cancel_requested = False
    
    def run(self):
        """Run merge process"""
        try:
            project = self.project_manager.current_project
            
            # Validate project
            is_valid, errors = self.project_manager.validate_current_project()
            if not is_valid:
                error_msg = "\n".join(errors)
                self.log_message.emit(f"Project validation failed:\n{error_msg}")
                self.finished.emit(False, f"Validation failed: {error_msg}")
                return
            
            # Start merge
            def progress_callback(percent: float, message: str):
                self.progress.emit(percent, message)
                self.log_message.emit(message)
                return not self.cancel_requested
            
            output_path = self.pipeline.merge_project(
                project,
                progress_callback=progress_callback
            )
            
            if self.cancel_requested:
                self.finished.emit(False, "Merge cancelled by user")
            else:
                self.finished.emit(True, f"Merge completed: {output_path}")
                
        except Exception as e:
            self.log_message.emit(f"Merge error: {str(e)}")
            self.finished.emit(False, f"Merge failed: {str(e)}")
    
    def cancel(self):
        """Cancel merge process"""
        self.cancel_requested = True

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.config = config_manager.config
        self.logger = get_logger()
        self.project_manager = ProjectManager()
        self.ffmpeg_manager = FFmpegManager()
        self.merge_pipeline = MergePipeline(self.ffmpeg_manager)
        self.merge_worker = None
        # THÊM: Lưu cấu hình hiện tại để sử dụng ngay
        self.current_merge_config = {}

        self.setup_light_theme()
        self.init_ui()
        self.init_menu()
        self.init_connections()
        
        # Create new project
        self.project_manager.new_project("Untitled Project")
        self.update_ui_from_project()

    def center_window(self):
        """Center the window on the screen, slightly higher"""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_geometry = self.frameGeometry()

        # Tâm màn hình
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)

        # Lấy vị trí góc trên trái
        top_left = window_geometry.topLeft()

        # 🔼 Đẩy cửa sổ lên trên (ví dụ 60px)
        offset_y = 60
        self.move(top_left.x(), top_left.y() - offset_y)


    def setup_light_theme(self):
        """Setup light theme with better contrast"""
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
                color: #2c3e50;
            }
            
            QWidget {
                background-color: #ffffff;
                color: #2c3e50;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 11px;
            }
            
            QMenuBar {
                background-color: #ffffff;
                color: #2c3e50;
                border-bottom: 1px solid #e1e5eb;
                padding: 4px;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 10px;
                border-radius: 3px;
            }
            
            QMenuBar::item:selected {
                background-color: #3498db;
                color: white;
            }
            
            QMenu {
                background-color: white;
                border: 1px solid #e1e5eb;
                border-radius: 4px;
                padding: 4px;
            }
            
            QMenu::item {
                padding: 6px 30px 6px 20px;
                border-radius: 3px;
            }
            
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
            
            QSplitter::handle {
                background-color: #e1e5eb;
                margin: 1px;
            }
            
            QSplitter::handle:hover {
                background-color: #3498db;
            }
            
            QStatusBar {
                background-color: #2c3e50;
                color: white;
                font-size: 10px;
                padding: 3px;
            }
            
            QTabWidget::pane {
                border: 1px solid #e1e5eb;
                border-radius: 4px;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #f8f9fa;
                color: #2c3e50;
                padding: 6px 12px;
                margin-right: 2px;
                border: 1px solid #e1e5eb;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                color: #3498db;
                font-weight: bold;
                border-bottom: 2px solid #3498db;
            }
            
            QTabBar::tab:hover {
                background-color: #e8f4fc;
            }
            
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background-color: #2980b9;
            }
            
            QPushButton:pressed {
                background-color: #21618c;
            }
            
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #e1e5eb;
                border-radius: 3px;
                padding: 4px 8px;
                selection-background-color: #3498db;
                selection-color: white;
            }
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #3498db;
                outline: none;
            }
            
            QComboBox {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #e1e5eb;
                border-radius: 3px;
                padding: 4px 8px;
                min-height: 20px;
            }
            
            QComboBox:focus {
                border: 1px solid #3498db;
            }
            
            QComboBox::drop-down {
                border: none;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #2c3e50;
            }
            
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #f8f9fa;
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #bdc3c7;
                border-radius: 6px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #95a5a6;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e1e5eb;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
            
            QProgressBar {
                border: 1px solid #e1e5eb;
                border-radius: 3px;
                background-color: white;
                text-align: center;
                color: #2c3e50;
            }
            
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 2px;
            }
            
            QListWidget {
                background-color: white;
                border: 1px solid #e1e5eb;
                border-radius: 3px;
                outline: none;
            }
            
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f8f9fa;
                color: #2c3e50;
            }
            
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            
            QListWidget::item:hover {
                background-color: #e8f4fc;
            }
            
            QTreeWidget {
                background-color: white;
                border: 1px solid #e1e5eb;
                border-radius: 3px;
                outline: none;
            }
            
            QTreeWidget::item {
                padding: 4px;
                color: #2c3e50;
            }
            
            QTreeWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            
            QTreeWidget::item:hover {
                background-color: #e8f4fc;
            }
            
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                padding: 6px;
                border: 1px solid #e1e5eb;
                font-weight: bold;
            }
            
            QToolButton {
                background-color: transparent;
                border: 1px solid #e1e5eb;
                border-radius: 3px;
                padding: 4px;
            }
            
            QToolButton:hover {
                background-color: #e8f4fc;
                border-color: #3498db;
            }
            
            QCheckBox, QRadioButton {
                color: #2c3e50;
                spacing: 5px;
            }
            
            QCheckBox::indicator, QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 1px solid #2980b9;
            }
            
            QLabel {
                color: #2c3e50;
            }
            
            QLabel[important="true"] {
                font-weight: bold;
                color: #e74c3c;
            }
        """)
        
        # Set palette for better text contrast
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(245, 247, 250))
        palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(248, 249, 250))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(44, 62, 80))
        palette.setColor(QPalette.Text, QColor(44, 62, 80))
        palette.setColor(QPalette.Button, QColor(52, 152, 219))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        palette.setColor(QPalette.Link, QColor(41, 128, 185))
        palette.setColor(QPalette.Highlight, QColor(52, 152, 219))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        self.setPalette(palette)
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("AVAM - Auto Video Audio Merger")
        self.setWindowIcon(QIcon.fromTheme("video-merge"))
        # self.setGeometry(100, 100, 1400, 800)
        self.resize(1400, 800)
        self.center_window()
        # Create central widget
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # # Navbar
        # self.navbar = Navbar()
        # main_layout.addWidget(self.navbar)
        
        # Splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("mainSplitter")
        splitter.setHandleWidth(3)
        
        # Left panel (Audio)
        self.audio_panel = AudioPanel()
        splitter.addWidget(self.audio_panel)
        
        # Center panel (Video)
        self.video_panel = VideoPanel()
        splitter.addWidget(self.video_panel)
        
        # Right panel (Config) - SỬA: truyền config_manager thay vì config
        self.config_panel = ConfigPanel(self.config_manager)
        splitter.addWidget(self.config_panel)
        
        # Set splitter sizes
        splitter.setSizes([300, 500, 300])
        
        main_layout.addWidget(splitter)
        
        # Control panel
        self.control_panel = ControlPanel()
        main_layout.addWidget(self.control_panel)
        
        # Status bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)
        
        # Apply specific styling to panels
        self.apply_panel_styling()
    
    def apply_panel_styling(self):
        """Apply additional styling to panels for better contrast"""
        # Additional panel styling can be added here if needed
        pass
    
    def init_menu(self):
        """Initialize menu bar"""
        menubar = self.menuBar()
        menubar.setObjectName("mainMenuBar")
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.setObjectName("fileMenu")
        
        new_action = QAction("&New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save Project &As", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        import_audio_action = QAction("&Import Audio Files", self)
        import_audio_action.setShortcut("Ctrl+I")
        import_audio_action.triggered.connect(self.import_audio_files)
        file_menu.addAction(import_audio_action)
        
        import_video_action = QAction("Import &Video Files", self)
        import_video_action.setShortcut("Ctrl+Shift+V")
        import_video_action.triggered.connect(self.import_video_files)
        file_menu.addAction(import_video_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.setObjectName("editMenu")
        
        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        edit_menu.addAction(settings_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.setObjectName("toolsMenu")
        
        preview_action = QAction("&Generate Preview", self)
        preview_action.setShortcut("Ctrl+P")
        preview_action.triggered.connect(self.generate_preview)
        tools_menu.addAction(preview_action)
        
        validate_action = QAction("&Validate Project", self)
        validate_action.setShortcut("Ctrl+V")
        validate_action.triggered.connect(self.validate_project)
        tools_menu.addAction(validate_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.setObjectName("helpMenu")
        
        about_action = QAction("&About AVAM", self)
        about_action.setShortcut("F1")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def init_connections(self):
        """Initialize signal connections"""
        # Audio panel signals
        self.audio_panel.files_dropped.connect(self.on_audio_files_dropped)
        self.audio_panel.files_reordered.connect(self.on_audio_files_reordered)
        self.audio_panel.file_removed.connect(self.on_audio_file_removed)
        
        # Video panel signals
        self.video_panel.files_dropped.connect(self.on_video_files_dropped)
        self.video_panel.segment_changed.connect(self.on_video_segment_changed)
        self.video_panel.segment_removed.connect(self.on_video_segment_removed)
        self.video_panel.segments_reordered.connect(self.on_video_segments_reordered)
        
        # Config panel signals
        self.config_panel.config_changed.connect(self.on_config_changed)
        
        # Control panel signals
        self.control_panel.start_clicked.connect(self.start_merge)
        self.control_panel.stop_clicked.connect(self.stop_merge)
        self.control_panel.open_output_clicked.connect(self.open_output_folder)
    
    def update_ui_from_project(self):
        """Update UI from current project"""
        if not self.project_manager.current_project:
            return
        
        project = self.project_manager.current_project
        
        # Update audio panel
        self.audio_panel.set_audio_files(project.audio_config.audio_files)
        
        # Update video panel
        video_segments = []
        for segment in project.video_config.video_segments:
            video_segments.append({
                'file_path': segment.file_path,
                'position': segment.position.value,
                'loop_behavior': segment.loop_behavior.value,
                'order': segment.order
            })
        self.video_panel.set_video_segments(video_segments)
        
        # QUAN TRỌNG: KHÔNG cập nhật ConfigPanel từ project ở đây
        # Vì ConfigPanel đang được người dùng chỉnh sửa trực tiếp
        # Chỉ cập nhật các panel khác, ConfigPanel giữ nguyên
        
        # Update window title
        self.setWindowTitle(f"AVAM - {project.name}")
        
        # Update status
        self.status_bar.show_message(f"Project: {project.name}")
    
    @Slot(list)
    def on_audio_files_dropped(self, file_paths: List[str]):
        """Handle audio files dropped"""
        added_files = self.project_manager.add_audio_files(file_paths)
        if added_files:
            self.update_ui_from_project()
            self.status_bar.show_message(f"Added {len(added_files)} audio files")
    
    @Slot(list)
    def on_audio_files_reordered(self, file_paths: List[str]):
        """Handle audio files reordered"""
        # TODO: Implement reordering in project manager
        pass
    
    @Slot(str)
    def on_audio_file_removed(self, file_path: str):
        """Handle audio file removed"""
        if self.project_manager.remove_audio_file(file_path):
            self.update_ui_from_project()
            self.status_bar.show_message(f"Removed audio file: {file_path}")
    
    @Slot(list)
    def on_video_files_dropped(self, file_paths: List[str]):
        """Handle video files dropped"""
        segments_data = []
        for file_path in file_paths:
            segments_data.append({
                'file_path': file_path,
                'position': 'middle',
                'loop_behavior': 'auto'
            })
        
        added_files = self.project_manager.add_video_segments(segments_data)
        if added_files:
            self.update_ui_from_project()
            self.status_bar.show_message(f"Added {len(added_files)} video files")
    
    @Slot(dict)
    def on_video_segment_changed(self, segment_data: Dict[str, Any]):
        """Handle video segment changed"""
        # TODO: Implement segment update in project manager
        pass
    
    @Slot(str)
    def on_video_segment_removed(self, file_path: str):
        """Handle video segment removed"""
        if self.project_manager.remove_video_segment(file_path):
            self.update_ui_from_project()
            self.status_bar.show_message(f"Removed video segment: {file_path}")
    
    @Slot(list)
    def on_video_segments_reordered(self, new_order: List[int]):
        """Handle video segments reordered"""
        if self.project_manager.reorder_video_segments(new_order):
            self.update_ui_from_project()
            self.status_bar.show_message("Reordered video segments")
    
    @Slot(dict)
    def on_config_changed(self, config: Dict[str, Any]):
        """Xử lý thay đổi cấu hình từ ConfigPanel - ĐÃ SỬA"""
        # QUAN TRỌNG: KHÔNG cập nhật project manager ở đây
        # Chỉ lưu cấu hình để sử dụng ngay cho lần ghép này
        self.current_merge_config = config
        
        self.status_bar.show_message("Cấu hình đã được áp dụng cho lần ghép này")
    
    def new_project(self):
        """Create new project"""
        if self.check_unsaved_changes():
            self.project_manager.new_project("Untitled Project")
            self.update_ui_from_project()
            self.status_bar.show_message("Created new project")
    
    def open_project(self):
        """Open project file"""
        if self.check_unsaved_changes():
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Project",
                "",
                "AVAM Projects (*.avam.json);;All Files (*.*)"
            )
            
            if file_path:
                try:
                    self.project_manager.load_project(file_path)
                    self.update_ui_from_project()
                    self.status_bar.show_message(f"Opened project: {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to open project: {str(e)}")
    
    def save_project(self):
        """Save current project"""
        try:
            saved_path = self.project_manager.save_project()
            self.status_bar.show_message(f"Project saved: {saved_path}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project: {str(e)}")
            return False
    
    def save_project_as(self):
        """Save project as new file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            "",
            "AVAM Projects (*.avam.json);;All Files (*.*)"
        )
        
        if file_path:
            if not file_path.endswith('.avam.json'):
                file_path += '.avam.json'
            
            try:
                saved_path = self.project_manager.save_project(file_path)
                self.update_ui_from_project()
                self.status_bar.show_message(f"Project saved as: {saved_path}")
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save project: {str(e)}")
                return False
        
        return False
    
    def check_unsaved_changes(self) -> bool:
        """
        Check for unsaved changes
        
        Returns:
            True if can proceed, False if cancelled
        """
        # TODO: Implement actual unsaved changes check
        return True
    
    def import_audio_files(self):
        """Import audio files"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Audio Files",
            "",
            "Audio Files (*.mp3 *.wav *.aac *.m4a *.flac *.ogg);;All Files (*.*)"
        )
        
        if file_paths:
            self.on_audio_files_dropped(file_paths)
    
    def import_video_files(self):
        """Import video files"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Video Files",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm);;All Files (*.*)"
        )
        
        if file_paths:
            self.on_video_files_dropped(file_paths)
    
    def open_settings(self):
        """Open settings window"""
        # SỬA: truyền config_manager thay vì config
        settings_window = SettingsWindow(self.config_manager, self)
        settings_window.exec_()
    
    def generate_preview(self):
        """Generate preview video"""
        # TODO: Implement preview generation
        QMessageBox.information(self, "Preview", "Preview generation not implemented yet")
    
    def validate_project(self):
        """Validate current project"""
        is_valid, errors = self.project_manager.validate_current_project()
        
        if is_valid:
            QMessageBox.information(self, "Validation", "Project is valid!")
        else:
            error_msg = "\n".join(errors)
            QMessageBox.warning(self, "Validation Failed", f"Project validation failed:\n{error_msg}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <div style='font-family: Arial, sans-serif;'>
        <h2 style='color: #2c3e50; margin-bottom: 10px;'>AVAM - Auto Video Audio Merger</h2>
        <p style='color: #2c3e50; font-size: 12px;'><strong>Version 1.0.1</strong></p>
        <p style='color: #2c3e50;'>A tool for creating long videos by intelligently looping videos according to audio.</p>
        <p style='color: #2c3e50;'>Optimized for GPU, no rendering, ultra-fast export.</p>
        <hr style='border: none; border-top: 1px solid #e1e5eb; margin: 15px 0;'>
        <p style='color: #7f8c8d; font-size: 10px;'>© 2025 Livaan - Mao</p>
        </div>
        """
        QMessageBox.about(self, "About AVAM", about_text)
    # Trong method start_merge của MainWindow, thêm phần kiểm tra và tạo thư mục output:

    @Slot()
    def start_merge(self):
        """Start merge process với cấu hình hiện tại từ ConfigPanel"""
        # ⛔ CHẶN thread cũ nếu còn sống
        if self.merge_worker is not None and self.merge_worker.isRunning():
            QMessageBox.warning(self, "Warning", "Merge is already in progress")
            return

        # Validate project
        is_valid, errors = self.project_manager.validate_current_project()
        if not is_valid:
            QMessageBox.critical(
                self,
                "Validation Failed",
                "Cannot start merge:\n" + "\n".join(errors)
            )
            return

        # Lấy cấu hình hiện tại từ ConfigPanel
        current_config = self.config_panel.get_config()
        project = self.project_manager.current_project

        # Lấy audio files theo thứ tự hiện tại từ UI
        audio_files = self.audio_panel.get_audio_files()
        
        # Kiểm tra tất cả audio files có tồn tại không
        missing_files = [f for f in audio_files if not Path(f).exists()]
        if missing_files:
            QMessageBox.critical(
                self,
                "Missing Audio Files",
                f"Các file âm thanh sau không tồn tại:\n" + "\n".join(missing_files)
            )
            return

        # Cập nhật project với audio files từ UI
        project.audio_config.audio_files = audio_files

        # Cập nhật audio config từ panel
        project.audio_config.fade_in_duration = current_config.get('fade_in_duration', 0.0)
        project.audio_config.fade_out_duration = current_config.get('fade_out_duration', 0.0)
        project.audio_config.normalize_volume = current_config.get('normalize_audio', True)
        project.audio_config.volume = current_config.get('audio_volume', 1.0)
        project.audio_config.shuffle_audio = current_config.get('shuffle_audio', False)

        # Cập nhật video config từ panel
        project.video_config.mute_all_video_audio = current_config.get('mute_video_audio', False)
        project.video_config.global_video_volume = current_config.get('video_volume', 1.0)

        # Cập nhật output config
        self.apply_config_to_project(current_config)
        
        # Đảm bảo thư mục output tồn tại
        output_dir = Path(project.output_config.output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Disable UI
        self.set_ui_enabled(False)

        # TẠO WORKER MỚI
        self.merge_worker = MergeWorker(
            self.project_manager,
            self.merge_pipeline
        )

        self.merge_worker.progress.connect(self.on_merge_progress)
        self.merge_worker.log_message.connect(self.on_merge_log)
        self.merge_worker.finished.connect(self.on_merge_finished)
        self.merge_worker.finished.connect(self.merge_worker.deleteLater)

        self.merge_worker.start()
        self.status_bar.show_message("Merging...")

    def apply_config_to_project(self, config: dict):
        """Áp dụng cấu hình từ ConfigPanel vào project"""
        if not config or not self.project_manager.current_project:
            return
        
        # Tạo bản sao của cấu hình hiện tại
        config = config.copy()
        
        # Thêm các trường cần thiết nếu thiếu
        if 'output_path' not in config:
            output_dir = config.get('output_dir', 'output')
            output_filename = config.get('output_filename', 'avam_video.mp4')
            output_format = config.get('output_format', '.mp4')
            
            if not output_filename.endswith(output_format):
                output_filename = f"{output_filename}{output_format}"
            
            config['output_path'] = os.path.join(output_dir, output_filename)
        
        # Cập nhật project với cấu hình hiện tại
        self.project_manager.set_output_config(config)
    
    @Slot(float, str)
    def on_merge_progress(self, percent: float, message: str):
        """Handle merge progress"""
        self.control_panel.update_progress(percent)
        self.status_bar.show_message(message)
    
    @Slot(bool, str)
    def on_merge_finished(self, success: bool, message: str):
        """Handle merge completion"""
        self.set_ui_enabled(True)
        self.control_panel.reset_progress()
        self.merge_worker = None
        if success:
            self.status_bar.show_message("Merge completed successfully", 5000)
            QMessageBox.information(self, "Success", message)
        else:
            self.status_bar.show_message("Merge failed", 5000)
            QMessageBox.critical(self, "Error", message)
    
    @Slot(str)
    def on_merge_log(self, message: str):
        """Handle merge log messages"""
        # Could be shown in a log window or status bar
        pass
    
    @Slot()
    def stop_merge(self):
        """Stop merge process"""
        if self.merge_worker and self.merge_worker.isRunning():
            self.merge_worker.cancel()
            self.status_bar.show_message("Stopping merge...")
    
    @Slot()
    def open_output_folder(self):
        """Open output folder"""
        if self.project_manager.current_project:
            output_path = self.project_manager.current_project.output_config.output_path
            if output_path:
                output_dir = Path(output_path).parent
                if output_dir.exists():
                    import subprocess
                    import sys
                    import os
                    
                    if sys.platform == 'win32':
                        os.startfile(output_dir)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', str(output_dir)])
                    else:
                        subprocess.run(['xdg-open', str(output_dir)])
    
    def set_ui_enabled(self, enabled: bool):
        """Enable or disable UI elements"""
        self.audio_panel.setEnabled(enabled)
        self.video_panel.setEnabled(enabled)
        self.config_panel.setEnabled(enabled)
        self.control_panel.set_start_enabled(enabled)
        # self.navbar.setEnabled(enabled)
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        if self.merge_worker and self.merge_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Merge in Progress",
                "A merge is currently in progress. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        if self.check_unsaved_changes():
            event.accept()
        else:
            event.ignore()