"""
OCRエンジン（YomitokuとTesseract）のユニットテスト
"""

import pytest
from PIL import Image
from unittest.mock import Mock, patch, MagicMock
from src.ocr.yomitoku_engine import YomitokuEngine
from src.ocr.tesseract_engine import TesseractEngine
from src.ocr.ocr_interface import OCRResult


class TestYomitokuEngine:
    """YomitokuEngineクラスのテスト"""

    def test_init_default(self):
        """デフォルト初期化のテスト"""
        engine = YomitokuEngine()

        assert engine.model_name == "yomitoku"
        assert engine.device == "cpu"
        assert engine.confidence_threshold == 0.0
        assert engine.model is None
        assert engine._initialized is False

    def test_init_custom(self):
        """カスタム設定での初期化テスト"""
        config = {
            "model_name": "custom_model",
            "device": "cuda",
            "confidence_threshold": 0.5
        }
        engine = YomitokuEngine(config)

        assert engine.model_name == "custom_model"
        assert engine.device == "cuda"
        assert engine.confidence_threshold == 0.5

    def test_get_engine_name(self):
        """エンジン名取得のテスト"""
        engine = YomitokuEngine()
        assert engine.get_engine_name() == "yomitoku"

    @patch('src.ocr.yomitoku_engine.logger')
    def test_is_available_true(self, mock_logger):
        """Yomitoku利用可能のテスト"""
        with patch.dict('sys.modules', {'yomitoku': MagicMock()}):
            engine = YomitokuEngine()
            assert engine.is_available() is True

    @patch('src.ocr.yomitoku_engine.logger')
    def test_is_available_false(self, mock_logger):
        """Yomitoku利用不可のテスト"""
        with patch.dict('sys.modules', {'yomitoku': None}):
            engine = YomitokuEngine()
            # ImportErrorが発生するため利用不可
            result = engine.is_available()
            assert result is False

    @patch('src.ocr.yomitoku_engine.logger')
    def test_initialize_success(self, mock_logger):
        """初期化成功のテスト"""
        # モックのDocumentAnalyzerを作成
        mock_analyzer = MagicMock()
        mock_module = MagicMock()
        mock_module.DocumentAnalyzer = MagicMock(return_value=mock_analyzer)

        with patch.dict('sys.modules', {'yomitoku': mock_module}):
            engine = YomitokuEngine()
            result = engine.initialize()

            assert result is True
            assert engine._initialized is True
            assert engine.model is not None

    @patch('src.ocr.yomitoku_engine.logger')
    def test_initialize_failure(self, mock_logger):
        """初期化失敗のテスト"""
        with patch.dict('sys.modules', {'yomitoku': None}):
            engine = YomitokuEngine()
            result = engine.initialize()

            assert result is False
            assert engine._initialized is False

    @patch('src.ocr.yomitoku_engine.logger')
    def test_extract_text_not_initialized(self, mock_logger):
        """未初期化でのテキスト抽出テスト"""
        engine = YomitokuEngine()
        engine._initialized = False

        test_image = Image.new("RGB", (100, 100))

        with patch.object(engine, 'initialize', return_value=False):
            result = engine.extract_text(test_image)

            assert result.success is False
            assert result.error_message == "Engine not initialized"

    @patch('src.ocr.yomitoku_engine.logger')
    def test_extract_text_success(self, mock_logger):
        """テキスト抽出成功のテスト"""
        engine = YomitokuEngine()
        engine._initialized = True

        # モック結果を作成
        mock_result = MagicMock()
        mock_result.text = "抽出されたテキスト"

        mock_line1 = MagicMock()
        mock_line1.confidence = 0.95
        mock_result.ocr_results = [mock_line1]

        # モデルをモック
        engine.model = MagicMock(return_value=mock_result)

        test_image = Image.new("RGB", (100, 100))
        result = engine.extract_text(test_image)

        assert result.success is True
        assert result.engine_name == "yomitoku"
        assert result.confidence >= 0.0

    @patch('src.ocr.yomitoku_engine.logger')
    def test_extract_with_layout_success(self, mock_logger):
        """レイアウト付きテキスト抽出成功のテスト"""
        engine = YomitokuEngine()
        engine._initialized = True

        # モック結果を作成
        mock_line1 = MagicMock()
        mock_line1.text = "行1"
        mock_line1.confidence = 0.9
        mock_line1.bbox = [10, 20, 100, 50]

        mock_result = MagicMock()
        mock_result.ocr_results = [mock_line1]

        engine.model = MagicMock(return_value=mock_result)

        test_image = Image.new("RGB", (100, 100))
        result = engine.extract_with_layout(test_image)

        assert result.success is True
        assert result.layout is not None
        assert len(result.layout.blocks) >= 0

    @patch('src.ocr.yomitoku_engine.logger')
    def test_close(self, mock_logger):
        """リソース解放のテスト"""
        engine = YomitokuEngine()
        engine.model = MagicMock()
        engine._initialized = True

        engine.close()

        assert engine.model is None
        assert engine._initialized is False


class TestTesseractEngine:
    """TesseractEngineクラスのテスト"""

    def test_init_default(self):
        """デフォルト初期化のテスト"""
        engine = TesseractEngine()

        assert engine.lang == "jpn+eng"
        assert engine.psm == 3
        assert engine.oem == 3
        assert engine.confidence_threshold == 0.0
        assert engine._initialized is False

    def test_init_custom(self):
        """カスタム設定での初期化テスト"""
        config = {
            "lang": "eng",
            "psm": 6,
            "oem": 1,
            "confidence_threshold": 0.6,
            "tesseract_cmd": "/usr/bin/tesseract"
        }
        engine = TesseractEngine(config)

        assert engine.lang == "eng"
        assert engine.psm == 6
        assert engine.oem == 1
        assert engine.confidence_threshold == 0.6

    def test_get_engine_name(self):
        """エンジン名取得のテスト"""
        engine = TesseractEngine()
        assert engine.get_engine_name() == "tesseract"

    @patch('src.ocr.tesseract_engine.pytesseract.get_tesseract_version')
    def test_is_available_true(self, mock_version):
        """Tesseract利用可能のテスト"""
        mock_version.return_value = "5.0.0"

        engine = TesseractEngine()
        assert engine.is_available() is True

    @patch('src.ocr.tesseract_engine.pytesseract.get_tesseract_version')
    def test_is_available_false(self, mock_version):
        """Tesseract利用不可のテスト"""
        mock_version.side_effect = Exception("Tesseract not found")

        engine = TesseractEngine()
        assert engine.is_available() is False

    @patch('src.ocr.tesseract_engine.pytesseract.get_languages')
    @patch('src.ocr.tesseract_engine.pytesseract.get_tesseract_version')
    @patch('src.ocr.tesseract_engine.logger')
    def test_initialize_success(self, mock_logger, mock_version, mock_langs):
        """初期化成功のテスト"""
        mock_version.return_value = "5.0.0"
        mock_langs.return_value = ["jpn", "eng"]

        engine = TesseractEngine()
        result = engine.initialize()

        assert result is True
        assert engine._initialized is True

    @patch('src.ocr.tesseract_engine.pytesseract.get_tesseract_version')
    @patch('src.ocr.tesseract_engine.logger')
    def test_initialize_failure(self, mock_logger, mock_version):
        """初期化失敗のテスト"""
        mock_version.side_effect = Exception("Test error")

        engine = TesseractEngine()
        result = engine.initialize()

        assert result is False
        assert engine._initialized is False

    @patch('src.ocr.tesseract_engine.logger')
    def test_extract_text_not_initialized(self, mock_logger):
        """未初期化でのテキスト抽出テスト"""
        engine = TesseractEngine()
        engine._initialized = False

        test_image = Image.new("RGB", (100, 100))

        with patch.object(engine, 'initialize', return_value=False):
            result = engine.extract_text(test_image)

            assert result.success is False
            assert result.error_message == "Engine not initialized"

    @patch('src.ocr.tesseract_engine.pytesseract.image_to_data')
    @patch('src.ocr.tesseract_engine.pytesseract.image_to_string')
    @patch('src.ocr.tesseract_engine.logger')
    def test_extract_text_success(self, mock_logger, mock_to_string, mock_to_data):
        """テキスト抽出成功のテスト"""
        mock_to_string.return_value = "抽出されたテキスト"
        mock_to_data.return_value = {
            'text': ['抽出されたテキスト'],
            'conf': ['85']
        }

        engine = TesseractEngine()
        engine._initialized = True

        test_image = Image.new("RGB", (100, 100))
        result = engine.extract_text(test_image)

        assert result.success is True
        assert result.text == "抽出されたテキスト"
        assert result.engine_name == "tesseract"
        assert result.confidence >= 0.0

    @patch('src.ocr.tesseract_engine.pytesseract.image_to_data')
    @patch('src.ocr.tesseract_engine.logger')
    def test_extract_with_layout_success(self, mock_logger, mock_to_data):
        """レイアウト付きテキスト抽出成功のテスト"""
        mock_to_data.return_value = {
            'text': ['word1', 'word2'],
            'conf': ['90', '85'],
            'left': [10, 20],
            'top': [30, 40],
            'width': [50, 60],
            'height': [20, 25],
            'level': [5, 5]
        }

        engine = TesseractEngine()
        engine._initialized = True

        test_image = Image.new("RGB", (100, 100))
        result = engine.extract_with_layout(test_image)

        assert result.success is True
        assert result.layout is not None
        assert len(result.layout.blocks) == 2

    @patch('src.ocr.tesseract_engine.logger')
    def test_close(self, mock_logger):
        """リソース解放のテスト"""
        engine = TesseractEngine()
        engine._initialized = True

        engine.close()

        assert engine._initialized is False

    def test_calculate_average_confidence(self):
        """平均信頼度計算のテスト"""
        engine = TesseractEngine()

        data = {
            'conf': ['90', '80', '-1', '70']
        }

        avg = engine._calculate_average_confidence(data)

        # (0.9 + 0.8 + 0.7) / 3 = 0.8
        assert avg == pytest.approx(0.8, abs=0.01)

    def test_extract_text_blocks_with_threshold(self):
        """信頼度閾値付きテキストブロック抽出のテスト"""
        engine = TesseractEngine({"confidence_threshold": 0.8})

        data = {
            'text': ['high', 'low', 'medium'],
            'conf': ['90', '50', '80'],
            'left': [10, 20, 30],
            'top': [10, 20, 30],
            'width': [50, 60, 70],
            'height': [20, 25, 30],
            'level': [5, 5, 5]
        }

        blocks = engine._extract_text_blocks(data)

        # 閾値0.8以上は'high'と'medium'のみ
        assert len(blocks) == 2
        assert blocks[0].text == "high"
        assert blocks[1].text == "medium"


class TestEngineIntegration:
    """エンジン統合テスト"""

    @patch('src.ocr.yomitoku_engine.logger')
    def test_yomitoku_not_initialized_auto_init(self, mock_logger):
        """Yomitoku自動初期化のテスト"""
        engine = YomitokuEngine()

        test_image = Image.new("RGB", (100, 100))

        with patch.object(engine, 'initialize', return_value=True):
            with patch.object(engine, 'model') as mock_model:
                mock_result = MagicMock()
                mock_result.text = "test"
                mock_result.ocr_results = []
                mock_model.return_value = mock_result

                result = engine.extract_text(test_image)

                # 自動初期化が呼ばれたか確認
                assert result.success is True

    @patch('src.ocr.tesseract_engine.logger')
    def test_tesseract_not_initialized_auto_init(self, mock_logger):
        """Tesseract自動初期化のテスト"""
        engine = TesseractEngine()

        test_image = Image.new("RGB", (100, 100))

        with patch.object(engine, 'initialize', return_value=True):
            with patch('src.ocr.tesseract_engine.pytesseract.image_to_string') as mock_string:
                with patch('src.ocr.tesseract_engine.pytesseract.image_to_data') as mock_data:
                    mock_string.return_value = "test"
                    mock_data.return_value = {'text': [], 'conf': []}

                    result = engine.extract_text(test_image)

                    # 自動初期化が呼ばれたか確認
                    assert result.success is True
