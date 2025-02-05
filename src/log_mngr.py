import os
import logging
from typing import Union
from datetime import datetime

class LogManager:
    def __init__(self, log_file: str='app.log',
                 log_level:Union[int, str]=logging.NOTSET):
        self.logger = logging.getLogger('LogManager')
        if isinstance(log_level, str):
            self.logger.setLevel(self.convert_log_level(log_level))
        else:
            self.logger.setLevel(log_level)
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def convert_log_level(self, log_level) -> int:
        if log_level == 'CRITICAL':
            return logging.CRITICAL
        if log_level == 'FATAL':
            return logging.FATAL
        if log_level == 'ERROR':
            return logging.ERROR
        if log_level == 'WARNING':
            return logging.WARNING
        if log_level == 'WARN':
            return logging.WARN
        if log_level == 'INFO':
            return logging.INFO
        if log_level == 'DEBUG':
            return logging.DEBUG
        if log_level == 'NOTSET':
            return logging.NOTSET

    def get_logger(self):
        return self.logger

if __name__ == "__main__":
    log_manager = LogManager(log_file=f'log/app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                             log_level='DEBUG')
    logger = log_manager.get_logger()
    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')