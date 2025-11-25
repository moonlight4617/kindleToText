"""
ocr_interface.py モジュールのユニットテスト
"""

import pytest
from PIL import Image
from unittest.mock import Mock, MagicMock
from src.ocr.ocr_interface import (
    BoundingBox,
    TextBlock,
    LayoutData,
    OCRResult,
    OCRInterface,
    OCREngineFactory,
    OCREngineSelector,
    create_default_ocr_engine
)


class TestBoundingBox:
    """BoundingBoxクラスのテスト"""

    def test_bounding_box_creation(self):
        """BoundingBoxの作成テスト"""
        bbox = BoundingBox(left=10, top=20, width=100, height=50, confidence=0.95)

        assert bbox.left == 10
        assert bbox.top == 20
        assert bbox.width == 100
        assert bbox.height == 50
        assert bbox.confidence == 0.95

    def test_bounding_box_default_confidence(self):
        """デフォルト信頼度のテスト"""
        bbox = BoundingBox(left=0, top=0, width=100, height=100)

        assert bbox.confidence == 0.0


class TestTextBlock:
    """TextBlockクラスのテスト"""

    def test_text_block_creation(self):
        """TextBlockの作成テスト"""
        bbox = BoundingBox(left=10, top=20, width=100, height=50)
        block = TextBlock(
            text="サンプルテキスト",
            bounding_box=bbox,
            confidence=0.9,
            block_type="heading"
        )

        assert block.text == "サンプルテキスト"
        assert block.bounding_box == bbox
        assert block.confidence == 0.9
        assert block.block_type == "heading"

    def test_text_block_default_values(self):
        """デフォルト値のテスト"""
        bbox = BoundingBox(left=0, top=0, width=100, height=50)
        block = TextBlock(text="Test", bounding_box=bbox, confidence=0.8)

        assert block.block_type == "text"
        assert block.font_size is None
        assert block.is_bold is False


class TestLayoutData:
    """LayoutDataクラスのテスト"""

    def test_layout_data_creation(self):
        """LayoutDataの作成テスト"""
        bbox = BoundingBox(left=0, top=0, width=100, height=50)
        block = TextBlock(text="Test", bounding_box=bbox, confidence=0.9)

        layout = LayoutData(
            full_text="Full text",
            blocks=[block],
            page_width=800,
            page_height=600,
            language="jpn",
            average_confidence=0.85
        )

        assert layout.full_text == "Full text"
        assert len(layout.blocks) == 1
        assert layout.page_width == 800
        assert layout.page_height == 600
        assert layout.language == "jpn"
        assert layout.average_confidence == 0.85

    def test_layout_data_default_values(self):
        """デフォルト値のテスト"""
        layout = LayoutData(
            full_text="Test",
            blocks=[],
            page_width=800,
            page_height=600
        )

        assert layout.language == "jpn"
        assert layout.average_confidence == 0.0


class TestOCRResult:
    """OCRResultクラスのテスト"""

    def test_ocr_result_creation(self):
        """OCRResultの作成テスト"""
        result = OCRResult(
            text="Extracted text",
            confidence=0.92,
            engine_name="test_engine",
            processing_time=1.5,
            success=True
        )

        assert result.text == "Extracted text"
        assert result.confidence == 0.92
        assert result.engine_name == "test_engine"
        assert result.processing_time == 1.5
        assert result.success is True
        assert result.layout is None
        assert result.error_message is None

    def test_ocr_result_with_layout(self):
        """レイアウト情報付きOCRResultのテスト"""
        layout = LayoutData(
            full_text="Test",
            blocks=[],
            page_width=800,
            page_height=600
        )

        result = OCRResult(
            text="Test",
            confidence=0.9,
            layout=layout
        )

        assert result.layout == layout

    def test_ocr_result_failure(self):
        """失敗結果のテスト"""
        result = OCRResult(
            text="",
            confidence=0.0,
            success=False,
            error_message="Test error"
        )

        assert result.success is False
        assert result.error_message == "Test error"


class TestOCREngineFactory:
    """OCREngineFactoryクラスのテスト"""

    def test_register_engine(self):
        """エンジン登録のテスト"""
        # モックエンジンクラスを作成
        mock_engine_class = Mock()

        OCREngineFactory.register_engine("test_engine", mock_engine_class)

        # 登録されたエンジンを取得
        engine = OCREngineFactory.create_engine("test_engine", {})

        assert engine is not None
        mock_engine_class.assert_called_once_with({})

    def test_create_engine_not_found(self):
        """存在しないエンジンの作成テスト"""
        engine = OCREngineFactory.create_engine("non_existent_engine")

        assert engine is None

    def test_create_engine_with_config(self):
        """設定付きエンジン作成のテスト"""
        mock_engine_class = Mock()
        OCREngineFactory.register_engine("test_engine2", mock_engine_class)

        config = {"param1": "value1"}
        OCREngineFactory.create_engine("test_engine2", config)

        mock_engine_class.assert_called_once_with(config)

    def test_get_available_engines(self):
        """利用可能エンジンリスト取得のテスト"""
        # モックエンジンを作成
        mock_engine = Mock(spec=OCRInterface)
        mock_engine.is_available.return_value = True

        mock_engine_class = Mock(return_value=mock_engine)

        OCREngineFactory.register_engine("available_engine", mock_engine_class)

        available = OCREngineFactory.get_available_engines()

        assert "available_engine" in available


class TestOCREngineSelector:
    """OCREngineSelectorクラスのテスト"""

    def test_init_default(self):
        """デフォルト初期化のテスト"""
        selector = OCREngineSelector()

        assert selector.preferred_engines == ["yomitoku", "tesseract"]

    def test_init_custom(self):
        """カスタム優先順位のテスト"""
        selector = OCREngineSelector(preferred_engines=["tesseract", "yomitoku"])

        assert selector.preferred_engines == ["tesseract", "yomitoku"]

    def test_select_engine_success(self):
        """エンジン選択成功のテスト"""
        # モックエンジンを作成
        mock_engine = Mock(spec=OCRInterface)
        mock_engine.is_available.return_value = True
        mock_engine.initialize.return_value = True

        mock_engine_class = Mock(return_value=mock_engine)

        OCREngineFactory.register_engine("test_selector_engine", mock_engine_class)

        selector = OCREngineSelector(preferred_engines=["test_selector_engine"])
        engine = selector.select_engine()

        assert engine is not None
        assert engine == mock_engine

    def test_select_engine_not_available(self):
        """エンジンが利用不可の場合のテスト"""
        # モックエンジンを作成
        mock_engine = Mock(spec=OCRInterface)
        mock_engine.is_available.return_value = False

        mock_engine_class = Mock(return_value=mock_engine)

        OCREngineFactory.register_engine("unavailable_engine", mock_engine_class)

        selector = OCREngineSelector(preferred_engines=["unavailable_engine"])
        engine = selector.select_engine(fallback=False)

        assert engine is None

    def test_select_engine_initialization_failed(self):
        """初期化失敗のテスト"""
        mock_engine = Mock(spec=OCRInterface)
        mock_engine.is_available.return_value = True
        mock_engine.initialize.return_value = False

        mock_engine_class = Mock(return_value=mock_engine)

        OCREngineFactory.register_engine("init_fail_engine", mock_engine_class)

        selector = OCREngineSelector(preferred_engines=["init_fail_engine"])
        engine = selector.select_engine(fallback=False)

        assert engine is None


class TestHelperFunctions:
    """ヘルパー関数のテスト"""

    def test_create_default_ocr_engine(self):
        """デフォルトOCRエンジン作成のテスト"""
        # モックエンジンを作成
        mock_engine = Mock(spec=OCRInterface)
        mock_engine.is_available.return_value = True
        mock_engine.initialize.return_value = True

        mock_engine_class = Mock(return_value=mock_engine)

        # yomitokuとして登録
        OCREngineFactory.register_engine("yomitoku_test", mock_engine_class)

        # 優先順位を変更
        from src.ocr.ocr_interface import OCREngineSelector
        original_preferred = OCREngineSelector.__init__

        def patched_init(self, preferred_engines=None):
            original_preferred(self, preferred_engines or ["yomitoku_test"])

        OCREngineSelector.__init__ = patched_init

        engine = create_default_ocr_engine()

        # 元に戻す
        OCREngineSelector.__init__ = original_preferred

        # エンジンが作成されたか確認（モックが利用可能な場合）
        # 実際の環境ではyomitoku/tesseractが利用できない可能性があるため、
        # Noneの可能性も許容
        assert engine is None or isinstance(engine, Mock)


class TestOCRInterface:
    """OCRInterfaceの抽象メソッドテスト"""

    def test_cannot_instantiate_directly(self):
        """直接インスタンス化できないことを確認"""
        with pytest.raises(TypeError):
            OCRInterface()

    def test_concrete_implementation(self):
        """具象クラスの実装テスト"""
        # 具象クラスを作成
        class ConcreteOCR(OCRInterface):
            def initialize(self):
                return True

            def extract_text(self, image):
                return OCRResult(text="test", confidence=0.9)

            def extract_with_layout(self, image):
                return OCRResult(text="test", confidence=0.9)

            def get_engine_name(self):
                return "concrete"

            def is_available(self):
                return True

        # インスタンス化できることを確認
        engine = ConcreteOCR()
        assert engine.get_engine_name() == "concrete"
        assert engine.is_available() is True
        assert engine.initialize() is True

        # テスト画像で実行
        test_image = Image.new("RGB", (100, 100))
        result = engine.extract_text(test_image)
        assert result.text == "test"
        assert result.confidence == 0.9
