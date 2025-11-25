"""Settings classes for configuration management.

This module provides typed settings classes for different configuration sections.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config_loader import ConfigLoader


@dataclass
class KindleSettings:
    """Kindle application settings."""

    window_title: str = "Kindle"
    page_turn_key: str = "Right"
    page_turn_delay: float = 1.5
    window_activation_delay: float = 0.5


@dataclass
class ScreenshotSettings:
    """Screenshot capture settings."""

    format: str = "png"
    quality: int = 95
    region: Optional[Dict[str, Optional[int]]] = None
    auto_trim: bool = True

    def get_region(self) -> Optional[Tuple[int, int, int, int]]:
        """Get screenshot region as tuple.

        Returns:
            (x, y, width, height) or None if auto-detect.
        """
        if self.region is None:
            return None

        x = self.region.get("x")
        y = self.region.get("y")
        width = self.region.get("width")
        height = self.region.get("height")

        if all(v is not None for v in [x, y, width, height]):
            return (x, y, width, height)
        return None


@dataclass
class NoiseReductionSettings:
    """Noise reduction settings."""

    enabled: bool = True
    method: str = "gaussian"
    kernel_size: int = 3


@dataclass
class ContrastSettings:
    """Contrast adjustment settings."""

    enabled: bool = True
    method: str = "clahe"
    clip_limit: float = 2.0
    tile_grid_size: Tuple[int, int] = (8, 8)


@dataclass
class SkewCorrectionSettings:
    """Skew correction settings."""

    enabled: bool = True
    angle_threshold: float = 0.5
    method: str = "hough"


@dataclass
class MarginTrimSettings:
    """Margin trimming settings."""

    enabled: bool = True
    threshold: int = 240
    padding: int = 10


@dataclass
class BinarizationSettings:
    """Binarization settings."""

    enabled: bool = True
    method: str = "adaptive"
    block_size: int = 11
    c: int = 2
    threshold: int = 127


@dataclass
class PreprocessingSettings:
    """Image preprocessing settings."""

    noise_reduction: NoiseReductionSettings = field(default_factory=NoiseReductionSettings)
    contrast: ContrastSettings = field(default_factory=ContrastSettings)
    skew_correction: SkewCorrectionSettings = field(default_factory=SkewCorrectionSettings)
    margin_trim: MarginTrimSettings = field(default_factory=MarginTrimSettings)
    binarization: BinarizationSettings = field(default_factory=BinarizationSettings)


@dataclass
class YomitokuSettings:
    """Yomitoku OCR engine settings."""

    model_path: Optional[str] = None
    confidence_threshold: float = 0.6
    device: str = "cpu"
    batch_size: int = 1


@dataclass
class TesseractSettings:
    """Tesseract OCR engine settings."""

    lang: str = "jpn"
    config: str = "--psm 6"
    confidence_threshold: float = 0.5
    tesseract_cmd: Optional[str] = None


@dataclass
class OCRSettings:
    """OCR processing settings."""

    primary_engine: str = "yomitoku"
    fallback_engine: str = "tesseract"
    retry_on_failure: bool = True
    max_retries: int = 3
    yomitoku: YomitokuSettings = field(default_factory=YomitokuSettings)
    tesseract: TesseractSettings = field(default_factory=TesseractSettings)


@dataclass
class FormattingSettings:
    """Text formatting settings."""

    preserve_linebreaks: bool = True
    remove_duplicates: bool = True
    trim_whitespace: bool = True
    normalize_spaces: bool = True


@dataclass
class OutputSettings:
    """Output file settings."""

    base_dir: str = "output"
    encoding: str = "utf-8"
    include_metadata: bool = True
    append_mode: bool = True
    formatting: FormattingSettings = field(default_factory=FormattingSettings)


@dataclass
class HeadingDetectionSettings:
    """Heading detection settings."""

    enabled: bool = True
    methods: List[str] = field(default_factory=lambda: ["font_size", "position"])
    font_size_threshold: float = 1.2
    position_based_weight: float = 0.7
    heading_markers: Dict[str, str] = field(
        default_factory=lambda: {"h1": "# ", "h2": "## ", "h3": "### "}
    )


@dataclass
class StateSettings:
    """State management settings."""

    enabled: bool = True
    save_interval: int = 10
    auto_save_on_error: bool = True
    state_dir: str = "output"
    cleanup_on_completion: bool = False


@dataclass
class ProgressSettings:
    """Progress display settings."""

    show_progress_bar: bool = True
    show_current_page: bool = True
    show_percentage: bool = True
    show_eta: bool = True
    update_interval: float = 1.0


@dataclass
class LoggingSettings:
    """Logging settings."""

    level: str = "INFO"
    console: bool = True
    file: bool = True
    file_path: str = "logs/{book_title}_{date}.log"
    rotation: str = "10 MB"
    retention: str = "30 days"
    format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
        "<level>{message}</level>"
    )


@dataclass
class ErrorHandlingSettings:
    """Error handling settings."""

    abort_on_window_not_found: bool = True
    abort_on_config_error: bool = True
    retry_screenshot_failure: bool = True
    retry_ocr_failure: bool = True
    retry_file_io_failure: bool = True
    max_consecutive_failures: int = 5
    warn_on_low_confidence: bool = True
    low_confidence_threshold: float = 0.5


@dataclass
class PerformanceSettings:
    """Performance settings."""

    priority: str = "accuracy"
    screenshot_delay: float = 0.5
    ocr_timeout: int = 60
    max_image_size: Tuple[int, int] = (3000, 3000)
    memory_limit: Optional[int] = None


@dataclass
class AdvancedSettings:
    """Advanced settings."""

    debug_mode: bool = False
    debug_output_dir: str = "debug"
    profile_performance: bool = False
    verify_kindle_window: bool = True


@dataclass
class Settings:
    """Main settings class containing all configuration sections."""

    kindle: KindleSettings = field(default_factory=KindleSettings)
    screenshot: ScreenshotSettings = field(default_factory=ScreenshotSettings)
    preprocessing: PreprocessingSettings = field(default_factory=PreprocessingSettings)
    ocr: OCRSettings = field(default_factory=OCRSettings)
    output: OutputSettings = field(default_factory=OutputSettings)
    heading_detection: HeadingDetectionSettings = field(
        default_factory=HeadingDetectionSettings
    )
    state: StateSettings = field(default_factory=StateSettings)
    progress: ProgressSettings = field(default_factory=ProgressSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    error_handling: ErrorHandlingSettings = field(default_factory=ErrorHandlingSettings)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    advanced: AdvancedSettings = field(default_factory=AdvancedSettings)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "Settings":
        """Create Settings from configuration dictionary.

        Args:
            config: Configuration dictionary from YAML.

        Returns:
            Settings instance.
        """
        # Helper function to create nested dataclass instances
        def create_instance(dataclass_type, data):
            if data is None:
                return dataclass_type()
            if not isinstance(data, dict):
                return data

            # Get field types from dataclass
            field_types = {f.name: f.type for f in dataclass_type.__dataclass_fields__.values()}
            kwargs = {}

            for key, value in data.items():
                if key in field_types:
                    field_type = field_types[key]
                    # Check if field type is a dataclass
                    if hasattr(field_type, '__dataclass_fields__'):
                        kwargs[key] = create_instance(field_type, value)
                    else:
                        kwargs[key] = value

            return dataclass_type(**kwargs)

        # Create settings with nested structures
        return cls(
            kindle=create_instance(KindleSettings, config.get("kindle")),
            screenshot=create_instance(ScreenshotSettings, config.get("screenshot")),
            preprocessing=create_instance(PreprocessingSettings, config.get("preprocessing")),
            ocr=create_instance(OCRSettings, config.get("ocr")),
            output=create_instance(OutputSettings, config.get("output")),
            heading_detection=create_instance(
                HeadingDetectionSettings, config.get("heading_detection")
            ),
            state=create_instance(StateSettings, config.get("state")),
            progress=create_instance(ProgressSettings, config.get("progress")),
            logging=create_instance(LoggingSettings, config.get("logging")),
            error_handling=create_instance(
                ErrorHandlingSettings, config.get("error_handling")
            ),
            performance=create_instance(PerformanceSettings, config.get("performance")),
            advanced=create_instance(AdvancedSettings, config.get("advanced")),
        )

    @classmethod
    def from_file(cls, config_path: Optional[str] = None) -> "Settings":
        """Load settings from configuration file.

        Args:
            config_path: Path to configuration file or None for default.

        Returns:
            Settings instance.
        """
        loader = ConfigLoader(config_path)
        config = loader.load()
        return cls.from_dict(config)


def load_settings(config_path: Optional[str] = None) -> Settings:
    """Convenience function to load settings.

    Args:
        config_path: Path to configuration file or None for default.

    Returns:
        Settings instance.
    """
    return Settings.from_file(config_path)
