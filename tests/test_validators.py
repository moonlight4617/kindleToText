"""Unit tests for validators module."""

import tempfile
from pathlib import Path

import pytest

from src.utils.validators import (
    ValidationError,
    sanitize_filename,
    validate_book_title,
    validate_confidence_threshold,
    validate_directory_path,
    validate_file_path,
    validate_image_format,
    validate_log_level,
    validate_non_negative_number,
    validate_ocr_engine,
    validate_page_number,
    validate_page_range,
    validate_positive_integer,
)


class TestValidateBookTitle:
    """Test cases for validate_book_title."""

    def test_valid_title(self):
        """Test validation with valid title."""
        assert validate_book_title("My Book") == "My Book"
        assert validate_book_title("深層学習入門") == "深層学習入門"

    def test_title_with_whitespace(self):
        """Test title with leading/trailing whitespace."""
        assert validate_book_title("  My Book  ") == "My Book"

    def test_empty_title(self):
        """Test validation with empty title."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_book_title("")

    def test_whitespace_only_title(self):
        """Test validation with whitespace-only title."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_book_title("   ")

    def test_long_title(self):
        """Test validation with excessively long title."""
        long_title = "A" * 201
        with pytest.raises(ValidationError, match="too long"):
            validate_book_title(long_title)


class TestSanitizeFilename:
    """Test cases for sanitize_filename."""

    def test_valid_filename(self):
        """Test sanitizing valid filename."""
        assert sanitize_filename("my_file.txt") == "my_file.txt"

    def test_filename_with_invalid_chars(self):
        """Test sanitizing filename with invalid characters."""
        assert sanitize_filename("my<file>.txt") == "my_file_.txt"
        assert sanitize_filename("file:name|test.txt") == "file_name_test.txt"
        assert sanitize_filename('file"path"/test.txt') == "file_path__test.txt"

    def test_filename_with_spaces(self):
        """Test sanitizing filename with spaces."""
        assert sanitize_filename("  my file.txt  ") == "my file.txt"

    def test_empty_filename(self):
        """Test sanitizing empty filename."""
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("...") == "untitled"


class TestValidateFilePath:
    """Test cases for validate_file_path."""

    def test_valid_path(self):
        """Test validation with valid path."""
        path = validate_file_path("test.txt")
        assert isinstance(path, Path)
        assert path == Path("test.txt")

    def test_empty_path(self):
        """Test validation with empty path."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_file_path("")

    def test_must_exist_true(self):
        """Test validation requiring existing file."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            path = validate_file_path(temp_path, must_exist=True)
            assert path.exists()
        finally:
            Path(temp_path).unlink()

    def test_must_exist_false(self):
        """Test validation not requiring existing file."""
        path = validate_file_path("nonexistent.txt", must_exist=False)
        assert isinstance(path, Path)

    def test_nonexistent_file_must_exist(self):
        """Test validation failing for non-existent file."""
        with pytest.raises(ValidationError, match="does not exist"):
            validate_file_path("nonexistent_file.txt", must_exist=True)


class TestValidateDirectoryPath:
    """Test cases for validate_directory_path."""

    def test_valid_directory(self):
        """Test validation with valid directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = validate_directory_path(tmpdir)
            assert path.is_dir()

    def test_create_if_missing(self):
        """Test creating directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new_dir"
            path = validate_directory_path(str(new_dir), create_if_missing=True)
            assert path.exists()
            assert path.is_dir()

    def test_empty_path(self):
        """Test validation with empty path."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_directory_path("")

    def test_path_is_file_not_directory(self):
        """Test validation failing when path is file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValidationError, match="not a directory"):
                validate_directory_path(temp_path)
        finally:
            Path(temp_path).unlink()


class TestValidatePageNumber:
    """Test cases for validate_page_number."""

    def test_valid_page_number(self):
        """Test validation with valid page number."""
        assert validate_page_number(1) == 1
        assert validate_page_number(100) == 100

    def test_page_below_minimum(self):
        """Test validation with page below minimum."""
        with pytest.raises(ValidationError, match="must be >= 1"):
            validate_page_number(0)

    def test_page_above_maximum(self):
        """Test validation with page above maximum."""
        with pytest.raises(ValidationError, match="must be <= 100"):
            validate_page_number(101, max_page=100)

    def test_non_integer_page(self):
        """Test validation with non-integer page."""
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_page_number("10")


class TestValidatePageRange:
    """Test cases for validate_page_range."""

    def test_valid_range(self):
        """Test validation with valid range."""
        start, end = validate_page_range(1, 100)
        assert start == 1
        assert end == 100

    def test_range_with_none_end(self):
        """Test validation with no end page."""
        start, end = validate_page_range(1, None)
        assert start == 1
        assert end is None

    def test_end_before_start(self):
        """Test validation with end before start."""
        with pytest.raises(ValidationError, match="must be >= start page"):
            validate_page_range(100, 50)


class TestValidateConfidenceThreshold:
    """Test cases for validate_confidence_threshold."""

    def test_valid_threshold(self):
        """Test validation with valid threshold."""
        assert validate_confidence_threshold(0.5) == 0.5
        assert validate_confidence_threshold(0.0) == 0.0
        assert validate_confidence_threshold(1.0) == 1.0

    def test_threshold_below_zero(self):
        """Test validation with threshold below 0."""
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            validate_confidence_threshold(-0.1)

    def test_threshold_above_one(self):
        """Test validation with threshold above 1."""
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            validate_confidence_threshold(1.1)

    def test_non_numeric_threshold(self):
        """Test validation with non-numeric threshold."""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_confidence_threshold("0.5")


class TestValidateImageFormat:
    """Test cases for validate_image_format."""

    def test_valid_formats(self):
        """Test validation with valid formats."""
        assert validate_image_format("png") == "png"
        assert validate_image_format("PNG") == "png"
        assert validate_image_format("jpg") == "jpg"
        assert validate_image_format("JPEG") == "jpeg"

    def test_invalid_format(self):
        """Test validation with invalid format."""
        with pytest.raises(ValidationError, match="Invalid image format"):
            validate_image_format("gif")


class TestValidateOCREngine:
    """Test cases for validate_ocr_engine."""

    def test_valid_engines(self):
        """Test validation with valid engines."""
        assert validate_ocr_engine("yomitoku") == "yomitoku"
        assert validate_ocr_engine("YOMITOKU") == "yomitoku"
        assert validate_ocr_engine("tesseract") == "tesseract"

    def test_invalid_engine(self):
        """Test validation with invalid engine."""
        with pytest.raises(ValidationError, match="Invalid OCR engine"):
            validate_ocr_engine("unknown")


class TestValidateLogLevel:
    """Test cases for validate_log_level."""

    def test_valid_levels(self):
        """Test validation with valid levels."""
        assert validate_log_level("DEBUG") == "DEBUG"
        assert validate_log_level("debug") == "DEBUG"
        assert validate_log_level("INFO") == "INFO"

    def test_invalid_level(self):
        """Test validation with invalid level."""
        with pytest.raises(ValidationError, match="Invalid log level"):
            validate_log_level("TRACE")


class TestValidatePositiveInteger:
    """Test cases for validate_positive_integer."""

    def test_valid_positive_integer(self):
        """Test validation with valid positive integer."""
        assert validate_positive_integer(1) == 1
        assert validate_positive_integer(100) == 100

    def test_zero(self):
        """Test validation with zero."""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_positive_integer(0)

    def test_negative(self):
        """Test validation with negative number."""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_positive_integer(-1)

    def test_non_integer(self):
        """Test validation with non-integer."""
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_positive_integer(1.5)


class TestValidateNonNegativeNumber:
    """Test cases for validate_non_negative_number."""

    def test_valid_non_negative(self):
        """Test validation with valid non-negative number."""
        assert validate_non_negative_number(0) == 0.0
        assert validate_non_negative_number(1.5) == 1.5
        assert validate_non_negative_number(100) == 100.0

    def test_negative(self):
        """Test validation with negative number."""
        with pytest.raises(ValidationError, match="must be non-negative"):
            validate_non_negative_number(-1)

    def test_non_numeric(self):
        """Test validation with non-numeric value."""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_non_negative_number("10")
