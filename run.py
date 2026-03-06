"""
Entry point for AVAM application
"""
import sys
import os
from pathlib import Path
from PySide6.QtCore import Qt

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

def setup_environment():
    """Setup application environment"""
    # Create necessary directories
    directories = ['output', 'temp', 'logs', 'history']
    for directory in directories:
        dir_path = current_dir / directory
        dir_path.mkdir(exist_ok=True)
    
    # Set up FFmpeg path
    ffmpeg_dir = current_dir / 'ffmpeg' / 'bin'
    if ffmpeg_dir.exists():
        os.environ['PATH'] = str(ffmpeg_dir) + os.pathsep + os.environ['PATH']

def main():
    """Main entry point"""
    # Setup environment
    setup_environment()
    
    # Import after setup
    from src.utils.logger import setup_logger
    from src.utils.config_manager import ConfigManager
    from src.gui.loader_window import LoaderWindow
    
    # Setup logger
    logger = setup_logger()
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Import Qt after logger setup
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QCoreApplication
        
        # Set application attributes
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("AVAM")
        app.setOrganizationName("Livaan - Mao")
        
        # Create and show loader window - SỬA: truyền config_manager thay vì config
        loader = LoaderWindow(config_manager)
        loader.show()
        
        # Start application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        
        # Show error dialog if GUI is available
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Application Error",
                f"Failed to start AVAM:\n\n{str(e)}\n\n"
                "Please check the logs for more details."
            )
            sys.exit(1)
        except:
            print(f"Fatal error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()