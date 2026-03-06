"""
Navigation bar component
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QComboBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

class Navbar(QWidget):
    """Navigation bar at the top of the main window"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Logo/Title
        title_label = QLabel("AVAM")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # Project selector
        project_combo = QComboBox()
        project_combo.addItem("Untitled Project")
        project_combo.setMinimumWidth(200)
        
        # Quick actions
        quick_save_btn = QPushButton("Quick Save")
        quick_export_btn = QPushButton("Quick Export")
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(QLabel("Project:"))
        layout.addWidget(project_combo)
        layout.addWidget(quick_save_btn)
        layout.addWidget(quick_export_btn)
        
        # Set style
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
            }
            QLabel {
                color: white;
            }
            QComboBox {
                background-color: white;
                color: black;
                border: 1px solid #34495e;
                border-radius: 3px;
                padding: 3px;
            }
            QPushButton {
                background-color: white;
                color: black;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
    
    def set_projects(self, projects: list):
        """Set project list"""
        # TODO: Implement project list update
        pass