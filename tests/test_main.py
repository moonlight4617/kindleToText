"""
main.py のユニットテスト
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner
from PIL import Image

from main import KindleOCRWorkflow, main
from src.ocr.ocr_interface import OCRResult


class TestKindleOCRWorkflow:
    """KindleOCRWorkflow クラスのテスト"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_config(self, temp_dir):
        """モック設定を作成"""
        return {
            "kindle": {
                "window_title": "Kindle",
                "page_turn_key": "Right",
                "page_turn_delay": 0.1,
                "window_activation_delay": 0.1,
            },
            "output": {"base_dir": temp_dir, "encoding": "utf-8"},
            "preprocessing": {
                "noise_reduction": {"enabled": False},
                "contrast": {"enabled": False},
                "skew_correction": {"enabled": False},
                "margin_trim": {"enabled": False},
                "binarization": {"enabled": False},
            },
            "ocr": {
                "primary_engine": "tesseract",
                "fallback_engine": "tesseract",
                "tesseract": {"lang": "jpn", "config": "--psm 6"},
            },
            "state": {
                "enabled": True,
                "save_interval": 5,
                "auto_save_on_error": True,
                "state_dir": f"{temp_dir}/state",
                "cleanup_on_completion": False,
            },
            "progress": {
                "show_progress_bar": False,
                "show_current_page": True,
                "show_percentage": True,
                "show_eta": True,
            },
            "error_handling": {
                "abort_on_window_not_found": True,
                "max_consecutive_failures": 3,
            },
            "logging": {
                "level": "INFO",
                "console": True,
                "file": False,
                "format": "{message}",
            },
        }

    @pytest.fixture
    def workflow(self, mock_config):
        """KindleOCRWorkflow インスタンスを作成"""
        return KindleOCRWorkflow(mock_config)

    def test_init(self, workflow, mock_config):
        """初期化テスト"""
        assert workflow.config == mock_config
        assert workflow.state_manager is not None
        assert workflow.window_manager is None
        assert workflow.screenshot_capture is None

    @patch("main.WindowManager")
    @patch("main.ScreenshotCapture")
    @patch("main.ImageProcessor")
    @patch("main.OCREngineFactory")
    @patch("main.TextWriter")
    def test_initialize(
        self,
        mock_text_writer,
        mock_ocr_factory,
        mock_image_processor,
        mock_screenshot,
        mock_window_manager,
        workflow,
    ):
        """初期化処理のテスト"""
        # モックの設定
        mock_window_manager.return_value = Mock()
        mock_screenshot.return_value = Mock()
        mock_image_processor.return_value = Mock()
        mock_ocr_instance = Mock()
        mock_ocr_instance.initialize.return_value = True
        mock_ocr_factory.create_engine.return_value = mock_ocr_instance
        mock_text_writer.return_value = Mock()

        # 初期化実行
        result = workflow.initialize("Test Book", total_pages=10, start_page=1)

        # 検証
        assert result is True
        assert workflow.window_manager is not None
        assert workflow.screenshot_capture is not None
        assert workflow.image_processor is not None
        assert workflow.ocr_engine is not None
        assert workflow.text_writer is not None
        assert workflow.progress_tracker is not None
        assert workflow.state is not None
        assert workflow.state.book_title == "Test Book"
        assert workflow.state.total_pages == 10

    @patch("main.WindowManager")
    @patch("main.ScreenshotCapture")
    @patch("main.ImageProcessor")
    @patch("main.OCREngineFactory")
    @patch("main.TextWriter")
    def test_resume_from_state(
        self,
        mock_text_writer,
        mock_ocr_factory,
        mock_image_processor,
        mock_screenshot,
        mock_window_manager,
        workflow,
    ):
        """状態からの再開テスト"""
        # モックの設定
        mock_window_manager.return_value = Mock()
        mock_screenshot.return_value = Mock()
        mock_image_processor.return_value = Mock()
        mock_ocr_instance = Mock()
        mock_ocr_instance.initialize.return_value = True
        mock_ocr_factory.create_engine.return_value = mock_ocr_instance
        mock_text_writer.return_value = Mock()

        # まず初期化して状態を保存
        workflow.initialize("Test Book", total_pages=10, start_page=1)
        workflow.state.current_page = 5
        workflow.state.processed_pages = [1, 2, 3, 4, 5]
        workflow.save_state()

        # 新しいワークフローインスタンスで再開
        new_workflow = KindleOCRWorkflow(workflow.config)
        result = new_workflow.resume_from_state("Test Book")

        # 検証
        assert result is True
        assert new_workflow.state is not None
        assert new_workflow.state.book_title == "Test Book"
        assert new_workflow.state.current_page == 5
        assert len(new_workflow.state.processed_pages) == 5

    def test_resume_from_state_not_found(self, workflow):
        """存在しない状態からの再開テスト"""
        result = workflow.resume_from_state("Non Existent Book")
        assert result is False

    @patch("main.WindowManager")
    @patch("main.ScreenshotCapture")
    @patch("main.ImageProcessor")
    @patch("main.OCREngineFactory")
    @patch("main.TextWriter")
    def test_process_page_success(
        self,
        mock_text_writer,
        mock_ocr_factory,
        mock_image_processor,
        mock_screenshot,
        mock_window_manager,
        workflow,
    ):
        """ページ処理成功のテスト"""
        # モックの設定
        mock_window = Mock()
        mock_window_manager_instance = Mock()
        mock_window_manager_instance.find_kindle_window.return_value = mock_window
        mock_window_manager_instance.get_window_region.return_value = (0, 0, 800, 600)
        mock_window_manager.return_value = mock_window_manager_instance

        # テスト用画像を作成
        test_image = Image.new("RGB", (800, 600), color="white")
        mock_screenshot_instance = Mock()
        mock_screenshot_instance.capture_screen.return_value = test_image
        mock_screenshot_instance.save_screenshot.return_value = True
        mock_screenshot.return_value = mock_screenshot_instance

        mock_image_processor_instance = Mock()
        mock_image_processor_instance.optimize_for_ocr.return_value = test_image
        mock_image_processor.return_value = mock_image_processor_instance

        mock_ocr_instance = Mock()
        mock_ocr_instance.initialize.return_value = True
        mock_ocr_instance.extract_text.return_value = OCRResult(
            text="Test text from page",
            confidence=0.9,
            success=True,
            engine_name="tesseract"
        )
        mock_ocr_factory.create_engine.return_value = mock_ocr_instance

        mock_text_writer_instance = Mock()
        mock_text_writer.return_value = mock_text_writer_instance

        # 初期化
        workflow.initialize("Test Book", total_pages=10, start_page=1)

        # ページ処理
        result = workflow.process_page(1)

        # 検証
        assert result is True
        mock_window_manager_instance.find_kindle_window.assert_called_once()
        mock_screenshot_instance.capture_screen.assert_called_once()
        mock_ocr_instance.extract_text.assert_called_once()
        mock_text_writer_instance.append_text.assert_called()

    @patch("main.WindowManager")
    @patch("main.ScreenshotCapture")
    @patch("main.ImageProcessor")
    @patch("main.OCREngineFactory")
    @patch("main.TextWriter")
    def test_process_page_window_not_found(
        self,
        mock_text_writer,
        mock_ocr_factory,
        mock_image_processor,
        mock_screenshot,
        mock_window_manager,
        workflow,
    ):
        """ウィンドウが見つからない場合のテスト"""
        # モックの設定
        mock_window_manager_instance = Mock()
        mock_window_manager_instance.find_kindle_window.return_value = None
        mock_window_manager.return_value = mock_window_manager_instance

        mock_screenshot.return_value = Mock()
        mock_image_processor.return_value = Mock()
        mock_ocr_instance = Mock()
        mock_ocr_instance.initialize.return_value = True
        mock_ocr_factory.create_engine.return_value = mock_ocr_instance
        mock_text_writer.return_value = Mock()

        # 初期化
        workflow.initialize("Test Book", total_pages=10, start_page=1)

        # ページ処理
        result = workflow.process_page(1)

        # 検証
        assert result is False

    def test_save_state(self, workflow):
        """状態保存のテスト"""
        # 初期化
        workflow.initialize("Test Book", total_pages=10, start_page=1)

        # 状態保存
        workflow.save_state()

        # 状態が保存されていることを確認
        loaded_state = workflow.state_manager.load_state("Test Book")
        assert loaded_state is not None
        assert loaded_state.book_title == "Test Book"


class TestMainCLI:
    """main() CLI関数のテスト"""

    @pytest.fixture
    def runner(self):
        """ClickのCliRunnerを作成"""
        return CliRunner()

    @pytest.fixture
    def temp_config_file(self):
        """一時設定ファイルを作成"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(
                """
kindle:
  window_title: "Kindle"
  page_turn_key: "Right"
  page_turn_delay: 0.1
  window_activation_delay: 0.1
output:
  base_dir: "output"
  encoding: "utf-8"
preprocessing:
  noise_reduction:
    enabled: false
  contrast:
    enabled: false
  skew_correction:
    enabled: false
  margin_trim:
    enabled: false
  binarization:
    enabled: false
ocr:
  primary_engine: "tesseract"
  tesseract:
    lang: "jpn"
    config: "--psm 6"
state:
  enabled: true
  save_interval: 5
  state_dir: "output/state"
  cleanup_on_completion: false
progress:
  show_progress_bar: false
error_handling:
  max_consecutive_failures: 3
logging:
  level: "INFO"
  console: true
  file: false
  format: "{message}"
"""
            )
            yield Path(f.name)
            Path(f.name).unlink()

    def test_main_missing_title(self, runner):
        """タイトル未指定のテスト"""
        result = runner.invoke(main, [])
        assert result.exit_code != 0
        assert "title" in result.output.lower() or "missing" in result.output.lower()

    def test_main_missing_total_pages(self, runner, temp_config_file):
        """総ページ数未指定のテスト"""
        result = runner.invoke(
            main, ["--title", "Test Book", "--config", str(temp_config_file)]
        )
        assert result.exit_code != 0

    @patch("main.KindleOCRWorkflow")
    def test_main_with_valid_args(self, mock_workflow_class, runner, temp_config_file):
        """正常な引数でのテスト"""
        # モックの設定
        mock_workflow = Mock()
        mock_workflow.initialize.return_value = True
        mock_workflow.run.return_value = True
        mock_workflow_class.return_value = mock_workflow

        # 実行
        result = runner.invoke(
            main,
            [
                "--title",
                "Test Book",
                "--total-pages",
                "10",
                "--config",
                str(temp_config_file),
            ],
        )

        # 検証
        assert result.exit_code == 0
        mock_workflow.initialize.assert_called_once()
        mock_workflow.run.assert_called_once()

    @patch("main.KindleOCRWorkflow")
    def test_main_with_resume(self, mock_workflow_class, runner, temp_config_file):
        """再開モードのテスト"""
        # モックの設定
        mock_workflow = Mock()
        mock_workflow.resume_from_state.return_value = True
        mock_workflow.run.return_value = True
        mock_workflow_class.return_value = mock_workflow

        # 実行
        result = runner.invoke(
            main,
            ["--title", "Test Book", "--resume", "--config", str(temp_config_file)],
        )

        # 検証
        assert result.exit_code == 0
        mock_workflow.resume_from_state.assert_called_once()
        mock_workflow.run.assert_called_once()

    @patch("main.KindleOCRWorkflow")
    def test_main_with_debug(self, mock_workflow_class, runner, temp_config_file):
        """デバッグモードのテスト"""
        # モックの設定
        mock_workflow = Mock()
        mock_workflow.initialize.return_value = True
        mock_workflow.run.return_value = True
        mock_workflow_class.return_value = mock_workflow

        # 実行
        result = runner.invoke(
            main,
            [
                "--title",
                "Test Book",
                "--total-pages",
                "10",
                "--debug",
                "--config",
                str(temp_config_file),
            ],
        )

        # 検証（デバッグモードでも正常終了することを確認）
        assert result.exit_code == 0
