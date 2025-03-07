import logging
from utils.logger import Logger
from PyQt6.QtWidgets import QApplication
import sys
from common.config_manager import get_global_config
from utils.version import version_info


def handle_exception(exc_type, exc_value, exc_traceback):
    """ Handle uncaught exceptions """
    if issubclass(exc_type, KeyboardInterrupt):
        # For KeyboardInterrupt, use default handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Set up logging
    logger = Logger.create_logger('app', 'lang_tools.log', logging.INFO)
    logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))


def main():
    # Get global configuration
    global_config = get_global_config()
    log_level = global_config.get('log.level', 'INFO')
    
    # Create application logger
    logger = Logger.create_logger('app', 'lang_tools.log', getattr(logging, log_level.upper()))
    
    # Log application startup information
    logger.info("=" * 50)
    logger.info(f"Lang Tools Startup - Version {version_info.version}")
    logger.info(f"Release Date: {version_info.release_date}")
    logger.info(f"Author: {version_info.author}")
    logger.info(f"License: {version_info.license}")
    logger.info("=" * 50)
    
    # Log dependency information
    logger.info("Dependencies:")
    logger.info(version_info.requirements)
    
    # Log changelog
    logger.info("Changelog:")
    logger.info(version_info.changelog)
    logger.info("=" * 50)

    # Initialize application
    logger.info("Initializing application...")
    app = QApplication(sys.argv)
    
    # Set up exception handler
    sys.excepthook = handle_exception
    logger.info("Exception handler configured")
    
    # Create main window
    from forms.main_window import MainWindow
    main_window = MainWindow()
    main_window.show()
    logger.info("Main window created and displayed")
    
    # Log application startup completion
    logger.info("Application initialization completed, starting main loop")
    
    # Run application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
