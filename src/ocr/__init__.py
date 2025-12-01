"""
OCR processing module

このモジュールは、画像からテキストを抽出するOCR機能を提供します。
複数のOCRエンジン（Yomitoku、Tesseract、Google Cloud Vision）をサポートします。
"""

from .ocr_interface import (
    OCRInterface,
    OCRResult,
    LayoutData,
    TextBlock,
    BoundingBox,
    OCREngineFactory,
    OCREngineSelector,
    create_default_ocr_engine
)
from .yomitoku_engine import YomitokuEngine
from .tesseract_engine import TesseractEngine
from .google_vision_engine import GoogleVisionEngine

__all__ = [
    "OCRInterface",
    "OCRResult",
    "LayoutData",
    "TextBlock",
    "BoundingBox",
    "OCREngineFactory",
    "OCREngineSelector",
    "YomitokuEngine",
    "TesseractEngine",
    "GoogleVisionEngine",
    "create_default_ocr_engine",
]
