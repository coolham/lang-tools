import unittest
import logging
from utils.logger import Logger
import os

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.log_file = 'test.log'
        self.logger_name = 'testLogger'
        self.logger = Logger.create_logger(self.logger_name, self.log_file, logging.DEBUG)

    def tearDown(self):
        # Remove all handlers associated with the logger
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def test_log_to_file_and_console(self):
        # Test logging to file and console
        self.logger.debug('This is a debug message')
        self.logger.info('This is an info message')
        self.logger.warning('This is a warning message')
        self.logger.error('This is an error message')
        self.logger.critical('This is a critical message')

        # Check if log file is created and contains the messages
        with open(self.log_file, 'r') as f:
            log_content = f.read()
            self.assertIn('This is a debug message', log_content)
            self.assertIn('This is an info message', log_content)
            self.assertIn('This is a warning message', log_content)
            self.assertIn('This is an error message', log_content)
            self.assertIn('This is a critical message', log_content)
        # Ensure file is closed after reading
        f.close()

    def test_log_level(self):
        # Test if the log level is set correctly
        self.assertEqual(self.logger.level, logging.DEBUG)

if __name__ == '__main__':
    unittest.main()
