import logging
import os
from datetime import datetime

class Logger:
    def __init__(self, name: str, log_file: str = 'app.log', level: int = logging.INFO):
        self.log_dir = 'logs'
        # Ensure the directory for the log file exists
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Append date and time to the log file name
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"{os.path.splitext(log_file)[0]}_{current_time}{os.path.splitext(log_file)[1]}"

        # Update log_file path to include log_dir
        log_file = os.path.join(self.log_dir, log_file)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create handlers
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(log_file)
        c_handler.setLevel(level)
        f_handler.setLevel(level)

        # Create formatters and add it to handlers
        c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        # Add handlers to the logger
        self.logger.addHandler(c_handler)
        self.logger.addHandler(f_handler)

    def get_logger(self):
        return self.logger

    @staticmethod
    def create_logger(name: str, log_file: str = 'app.log', level: int = logging.INFO):
        return Logger(name=name, log_file=log_file, level=level).get_logger()



