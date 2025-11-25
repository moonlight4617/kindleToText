"""Validation utilities.

This module provides validation functions for user inputs and file operations.
"""

import re
from pathlib import Path
from typing import Optional


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_book_title(title: str) -> str:
    """Validate and sanitize book title.

    Args:
        title: Book title to validate.

    Returns:
        Sanitized book title.

    Raises:
        ValidationError: If title is invalid.
    """
    if not title or not title.strip():
        raise ValidationError("Book title cannot be empty")

    # Remove leading/trailing whitespace
    title = title.strip()

    # Check for excessively long titles
    if len(title) > 200:
        raise ValidationError("Book title is too long (maximum 200 characters)")

    return title


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """Sanitize filename by removing invalid characters.

    Args:
        filename: Filename to sanitize.
        replacement: Character to replace invalid characters with.

    Returns:
        Sanitized filename.
    """
    # Windows forbidden characters: < > : " / \ | ? *
    # Also remove control characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, replacement, filename)

    # Remove leading/trailing spaces and dots (Windows limitation)
    sanitized = sanitized.strip(". ")

    # Ensure filename is not empty after sanitization
    if not sanitized:
        sanitized = "untitled"

    return sanitized


def validate_file_path(path: str, must_exist: bool = False) -> Path:
    """Validate file path.

    Args:
        path: File path to validate.
        must_exist: If True, file must exist.

    Returns:
        Validated Path object.

    Raises:
        ValidationError: If path is invalid or file doesn't exist when required.
    """
    if not path or not path.strip():
        raise ValidationError("File path cannot be empty")

    try:
        file_path = Path(path)
    except Exception as e:
        raise ValidationError(f"Invalid file path: {e}")

    if must_exist and not file_path.exists():
        raise ValidationError(f"File does not exist: {path}")

    return file_path


def validate_directory_path(path: str, create_if_missing: bool = False) -> Path:
    """Validate directory path.

    Args:
        path: Directory path to validate.
        create_if_missing: If True, create directory if it doesn't exist.

    Returns:
        Validated Path object.

    Raises:
        ValidationError: If path is invalid.
    """
    if not path or not path.strip():
        raise ValidationError("Directory path cannot be empty")

    try:
        dir_path = Path(path)
    except Exception as e:
        raise ValidationError(f"Invalid directory path: {e}")

    if create_if_missing and not dir_path.exists():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValidationError(f"Failed to create directory: {e}")

    if dir_path.exists() and not dir_path.is_dir():
        raise ValidationError(f"Path exists but is not a directory: {path}")

    return dir_path


def validate_page_number(page: int, min_page: int = 1, max_page: Optional[int] = None) -> int:
    """Validate page number.

    Args:
        page: Page number to validate.
        min_page: Minimum valid page number.
        max_page: Maximum valid page number (None for no limit).

    Returns:
        Validated page number.

    Raises:
        ValidationError: If page number is invalid.
    """
    if not isinstance(page, int):
        raise ValidationError(f"Page number must be an integer, got {type(page).__name__}")

    if page < min_page:
        raise ValidationError(f"Page number must be >= {min_page}, got {page}")

    if max_page is not None and page > max_page:
        raise ValidationError(f"Page number must be <= {max_page}, got {page}")

    return page


def validate_page_range(
    start_page: int, end_page: Optional[int] = None, max_page: Optional[int] = None
) -> tuple[int, Optional[int]]:
    """Validate page range.

    Args:
        start_page: Starting page number.
        end_page: Ending page number (None for no limit).
        max_page: Maximum valid page number (None for no limit).

    Returns:
        Validated (start_page, end_page) tuple.

    Raises:
        ValidationError: If page range is invalid.
    """
    start_page = validate_page_number(start_page, min_page=1, max_page=max_page)

    if end_page is not None:
        end_page = validate_page_number(end_page, min_page=1, max_page=max_page)

        if end_page < start_page:
            raise ValidationError(
                f"End page ({end_page}) must be >= start page ({start_page})"
            )

    return start_page, end_page


def validate_confidence_threshold(threshold: float) -> float:
    """Validate confidence threshold.

    Args:
        threshold: Confidence threshold (0.0 to 1.0).

    Returns:
        Validated threshold.

    Raises:
        ValidationError: If threshold is invalid.
    """
    if not isinstance(threshold, (int, float)):
        raise ValidationError(
            f"Confidence threshold must be a number, got {type(threshold).__name__}"
        )

    if not 0.0 <= threshold <= 1.0:
        raise ValidationError(
            f"Confidence threshold must be between 0.0 and 1.0, got {threshold}"
        )

    return float(threshold)


def validate_image_format(format: str) -> str:
    """Validate image format.

    Args:
        format: Image format (e.g., 'png', 'jpg').

    Returns:
        Validated format in lowercase.

    Raises:
        ValidationError: If format is invalid.
    """
    valid_formats = {"png", "jpg", "jpeg", "bmp", "tiff"}
    format_lower = format.lower().strip()

    if format_lower not in valid_formats:
        raise ValidationError(
            f"Invalid image format '{format}'. Must be one of: {', '.join(valid_formats)}"
        )

    return format_lower


def validate_ocr_engine(engine: str) -> str:
    """Validate OCR engine name.

    Args:
        engine: OCR engine name.

    Returns:
        Validated engine name in lowercase.

    Raises:
        ValidationError: If engine is invalid.
    """
    valid_engines = {"yomitoku", "tesseract"}
    engine_lower = engine.lower().strip()

    if engine_lower not in valid_engines:
        raise ValidationError(
            f"Invalid OCR engine '{engine}'. Must be one of: {', '.join(valid_engines)}"
        )

    return engine_lower


def validate_log_level(level: str) -> str:
    """Validate logging level.

    Args:
        level: Logging level.

    Returns:
        Validated level in uppercase.

    Raises:
        ValidationError: If level is invalid.
    """
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    level_upper = level.upper().strip()

    if level_upper not in valid_levels:
        raise ValidationError(
            f"Invalid log level '{level}'. Must be one of: {', '.join(valid_levels)}"
        )

    return level_upper


def validate_positive_integer(value: int, name: str = "value") -> int:
    """Validate positive integer.

    Args:
        value: Integer value to validate.
        name: Name of the value for error messages.

    Returns:
        Validated integer.

    Raises:
        ValidationError: If value is invalid.
    """
    if not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer, got {type(value).__name__}")

    if value <= 0:
        raise ValidationError(f"{name} must be positive, got {value}")

    return value


def validate_non_negative_number(value: float, name: str = "value") -> float:
    """Validate non-negative number.

    Args:
        value: Number to validate.
        name: Name of the value for error messages.

    Returns:
        Validated number.

    Raises:
        ValidationError: If value is invalid.
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")

    if value < 0:
        raise ValidationError(f"{name} must be non-negative, got {value}")

    return float(value)
