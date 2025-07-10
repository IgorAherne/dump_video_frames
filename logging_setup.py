# src/utils/logging_setup.py

import logging
import sys
from typing import Optional

# Custom Logging Formatter
class ShortLevelFormatter(logging.Formatter):
    """Formats log records to HH:MM:SS - L\t Message"""
    LEVEL_MAP = {
        logging.DEBUG:   'd',
        logging.INFO:    'i',
        logging.WARNING: 'W',
        logging.ERROR:   'E',
        logging.CRITICAL:'C'
    }
    DEFAULT_LEVEL_CHAR = '?'

    def format(self, record):
        # Create the short level character
        record.shortlevel = self.LEVEL_MAP.get(record.levelno, self.DEFAULT_LEVEL_CHAR)
        # Use the default Formatter logic for the actual formatting
        return super().format(record)

# Configuration Function
def configure_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """
    Configures the root logger with a custom format for console output
    and optionally adds a file handler.

    Args:
        level: The minimum logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a file where logs should also be written.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console Handler
    console_formatter = ShortLevelFormatter(
        fmt='%(asctime)s  %(shortlevel)s   %(message)s',
        datefmt='%H:%M:%S' # Only show HH:MM:SS
    )
    console_handler = logging.StreamHandler(sys.stdout) # Or sys.stderr
    console_handler.setFormatter(console_formatter)
    # Set level specifically for handler IF you want console to show less than root logger's level
    # console_handler.setLevel(logging.INFO) # Example: Root is DEBUG, console is INFO

    # Optional File Handler
    file_handler = None
    if log_file:
        try:
            # Use a more standard format for file logging
            file_formatter = logging.Formatter(
                fmt='%(asctime)s - %(levelname)-8s - %(name)-15s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setFormatter(file_formatter)
            # File handler usually logs everything >= root logger's level
            # file_handler.setLevel(logging.DEBUG) # Example
        except Exception as e:
            # Log an error about file handler creation using a temporary basic config
            logging.basicConfig()
            logging.error(f"Failed to create log file handler for {log_file}: {e}", exc_info=True)
            logging.basicConfig(handlers=[]) # Clean up temp config

    # Apply Handlers
    # Clear existing handlers from the root logger first
    if root_logger.hasHandlers():
        # Important: Use list() to avoid modifying the list while iterating
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
            handler.close() # Close the handler properly


    # Add the new console handler
    root_logger.addHandler(console_handler)
    print(f"Console logging configured at level: {logging.getLevelName(level)}", file=sys.stderr) # Add a confirmation print

    # Add the file handler if successfully created
    if file_handler:
        root_logger.addHandler(file_handler)
        print(f"File logging configured at level: {logging.getLevelName(level)} to file: {log_file}", file=sys.stderr)