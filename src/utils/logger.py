"""Logging configuration module.

This module provides centralized logging configuration using Loguru.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger


class LoggerConfig:
    """Configure application logging."""

    def __init__(
        self,
        level: str = "INFO",
        console: bool = True,
        file: bool = True,
        file_path: Optional[str] = None,
        rotation: str = "10 MB",
        retention: str = "30 days",
        format_string: Optional[str] = None,
    ):
        """Initialize logger configuration.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            console: Enable console logging.
            file: Enable file logging.
            file_path: Log file path (supports {book_title} and {date} placeholders).
            rotation: Log rotation size.
            retention: Log retention period.
            format_string: Custom log format string.
        """
        self.level = level.upper()
        self.console = console
        self.file = file
        self.file_path = file_path
        self.rotation = rotation
        self.retention = retention
        self.format_string = format_string or self._default_format()
        self._configured = False

    def _default_format(self) -> str:
        """Get default log format.

        Returns:
            Default format string.
        """
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )

    def _resolve_log_path(self, book_title: Optional[str] = None) -> Path:
        """Resolve log file path with placeholders.

        Args:
            book_title: Book title for file naming.

        Returns:
            Resolved log file path.
        """
        if self.file_path is None:
            log_dir = Path("logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            return log_dir / f"app_{datetime.now():%Y%m%d_%H%M%S}.log"

        path_str = self.file_path
        # Replace placeholders
        if "{book_title}" in path_str and book_title:
            # Sanitize book title for filename
            safe_title = "".join(
                c for c in book_title if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            safe_title = safe_title.replace(" ", "_")
            path_str = path_str.replace("{book_title}", safe_title)
        elif "{book_title}" in path_str:
            path_str = path_str.replace("{book_title}", "app")

        if "{date}" in path_str:
            path_str = path_str.replace("{date}", f"{datetime.now():%Y%m%d}")

        log_path = Path(path_str)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path

    def configure(self, book_title: Optional[str] = None) -> None:
        """Configure logger with specified settings.

        Args:
            book_title: Book title for log file naming.
        """
        if self._configured:
            logger.warning("Logger already configured, skipping reconfiguration")
            return

        # Remove default handler
        logger.remove()

        # Add console handler
        if self.console:
            logger.add(
                sys.stderr,
                format=self.format_string,
                level=self.level,
                colorize=True,
            )

        # Add file handler
        if self.file:
            log_path = self._resolve_log_path(book_title)
            logger.add(
                log_path,
                format=self.format_string,
                level=self.level,
                rotation=self.rotation,
                retention=self.retention,
                encoding="utf-8",
            )
            logger.info(f"Logging to file: {log_path}")

        self._configured = True
        logger.info(f"Logger configured with level: {self.level}")

    def set_level(self, level: str) -> None:
        """Change logging level dynamically.

        Args:
            level: New logging level.
        """
        self.level = level.upper()
        logger.info(f"Logging level changed to: {self.level}")
        # Reconfigure to apply new level
        self._configured = False
        self.configure()


def setup_logger(
    level: str = "INFO",
    console: bool = True,
    file: bool = True,
    file_path: Optional[str] = None,
    book_title: Optional[str] = None,
) -> None:
    """Setup application logger with default configuration.

    Args:
        level: Logging level.
        console: Enable console logging.
        file: Enable file logging.
        file_path: Log file path.
        book_title: Book title for log file naming.
    """
    config = LoggerConfig(
        level=level,
        console=console,
        file=file,
        file_path=file_path,
    )
    config.configure(book_title)


def get_logger():
    """Get the configured logger instance.

    Returns:
        Loguru logger instance.
    """
    return logger
