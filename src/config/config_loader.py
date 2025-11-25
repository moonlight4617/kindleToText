"""Configuration loader module.

This module provides functionality to load and validate YAML configuration files.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from loguru import logger


class ConfigLoader:
    """Load and manage configuration from YAML files."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize ConfigLoader.

        Args:
            config_path: Path to configuration file. If None, uses default path.
        """
        self.config_path = self._resolve_config_path(config_path)
        self._config: Optional[Dict[str, Any]] = None

    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """Resolve configuration file path.

        Args:
            config_path: Path to configuration file or None for default.

        Returns:
            Resolved Path object.

        Raises:
            FileNotFoundError: If configuration file does not exist.
        """
        if config_path is None:
            # Default to config/config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Please copy config/config.example.yaml to config/config.yaml"
            )

        return config_path

    def load(self) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            Configuration dictionary.

        Raises:
            yaml.YAMLError: If YAML parsing fails.
            FileNotFoundError: If configuration file does not exist.
        """
        try:
            logger.info(f"Loading configuration from: {self.config_path}")
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)

            if self._config is None:
                self._config = {}

            logger.debug(f"Configuration loaded successfully: {len(self._config)} sections")
            return self._config

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., "kindle.window_title")
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        if self._config is None:
            self.load()

        # Support dot notation for nested keys
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section.

        Args:
            section: Section name (e.g., "kindle", "ocr").

        Returns:
            Configuration section dictionary.

        Raises:
            KeyError: If section does not exist.
        """
        if self._config is None:
            self.load()

        if section not in self._config:
            raise KeyError(f"Configuration section '{section}' not found")

        return self._config[section]

    def reload(self) -> Dict[str, Any]:
        """Reload configuration from file.

        Returns:
            Reloaded configuration dictionary.
        """
        logger.info("Reloading configuration")
        return self.load()

    def validate_required_keys(self, required_keys: list[str]) -> bool:
        """Validate that required configuration keys exist.

        Args:
            required_keys: List of required keys (supports dot notation).

        Returns:
            True if all required keys exist.

        Raises:
            ValueError: If any required key is missing.
        """
        if self._config is None:
            self.load()

        missing_keys = []
        for key in required_keys:
            if self.get(key) is None:
                missing_keys.append(key)

        if missing_keys:
            raise ValueError(
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )

        logger.debug(f"All required keys validated: {len(required_keys)} keys")
        return True

    @property
    def config(self) -> Dict[str, Any]:
        """Get full configuration dictionary.

        Returns:
            Configuration dictionary.
        """
        if self._config is None:
            self.load()
        return self._config


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to load configuration.

    Args:
        config_path: Path to configuration file or None for default.

    Returns:
        Configuration dictionary.
    """
    loader = ConfigLoader(config_path)
    return loader.load()
