'''
Script to set up logging with file name altering based on date and time.
'''

import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


def setup_logging() -> None:
    """
    Set up logging configuration.
    """
    
    log_dir = f'{os.environ['CARP_DIR']}/log'

    # Create a unique log file name based on the current date and time
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    # Set up the logging configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)-8s | %(asctime)s | %(message)s',
        handlers=[
            TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7),
            logging.StreamHandler()
        ]
    )