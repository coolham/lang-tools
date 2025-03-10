import logging
from utils.logger import Logger
from PyQt6.QtWidgets import QApplication
import sys
from utils.version import version_info
from utils.config_manager import ConfigManager


def handle_exception(exc_type, exc_value, exc_traceback):
    """ Handle uncaught exceptions """
    if issubclass(exc_type, KeyboardInterrupt):
        # For KeyboardInterrupt, use default handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Use the default parameters set by set_defaults
    logger = Logger.create_logger('app')
    logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))


def main():
    # 使用ConfigManager加载全局配置
    config_manager = ConfigManager()
    global_config = config_manager.get_config()
    log_level = global_config.get('logging.level', 'INFO')
    fixed_filename = global_config.get('logging.fixed_filename', False)

    # Set default logger parameters FIRST
    Logger.set_defaults('lang_tools.log', getattr(logging, log_level.upper()), fixed_filename)

    # Then create loggers
    logger = Logger.create_logger('app', 'lang_tools.log', getattr(logging, log_level.upper()), fixed_filename=True)
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
