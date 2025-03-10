"""Logging utilities for py_dem_bones.

This module provides a simple interface to configure logging for both Python and C++ components.
"""

import logging
from typing import Optional, Union

# Import the C++ logger
from ._py_dem_bones import Logger, LogLevel

# Configure the default Python logger
logger = logging.getLogger("dem_bones")


def configure_logging(
    level: Union[int, str, LogLevel] = LogLevel.INFO,
    to_console: bool = True,
    to_python: bool = True,
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """Configure logging for both Python and C++ components.

    Args:
        level: The logging level. Can be a Python logging level (e.g., logging.INFO),
              a string level name (e.g., 'INFO'), or a C++ LogLevel enum value.
        to_console: Whether to log to the console.
        to_python: Whether to forward C++ logs to Python logging system.
        format_string: Custom format string for Python logging. If None, uses a default format.
        log_file: If provided, also log to this file.
    """
    # Map Python logging levels to C++ LogLevel
    level_map = {
        "NOTSET": LogLevel.DEBUG,
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "WARNING": LogLevel.WARN,
        "ERROR": LogLevel.ERROR,
        "CRITICAL": LogLevel.CRITICAL,
    }

    # Convert level to appropriate types
    cpp_level = level
    py_level = level

    if isinstance(level, int):
        # Convert Python logging level to C++ LogLevel
        if level <= logging.DEBUG:
            cpp_level = LogLevel.DEBUG
        elif level <= logging.INFO:
            cpp_level = LogLevel.INFO
        elif level <= logging.WARNING:
            cpp_level = LogLevel.WARN
        elif level <= logging.ERROR:
            cpp_level = LogLevel.ERROR
        else:
            cpp_level = LogLevel.CRITICAL
    elif isinstance(level, str):
        # Convert string level to C++ LogLevel
        cpp_level = level_map.get(level.upper(), LogLevel.INFO)
        py_level = getattr(logging, level.upper(), logging.INFO)

    # Configure Python logging
    if format_string is None:
        format_string = "[%(asctime)s] %(levelname)s - %(message)s"

    handlers = []
    if to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(file_handler)

    # Configure the Python logger
    logger.setLevel(py_level if isinstance(py_level, int) else logging.INFO)
    logger.handlers = []
    for handler in handlers:
        logger.addHandler(handler)

    # Configure the C++ logger
    Logger.instance().init(cpp_level, to_console, to_python)


def get_logger() -> logging.Logger:
    """Get the Python logger for dem_bones.

    Returns:
        The configured Python logger instance.
    """
    return logger


# Convenience functions that mirror the C++ logging macros
def trace(message: str) -> None:
    """Log a trace message."""
    logger.debug(message)  # Python doesn't have TRACE, use DEBUG
    Logger.instance().trace(message)


def debug(message: str) -> None:
    """Log a debug message."""
    logger.debug(message)
    Logger.instance().debug(message)


def info(message: str) -> None:
    """Log an info message."""
    logger.info(message)
    Logger.instance().info(message)


def warn(message: str) -> None:
    """Log a warning message."""
    logger.warning(message)
    Logger.instance().warn(message)


def error(message: str) -> None:
    """Log an error message."""
    logger.error(message)
    Logger.instance().error(message)


def critical(message: str) -> None:
    """Log a critical message."""
    logger.critical(message)
    Logger.instance().critical(message)
