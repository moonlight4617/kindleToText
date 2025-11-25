"""
OCRエンジン抽象インターフェース

このモジュールは、異なるOCRエンジン（Yomitoku、Tesseract等）を
統一的に扱うための抽象インターフェースを提供します。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple
from PIL import Image


@dataclass
class BoundingBox:
    """テキスト領域の境界ボックス"""
    left: int
    top: int
    width: int
    height: int
    confidence: float = 0.0


@dataclass
class TextBlock:
    """テキストブロック（検出されたテキスト領域）"""
    text: str
    bounding_box: BoundingBox
    confidence: float
    block_type: str = "text"  # "text", "heading", "caption" etc.
    font_size: Optional[int] = None
    is_bold: bool = False


@dataclass
class LayoutData:
    """レイアウト情報を含むOCR結果"""
    full_text: str
    blocks: List[TextBlock]
    page_width: int
    page_height: int
    language: str = "jpn"
    average_confidence: float = 0.0


@dataclass
class OCRResult:
    """OCR処理結果"""
    text: str
    confidence: float
    layout: Optional[LayoutData] = None
    engine_name: str = ""
    processing_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


class OCRInterface(ABC):
    """
    OCRエンジンの抽象インターフェース

    すべてのOCRエンジンはこのインターフェースを実装する必要があります。
    """

    @abstractmethod
    def initialize(self) -> bool:
        """
        OCRエンジンを初期化する

        Returns:
            bool: 初期化に成功した場合はTrue、失敗した場合はFalse
        """
        pass

    @abstractmethod
    def extract_text(self, image: Image.Image) -> OCRResult:
        """
        画像からテキストを抽出する

        Args:
            image: 入力画像（PIL Image）

        Returns:
            OCRResult: OCR結果
        """
        pass

    @abstractmethod
    def extract_with_layout(self, image: Image.Image) -> OCRResult:
        """
        画像からテキストとレイアウト情報を抽出する

        Args:
            image: 入力画像（PIL Image）

        Returns:
            OCRResult: レイアウト情報を含むOCR結果
        """
        pass

    @abstractmethod
    def get_engine_name(self) -> str:
        """
        エンジン名を取得する

        Returns:
            str: エンジン名
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        エンジンが利用可能かチェックする

        Returns:
            bool: 利用可能な場合はTrue
        """
        pass

    def close(self) -> None:
        """
        エンジンのリソースを解放する（オプション）
        """
        pass


class OCREngineFactory:
    """
    OCRエンジンのファクトリークラス

    エンジン名に基づいて適切なOCRエンジンインスタンスを生成します。
    """

    _engines = {}

    @classmethod
    def register_engine(cls, name: str, engine_class):
        """
        エンジンを登録する

        Args:
            name: エンジン名
            engine_class: エンジンクラス
        """
        cls._engines[name.lower()] = engine_class

    @classmethod
    def create_engine(cls, name: str, config: Optional[dict] = None) -> Optional[OCRInterface]:
        """
        エンジンを生成する

        Args:
            name: エンジン名（"yomitoku", "tesseract"）
            config: エンジン設定（オプション）

        Returns:
            OCRInterface: OCRエンジンインスタンス。見つからない場合はNone
        """
        engine_class = cls._engines.get(name.lower())
        if engine_class is None:
            return None

        engine = engine_class(config or {})
        return engine

    @classmethod
    def get_available_engines(cls) -> List[str]:
        """
        利用可能なエンジンのリストを取得する

        Returns:
            List[str]: 利用可能なエンジン名のリスト
        """
        available = []
        for name, engine_class in cls._engines.items():
            try:
                engine = engine_class({})
                if engine.is_available():
                    available.append(name)
            except Exception:
                pass
        return available


class OCREngineSelector:
    """
    OCRエンジン選択クラス

    優先順位に基づいて利用可能なエンジンを自動選択します。
    """

    def __init__(self, preferred_engines: Optional[List[str]] = None):
        """
        OCREngineSelectorの初期化

        Args:
            preferred_engines: 優先エンジンのリスト（順序付き）
                              指定がない場合はデフォルト優先順位を使用
        """
        self.preferred_engines = preferred_engines or ["yomitoku", "tesseract"]

    def select_engine(
        self,
        config: Optional[dict] = None,
        fallback: bool = True
    ) -> Optional[OCRInterface]:
        """
        利用可能なエンジンを選択する

        Args:
            config: エンジン設定
            fallback: フォールバック有効化

        Returns:
            OCRInterface: 選択されたエンジン。利用可能なエンジンがない場合はNone
        """
        for engine_name in self.preferred_engines:
            engine = OCREngineFactory.create_engine(engine_name, config)
            if engine and engine.is_available():
                if engine.initialize():
                    return engine

        if not fallback:
            return None

        # フォールバック: 登録されている全エンジンを試す
        for engine_name in OCREngineFactory.get_available_engines():
            if engine_name not in self.preferred_engines:
                engine = OCREngineFactory.create_engine(engine_name, config)
                if engine and engine.initialize():
                    return engine

        return None


def create_default_ocr_engine(config: Optional[dict] = None) -> Optional[OCRInterface]:
    """
    デフォルトのOCRエンジンを作成する便利関数

    Args:
        config: エンジン設定

    Returns:
        OCRInterface: OCRエンジンインスタンス
    """
    selector = OCREngineSelector()
    return selector.select_engine(config)
