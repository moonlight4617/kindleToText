"""
Gemini OCRエンジンのテスト
"""

import os
import pytest
from pathlib import Path
from PIL import Image
from unittest.mock import MagicMock, patch

from src.ocr.gemini_engine import GeminiEngine
from src.ocr.ocr_interface import OCRResult


@pytest.fixture
def sample_image():
    """テスト用のサンプル画像を作成"""
    # 100x100の白い画像を作成
    img = Image.new('RGB', (100, 100), color='white')
    return img


@pytest.fixture
def gemini_config():
    """Gemini設定の作成"""
    return {
        "api_key": "test_api_key_12345",
        "model": "gemini-1.5-flash",
        "temperature": 0.0,
        "max_output_tokens": 8192,
        "prompt_template": "テスト用プロンプト"
    }


class TestGeminiEngineInitialization:
    """GeminiEngineの初期化テスト"""

    def test_init_with_config(self, gemini_config):
        """設定ありで初期化"""
        engine = GeminiEngine(gemini_config)
        assert engine.api_key == "test_api_key_12345"
        assert engine.model_name == "gemini-1.5-flash"
        assert engine.temperature == 0.0
        assert engine.max_output_tokens == 8192
        assert engine.prompt_template == "テスト用プロンプト"

    def test_init_with_nested_config(self):
        """ネストされた設定で初期化"""
        config = {
            "gemini": {
                "api_key": "nested_api_key",
                "model": "gemini-1.5-pro"
            }
        }
        engine = GeminiEngine(config)
        assert engine.api_key == "nested_api_key"
        assert engine.model_name == "gemini-1.5-pro"

    def test_init_with_defaults(self):
        """デフォルト設定で初期化"""
        engine = GeminiEngine({})
        assert engine.api_key is None
        assert engine.model_name == "gemini-1.5-flash"
        assert engine.temperature == 0.0
        assert engine.max_output_tokens == 8192
        assert "書籍のページ" in engine.prompt_template

    def test_get_engine_name(self, gemini_config):
        """エンジン名の取得"""
        engine = GeminiEngine(gemini_config)
        assert engine.get_engine_name() == "gemini"


class TestGeminiEngineAvailability:
    """GeminiEngineの利用可能性チェックテスト"""

    @patch('src.ocr.gemini_engine.logger')
    def test_is_available_with_api_key(self, mock_logger, gemini_config):
        """APIキーがある場合は利用可能"""
        engine = GeminiEngine(gemini_config)

        # google.generativeaiモジュールが存在すると仮定
        with patch.dict('sys.modules', {'google.generativeai': MagicMock()}):
            assert engine.is_available() is True

    @patch('src.ocr.gemini_engine.logger')
    def test_is_available_with_env_var(self, mock_logger):
        """環境変数にAPIキーがある場合は利用可能"""
        engine = GeminiEngine({})

        with patch.dict('sys.modules', {'google.generativeai': MagicMock()}):
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'env_api_key'}):
                assert engine.is_available() is True

    @patch('src.ocr.gemini_engine.logger')
    def test_is_available_without_api_key(self, mock_logger):
        """APIキーがない場合は利用不可"""
        engine = GeminiEngine({})

        with patch.dict('sys.modules', {'google.generativeai': MagicMock()}):
            with patch.dict(os.environ, {}, clear=True):
                assert engine.is_available() is False

    def test_is_available_without_module(self, gemini_config):
        """モジュールがインストールされていない場合"""
        engine = GeminiEngine(gemini_config)

        # ImportErrorをシミュレート
        with patch.dict('sys.modules', {'google.generativeai': None}):
            # モジュールが存在しないことを確認
            assert engine.is_available() is False


class TestGeminiEngineInitialize:
    """GeminiEngineの初期化メソッドテスト"""

    @patch('src.ocr.gemini_engine.logger')
    def test_initialize_without_api_key(self, mock_logger):
        """APIキーなしで初期化失敗"""
        engine = GeminiEngine({})

        # 環境変数からもAPIキーが取得できない状態でテスト
        with patch.dict(os.environ, {}, clear=True):
            # モジュールはインポート可能と仮定
            mock_genai = MagicMock()
            with patch.dict('sys.modules', {'google.generativeai': mock_genai}):
                # 実際のインポートを試みた際にモックを返す
                engine._genai = mock_genai
                result = engine.initialize()

                assert result is False
                assert engine._initialized is False

    @patch('src.ocr.gemini_engine.logger')
    def test_initialize_module_not_found(self, mock_logger, gemini_config):
        """モジュールが見つからない場合"""
        engine = GeminiEngine(gemini_config)

        # ImportErrorをシミュレート
        def raise_import_error(*args, **kwargs):
            raise ImportError("Module not found")

        with patch('builtins.__import__', side_effect=raise_import_error):
            result = engine.initialize()

            assert result is False
            assert engine._initialized is False


class TestGeminiEngineExtractText:
    """GeminiEngineのテキスト抽出テスト"""

    @patch('src.ocr.gemini_engine.logger')
    def test_extract_text_success(self, mock_logger, gemini_config, sample_image):
        """テキスト抽出成功"""
        engine = GeminiEngine(gemini_config)

        # モックのレスポンス
        mock_response = MagicMock()
        mock_response.text = "抽出されたテキスト"

        # モックのモデル
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        engine.model = mock_model
        engine._initialized = True

        result = engine.extract_text(sample_image)

        assert result.success is True
        assert result.text == "抽出されたテキスト"
        assert result.confidence == 0.95
        assert result.engine_name == "gemini"
        assert result.processing_time >= 0  # 処理時間は0以上

    @patch('src.ocr.gemini_engine.logger')
    def test_extract_text_empty_response(self, mock_logger, gemini_config, sample_image):
        """空のレスポンス"""
        engine = GeminiEngine(gemini_config)

        mock_response = MagicMock()
        mock_response.text = "   "  # 空白のみのテキスト

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        engine.model = mock_model
        engine._initialized = True

        result = engine.extract_text(sample_image)

        assert result.success is True
        assert result.text == ""  # stripされて空になる
        assert result.confidence == 0.0

    @patch('src.ocr.gemini_engine.logger')
    def test_extract_text_not_initialized(self, mock_logger, gemini_config, sample_image):
        """初期化されていない状態でテキスト抽出"""
        engine = GeminiEngine(gemini_config)
        engine._initialized = False

        # initializeをモック化して失敗させる
        with patch.object(engine, 'initialize', return_value=False):
            result = engine.extract_text(sample_image)

            assert result.success is False
            assert result.text == ""
            assert result.confidence == 0.0
            assert result.error_message == "Engine not initialized"

    @patch('src.ocr.gemini_engine.logger')
    def test_extract_text_api_error(self, mock_logger, gemini_config, sample_image):
        """API エラー"""
        engine = GeminiEngine(gemini_config)

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")

        engine.model = mock_model
        engine._initialized = True

        result = engine.extract_text(sample_image)

        assert result.success is False
        assert result.text == ""
        assert "API Error" in result.error_message


class TestGeminiEngineExtractWithLayout:
    """GeminiEngineのレイアウト抽出テスト"""

    @patch('src.ocr.gemini_engine.logger')
    def test_extract_with_layout_success(self, mock_logger, gemini_config, sample_image):
        """レイアウト付きテキスト抽出成功"""
        engine = GeminiEngine(gemini_config)

        mock_response = MagicMock()
        mock_response.text = "レイアウト付きテキスト"

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        engine.model = mock_model
        engine._initialized = True

        result = engine.extract_with_layout(sample_image)

        assert result.success is True
        assert result.text == "レイアウト付きテキスト"
        assert result.layout is not None
        assert result.layout.full_text == "レイアウト付きテキスト"
        assert len(result.layout.blocks) == 1
        assert result.layout.page_width == 100
        assert result.layout.page_height == 100


class TestGeminiEngineClose:
    """GeminiEngineのクローズテスト"""

    @patch('src.ocr.gemini_engine.logger')
    def test_close(self, mock_logger, gemini_config):
        """リソースのクローズ"""
        engine = GeminiEngine(gemini_config)
        engine.model = MagicMock()
        engine._initialized = True

        engine.close()

        assert engine.model is None
        assert engine._initialized is False
