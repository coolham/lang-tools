import unittest
import logging
import os
import shutil
from utils.logger import Logger
from datetime import datetime

class TestLogger(unittest.TestCase):
    """Test the Logger class with emphasis on multi-module usage patterns"""

    @classmethod
    def setUpClass(cls):
        """Create logs directory if it doesn't exist"""
        cls.logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(cls.logs_dir, exist_ok=True)

    def setUp(self):
        """Reset Logger class state before each test"""
        # Clear the file handlers dictionary
        Logger._file_handlers = {}
        # Reset defaults
        Logger._default_filename = "application.log"
        Logger._default_level = logging.INFO
        Logger._default_fixed_filename = False
        
        # Remove existing log files
        self.clean_log_directory()

    def tearDown(self):
        """Clean up after each test"""
        # Clear loggers to avoid interference between tests
        for name in logging.root.manager.loggerDict.keys():
            logger = logging.getLogger(name)
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        
        # Verify we don't have multiple log files when fixed_filename is True
        self.check_log_file_count()
        
        # Clean log directory
        self.clean_log_directory()

    def clean_log_directory(self):
        """Remove all test log files"""
        if os.path.exists(self.logs_dir):
            for filename in os.listdir(self.logs_dir):
                if filename.startswith("test_"):
                    try:
                        os.remove(os.path.join(self.logs_dir, filename))
                    except PermissionError:
                        print(f"Warning: Could not delete {filename}, file still in use")

    def check_log_file_count(self):
        """Check that we don't have multiple log files for fixed_filename=True tests"""
        # Group files by their base name (without timestamp)
        file_groups = {}
        for filename in os.listdir(self.logs_dir):
            if filename.startswith("test_"):
                # Extract base name for comparison
                if "_20" in filename:  # Has a timestamp
                    base_name = filename.split("_20")[0]
                    if base_name not in file_groups:
                        file_groups[base_name] = []
                    file_groups[base_name].append(filename)
        
        # Check each group - if any test created multiple files with the same base name
        # when it shouldn't have, this will fail
        for base_name, files in file_groups.items():
            if len(files) > 1:
                # Only fail if this was supposed to be a fixed filename test
                test_marker = f"{base_name}.test_fixed"
                if os.path.exists(os.path.join(self.logs_dir, test_marker)):
                    self.fail(f"Multiple files found for base name {base_name}: {files}")

    def test_basic_logging(self):
        """Test basic logging functionality"""
        logger = Logger.create_logger('test_module', 'test_basic.log')
        logger.info('Test message')
        
        log_path = os.path.join(self.logs_dir, self._find_log_file('test_basic'))
        self.assertTrue(os.path.exists(log_path))
        
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn('Test message', content)

    def test_multiple_modules_same_file(self):
        """Test multiple modules logging to the same file"""
        # Set fixed filename to True
        Logger.set_defaults('test_shared.log', logging.INFO, True)
        
        # Create loggers for different modules
        logger1 = Logger.create_logger('module1')
        logger2 = Logger.create_logger('module2')
        logger3 = Logger.create_logger('module3')
        
        # Log messages from each module
        logger1.info('Message from module1')
        logger2.info('Message from module2')
        logger3.info('Message from module3')
        
        # Check that only one log file was created
        log_files = [f for f in os.listdir(self.logs_dir) if f == 'test_shared.log']
        self.assertEqual(len(log_files), 1, "Only one log file should be created")
        
        # Check that all messages are in the same file
        log_path = os.path.join(self.logs_dir, 'test_shared.log')
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn('Message from module1', content)
            self.assertIn('Message from module2', content)
            self.assertIn('Message from module3', content)

    def test_fixed_vs_timestamped_filenames(self):
        """Test fixed filenames vs timestamped filenames"""
        # Create a logger with fixed filename
        Logger.create_logger('fixed_module', 'test_fixed.log', fixed_filename=True)
        
        # Create a logger with timestamped filename
        Logger.create_logger('timestamp_module', 'test_timestamp.log', fixed_filename=False)
        
        # Check that the fixed filename exists exactly as specified
        fixed_path = os.path.join(self.logs_dir, 'test_fixed.log')
        self.assertTrue(os.path.exists(fixed_path))
        
        # Check that the timestamped filename exists with a timestamp
        timestamp_files = [f for f in os.listdir(self.logs_dir) if f.startswith('test_timestamp_')]
        self.assertEqual(len(timestamp_files), 1, "Timestamped file should be created")

    def test_defaults_application(self):
        """Test that defaults are properly applied"""
        # Set defaults
        Logger.set_defaults('test_defaults.log', logging.DEBUG, True)
        
        # Create loggers without specifying parameters
        logger1 = Logger.create_logger('default_module1')
        logger2 = Logger.create_logger('default_module2')
        
        # Check that they use the defaults
        logger1.debug('Debug message')  # This should appear if default level is DEBUG
        
        log_path = os.path.join(self.logs_dir, 'test_defaults.log')
        self.assertTrue(os.path.exists(log_path))
        
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn('Debug message', content)

    def test_mixed_parameters(self):
        """Test mixed parameters between defaults and explicit settings"""
        # Set defaults
        Logger.set_defaults('default.log', logging.INFO, True)
        
        # Create loggers with mixed parameters
        logger1 = Logger.create_logger('mixed1')  # Uses all defaults
        logger2 = Logger.create_logger('mixed2', 'custom.log')  # Custom filename, default level and fixed_filename
        logger3 = Logger.create_logger('mixed3', fixed_filename=False)  # Default filename but dynamic
        
        # Log messages
        logger1.info('Message to default log')
        logger2.info('Message to custom log')
        logger3.info('Message to timestamped log')
        
        # Check that the log files are created correctly
        self.assertTrue(os.path.exists(os.path.join(self.logs_dir, 'default.log')))
        self.assertTrue(os.path.exists(os.path.join(self.logs_dir, 'custom.log')))
        
        # Check that the dynamic log file is created with timestamp
        dynamic_files = [f for f in os.listdir(self.logs_dir) if f.startswith('default_') and f.endswith('.log')]
        self.assertEqual(len(dynamic_files), 1)

    def _find_log_file(self, prefix):
        """Helper to find a log file by prefix"""
        for filename in os.listdir(self.logs_dir):
            if filename.startswith(prefix):
                return filename
        return None

if __name__ == '__main__':
    unittest.main()
