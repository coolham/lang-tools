import logging
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

class Logger:
    """日志记录器工具类"""
    
    # Class variables to track state
    _file_handlers: Dict[str, logging.FileHandler] = {}  # Path -> Handler mapping
    _logger_configs: Dict[str, Tuple] = {}  # Logger name -> (filename, level, fixed) mapping
    _default_filename = "app.log"
    _default_level = logging.INFO
    _default_fixed_filename = False
    
    @classmethod
    def set_defaults(cls, filename: str, level: int, fixed_filename: bool = False):
        """设置默认日志参数"""
        cls._default_filename = filename
        cls._default_level = level
        cls._default_fixed_filename = fixed_filename
    
    @classmethod
    def create_logger(cls, name: str, filename: str = None, level: int = None, fixed_filename: Optional[bool] = None):
        """创建一个logger实例"""
        # Use defaults if not specified
        level = level if level is not None else cls._default_level
        filename = filename if filename is not None else cls._default_filename
        
        # Special handling for fixed_filename
        if fixed_filename is not None:
            cls._default_fixed_filename = fixed_filename
        fixed_filename = cls._default_fixed_filename
        
        # Get or create logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Check if this logger configuration has changed
        current_config = (filename, level, fixed_filename)
        stored_config = cls._logger_configs.get(name)
        
        # If logger exists with same config, just return it
        if stored_config == current_config and logger.handlers:
            return logger
            
        # Otherwise, reset the logger by removing all handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            if isinstance(handler, logging.FileHandler):
                handler.close()
                
        # Store the new configuration
        cls._logger_configs[name] = current_config
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Create full path for log file
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Determine actual filename based on fixed_filename setting
        if fixed_filename:
            actual_filename = filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name, ext = os.path.splitext(filename)
            actual_filename = f"{base_name}_{timestamp}{ext}"
        
        log_path = os.path.join(log_dir, actual_filename)
        
        # Manage file handler
        if fixed_filename and log_path in cls._file_handlers:
            # For fixed filenames, reuse existing handler
            file_handler = cls._file_handlers[log_path]
        else:
            # Create a new handler
            file_handler = logging.FileHandler(log_path, 'w' if fixed_filename else 'a', encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            
            # Store handler for reuse with fixed filenames
            if fixed_filename:
                cls._file_handlers[log_path] = file_handler
        
        # Add the file handler to this logger
        logger.addHandler(file_handler)
        
        return logger



