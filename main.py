import logging
from utils.logger import Logger
from PyQt6.QtWidgets import QApplication
import sys
from utils.logger import Logger
from common.config_manager import get_global_config

def handle_exception(exc_type, exc_value, exc_traceback):
    """ 处理未捕获的异常 """
    if issubclass(exc_type, KeyboardInterrupt):
        # 对于 KeyboardInterrupt，直接调用默认处理
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Set up logging
    logger = Logger.create_logger('app', 'lang_tools.log', logging.INFO)
    logger.error("未处理异常", exc_info=(exc_type, exc_value, exc_traceback))
        



def main():
    global_config = get_global_config()
    log_level = global_config.get('log.level', 'INFO')


    # Initialize the application
    app = QApplication(sys.argv)

    sys.excepthook = handle_exception
    
    from forms.main_window import MainWindow
    # Create the main window
    main_window = MainWindow()
    main_window.show()

    # Set up logging
    logger = Logger.create_logger('app', 'lang_tools.log', logging.DEBUG)
    logger.info('Application started')

    # Execute the application
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
