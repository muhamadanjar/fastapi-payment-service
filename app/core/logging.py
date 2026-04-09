
import logging
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from app.config.config import get_settings

settings = get_settings()

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class LoggerConfig:
    """
    Centralized logger configuration class
    """
    
    # Default log file settings
    DEFAULT_MAX_BYTES = 10485760  # 10MB
    DEFAULT_BACKUP_COUNT = 5
    DEFAULT_ENCODING = "utf8"
    
    # Formatter configurations
    FORMATTERS = {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(levelname)s - %(message)s",
        },
        "celery": {
            "format": "[%(asctime)s: %(levelname)s/%(processName)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access": {
            "format": "%(asctime)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }


def get_logging_config() -> Dict[str, Any]:
    """
    Get the complete logging configuration dictionary for the application.
    
    This configuration includes:
    - Multiple formatters (default, detailed, simple, celery, access)
    - Console handler for stdout
    - File handlers for different log types (app, error, celery, access, database)
    - Rotating file handlers to prevent log files from growing too large
    
    Returns:
        Dict[str, Any]: Logging configuration dictionary compatible with logging.config.dictConfig()
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": LoggerConfig.FORMATTERS["default"],
            "detailed": LoggerConfig.FORMATTERS["detailed"],
            "simple": LoggerConfig.FORMATTERS["simple"],
            "celery": LoggerConfig.FORMATTERS["celery"],
            "access": LoggerConfig.FORMATTERS["access"],
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": sys.stdout,
            },
            "file_app": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(LOGS_DIR / "app.log"),
                "maxBytes": LoggerConfig.DEFAULT_MAX_BYTES,
                "backupCount": LoggerConfig.DEFAULT_BACKUP_COUNT,
                "encoding": LoggerConfig.DEFAULT_ENCODING,
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(LOGS_DIR / "error.log"),
                "maxBytes": LoggerConfig.DEFAULT_MAX_BYTES,
                "backupCount": LoggerConfig.DEFAULT_BACKUP_COUNT,
                "encoding": LoggerConfig.DEFAULT_ENCODING,
            },
            "file_celery": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "celery",
                "filename": str(LOGS_DIR / "celery.log"),
                "maxBytes": LoggerConfig.DEFAULT_MAX_BYTES,
                "backupCount": LoggerConfig.DEFAULT_BACKUP_COUNT,
                "encoding": LoggerConfig.DEFAULT_ENCODING,
            },
            "file_access": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "access",
                "filename": str(LOGS_DIR / "access.log"),
                "maxBytes": LoggerConfig.DEFAULT_MAX_BYTES,
                "backupCount": LoggerConfig.DEFAULT_BACKUP_COUNT,
                "encoding": LoggerConfig.DEFAULT_ENCODING,
            },
            "file_database": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(LOGS_DIR / "database.log"),
                "maxBytes": LoggerConfig.DEFAULT_MAX_BYTES,
                "backupCount": LoggerConfig.DEFAULT_BACKUP_COUNT,
                "encoding": LoggerConfig.DEFAULT_ENCODING,
            },
        },
        "loggers": {
            # Root logger configuration
            "": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file_app", "file_error"],
            },
            # Celery logger
            "celery": {
                "level": "INFO",
                "handlers": ["console", "file_celery", "file_error"],
                "propagate": False,
            },
            # Access logger
            "access": {
                "level": "INFO",
                "handlers": ["console", "file_access"],
                "propagate": False,
            },
            # Database logger
            "database": {
                "level": "INFO",
                "handlers": ["console", "file_database", "file_error"],
                "propagate": False,
            },
            # SQLAlchemy logger
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["file_database"],
                "propagate": False,
            },
        },
    }


def setup_logging() -> None:
    """
    Initialize the logging configuration for the entire application.
    
    This should be called once at application startup (e.g., in main.py).
    It applies the logging configuration from get_logging_config().
    """
    import logging.config
    
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Log that logging has been initialized
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized successfully")


def get_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = True,
    formatter: str = "detailed",
) -> logging.Logger:
    """
    Create and configure a logger with the specified settings.
    
    This is a helper function to easily create loggers anywhere in the application.
    
    Args:
        name: Name of the logger (usually __name__ of the module)
        log_file: Optional custom log file name (without path, will be saved in logs/)
                 If None, uses the default app.log
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
              If None, uses the application's default LOG_LEVEL
        console_output: Whether to output logs to console (default: True)
        file_output: Whether to output logs to file (default: True)
        formatter: Formatter to use (default, detailed, simple, celery, access)
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("This is an info message")
        
        >>> logger = get_logger(__name__, log_file="custom.log", level="DEBUG")
        >>> logger.debug("This is a debug message")
    """
    logger = logging.getLogger(name)
    
    # Set log level
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    else:
        logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    if formatter in LoggerConfig.FORMATTERS:
        fmt = logging.Formatter(
            LoggerConfig.FORMATTERS[formatter]["format"],
            datefmt=LoggerConfig.FORMATTERS[formatter].get("datefmt"),
        )
    else:
        fmt = logging.Formatter(
            LoggerConfig.FORMATTERS["detailed"]["format"],
            datefmt=LoggerConfig.FORMATTERS["detailed"]["datefmt"],
        )
    
    # Add console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(fmt)
        logger.addHandler(console_handler)
    
    # Add file handler
    if file_output:
        if log_file:
            file_path = LOGS_DIR / log_file
        else:
            file_path = LOGS_DIR / "app.log"
        
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=LoggerConfig.DEFAULT_MAX_BYTES,
            backupCount=LoggerConfig.DEFAULT_BACKUP_COUNT,
            encoding=LoggerConfig.DEFAULT_ENCODING,
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger


def create_custom_logger(
    name: str,
    log_file: str,
    level: str = "INFO",
    max_bytes: int = LoggerConfig.DEFAULT_MAX_BYTES,
    backup_count: int = LoggerConfig.DEFAULT_BACKUP_COUNT,
    formatter: str = "detailed",
    console_output: bool = True,
) -> logging.Logger:
    """
    Create a completely custom logger with full control over all settings.
    
    Args:
        name: Name of the logger
        log_file: Log file name (will be saved in logs/)
        level: Log level (default: INFO)
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        formatter: Formatter to use (default: detailed)
        console_output: Whether to also output to console (default: True)
    
    Returns:
        logging.Logger: Configured custom logger
    
    Example:
        >>> logger = create_custom_logger(
        ...     name="payment_processor",
        ...     log_file="payment.log",
        ...     level="DEBUG",
        ...     max_bytes=5242880,  # 5MB
        ...     backup_count=10
        ... )
        >>> logger.info("Payment processed successfully")
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()
    
    # Create formatter
    if formatter in LoggerConfig.FORMATTERS:
        fmt = logging.Formatter(
            LoggerConfig.FORMATTERS[formatter]["format"],
            datefmt=LoggerConfig.FORMATTERS[formatter].get("datefmt"),
        )
    else:
        fmt = logging.Formatter(
            LoggerConfig.FORMATTERS["detailed"]["format"],
            datefmt=LoggerConfig.FORMATTERS["detailed"]["datefmt"],
        )
    
    # Add file handler
    file_path = LOGS_DIR / log_file
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding=LoggerConfig.DEFAULT_ENCODING,
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(fmt)
        logger.addHandler(console_handler)
    
    logger.propagate = False
    
    return logger