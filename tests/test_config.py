"""Unit tests for config module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.config.config_loader import ConfigLoader, load_config
from src.config.settings import Settings, load_settings


class TestConfigLoader:
    """Test cases for ConfigLoader class."""

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration dictionary."""
        return {
            "kindle": {"window_title": "Kindle", "page_turn_key": "Right"},
            "ocr": {
                "primary_engine": "yomitoku",
                "yomitoku": {"confidence_threshold": 0.7},
            },
            "logging": {"level": "DEBUG"},
        }

    @pytest.fixture
    def config_file(self, sample_config):
        """Create temporary configuration file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(sample_config, f)
            return Path(f.name)

    def test_load_config_success(self, config_file, sample_config):
        """Test successful configuration loading."""
        loader = ConfigLoader(str(config_file))
        config = loader.load()

        assert config == sample_config
        assert config["kindle"]["window_title"] == "Kindle"

        # Cleanup
        config_file.unlink()

    def test_load_config_file_not_found(self):
        """Test loading non-existent configuration file."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader("nonexistent.yaml")

    def test_get_value_simple_key(self, config_file):
        """Test getting value with simple key."""
        loader = ConfigLoader(str(config_file))
        loader.load()

        assert loader.get("logging") == {"level": "DEBUG"}

        # Cleanup
        config_file.unlink()

    def test_get_value_dot_notation(self, config_file):
        """Test getting value with dot notation."""
        loader = ConfigLoader(str(config_file))
        loader.load()

        assert loader.get("kindle.window_title") == "Kindle"
        assert loader.get("ocr.yomitoku.confidence_threshold") == 0.7

        # Cleanup
        config_file.unlink()

    def test_get_value_with_default(self, config_file):
        """Test getting non-existent value with default."""
        loader = ConfigLoader(str(config_file))
        loader.load()

        assert loader.get("nonexistent", "default") == "default"
        assert loader.get("kindle.nonexistent", 123) == 123

        # Cleanup
        config_file.unlink()

    def test_get_section(self, config_file):
        """Test getting configuration section."""
        loader = ConfigLoader(str(config_file))
        loader.load()

        kindle_config = loader.get_section("kindle")
        assert kindle_config["window_title"] == "Kindle"
        assert kindle_config["page_turn_key"] == "Right"

        # Cleanup
        config_file.unlink()

    def test_get_section_not_found(self, config_file):
        """Test getting non-existent section."""
        loader = ConfigLoader(str(config_file))
        loader.load()

        with pytest.raises(KeyError):
            loader.get_section("nonexistent")

        # Cleanup
        config_file.unlink()

    def test_validate_required_keys_success(self, config_file):
        """Test validation with all required keys present."""
        loader = ConfigLoader(str(config_file))
        loader.load()

        required = ["kindle.window_title", "ocr.primary_engine", "logging.level"]
        assert loader.validate_required_keys(required) is True

        # Cleanup
        config_file.unlink()

    def test_validate_required_keys_missing(self, config_file):
        """Test validation with missing required keys."""
        loader = ConfigLoader(str(config_file))
        loader.load()

        required = ["kindle.window_title", "nonexistent.key"]
        with pytest.raises(ValueError, match="Missing required configuration keys"):
            loader.validate_required_keys(required)

        # Cleanup
        config_file.unlink()

    def test_reload_config(self, config_file, sample_config):
        """Test reloading configuration."""
        loader = ConfigLoader(str(config_file))
        config1 = loader.load()

        # Modify file
        sample_config["logging"]["level"] = "INFO"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)

        config2 = loader.reload()
        assert config2["logging"]["level"] == "INFO"

        # Cleanup
        config_file.unlink()

    def test_config_property(self, config_file):
        """Test config property."""
        loader = ConfigLoader(str(config_file))

        # Config should load automatically when accessed
        config = loader.config
        assert config is not None
        assert "kindle" in config

        # Cleanup
        config_file.unlink()


class TestSettings:
    """Test cases for Settings class."""

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration dictionary."""
        return {
            "kindle": {
                "window_title": "Kindle",
                "page_turn_key": "Right",
                "page_turn_delay": 1.5,
            },
            "ocr": {
                "primary_engine": "google_vision",
                "yomitoku": {"confidence_threshold": 0.7, "device": "cpu"},
                "google_vision": {
                    "credentials_path": "config/google_credentials.json",
                    "detection_type": "DOCUMENT_TEXT_DETECTION",
                    "language_hints": ["ja", "en"],
                },
            },
            "logging": {"level": "INFO", "console": True},
        }

    def test_settings_from_dict(self, sample_config):
        """Test creating Settings from dictionary."""
        settings = Settings.from_dict(sample_config)

        assert settings.kindle.window_title == "Kindle"
        assert settings.kindle.page_turn_delay == 1.5
        assert settings.ocr.primary_engine == "google_vision"
        assert settings.ocr.yomitoku.confidence_threshold == 0.7
        assert settings.logging.level == "INFO"

    def test_settings_with_defaults(self):
        """Test Settings with default values."""
        settings = Settings.from_dict({})

        # Should use default values
        assert settings.kindle.window_title == "Kindle"
        assert settings.ocr.primary_engine == "google_vision"
        assert settings.logging.level == "INFO"

    def test_settings_partial_config(self):
        """Test Settings with partial configuration."""
        partial_config = {
            "kindle": {"window_title": "Custom Kindle"},
            # Other sections will use defaults
        }

        settings = Settings.from_dict(partial_config)

        assert settings.kindle.window_title == "Custom Kindle"
        # Default values for other settings
        assert settings.ocr.primary_engine == "google_vision"

    def test_screenshot_region_tuple(self):
        """Test screenshot region conversion to tuple."""
        from src.config.settings import ScreenshotSettings

        # With all values specified
        settings = ScreenshotSettings(region={"x": 10, "y": 20, "width": 800, "height": 600})
        assert settings.get_region() == (10, 20, 800, 600)

        # With None values (auto-detect)
        settings = ScreenshotSettings(region={"x": None, "y": None, "width": None, "height": None})
        assert settings.get_region() is None

        # With no region specified
        settings = ScreenshotSettings()
        assert settings.get_region() is None
