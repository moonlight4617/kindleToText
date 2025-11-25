"""
screenshot.py モジュールのユニットテスト
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from PIL import Image
from src.capture.screenshot import ScreenshotCapture, quick_screenshot
from src.capture.window_manager import Region


class TestScreenshotCapture:
    """ScreenshotCaptureクラスのテスト"""

    def test_init_default(self):
        """デフォルト設定での初期化テスト"""
        capture = ScreenshotCapture()

        assert capture.page_turn_key == "right"
        assert capture.page_load_delay == 1.5
        assert capture.screenshot_delay == 0.5

    def test_init_custom(self):
        """カスタム設定での初期化テスト"""
        capture = ScreenshotCapture(
            page_turn_key="space",
            page_load_delay=2.0,
            screenshot_delay=1.0
        )

        assert capture.page_turn_key == "space"
        assert capture.page_load_delay == 2.0
        assert capture.screenshot_delay == 1.0

    @patch('src.capture.screenshot.time.sleep')
    @patch('src.capture.screenshot.mss.mss')
    def test_capture_screen_full_screen(self, mock_mss, mock_sleep):
        """全画面スクリーンショットのテスト"""
        # モックスクリーンショットデータを作成
        mock_screenshot = Mock()
        mock_screenshot.size = (1920, 1080)
        mock_screenshot.bgra = b'\x00' * (1920 * 1080 * 4)

        mock_sct = MagicMock()
        mock_sct.monitors = [None, {"left": 0, "top": 0, "width": 1920, "height": 1080}]
        mock_sct.grab.return_value = mock_screenshot
        mock_mss.return_value.__enter__.return_value = mock_sct

        capture = ScreenshotCapture()
        image = capture.capture_screen()

        assert image is not None
        assert isinstance(image, Image.Image)
        mock_sleep.assert_called_once_with(0.5)  # screenshot_delay

    @patch('src.capture.screenshot.time.sleep')
    @patch('src.capture.screenshot.mss.mss')
    def test_capture_screen_region(self, mock_mss, mock_sleep):
        """領域指定スクリーンショットのテスト"""
        region = Region(left=100, top=200, width=800, height=600)

        mock_screenshot = Mock()
        mock_screenshot.size = (800, 600)
        mock_screenshot.bgra = b'\x00' * (800 * 600 * 4)

        mock_sct = MagicMock()
        mock_sct.grab.return_value = mock_screenshot
        mock_mss.return_value.__enter__.return_value = mock_sct

        capture = ScreenshotCapture()
        image = capture.capture_screen(region)

        assert image is not None
        assert isinstance(image, Image.Image)

        # 正しい領域パラメータで呼び出されたか確認
        call_args = mock_sct.grab.call_args[0][0]
        assert call_args["left"] == 100
        assert call_args["top"] == 200
        assert call_args["width"] == 800
        assert call_args["height"] == 600

    @patch('src.capture.screenshot.time.sleep')
    @patch('src.capture.screenshot.mss.mss')
    def test_capture_screen_no_delay(self, mock_mss, mock_sleep):
        """遅延なしのスクリーンショットテスト"""
        mock_screenshot = Mock()
        mock_screenshot.size = (1920, 1080)
        mock_screenshot.bgra = b'\x00' * (1920 * 1080 * 4)

        mock_sct = MagicMock()
        mock_sct.monitors = [None, {"left": 0, "top": 0, "width": 1920, "height": 1080}]
        mock_sct.grab.return_value = mock_screenshot
        mock_mss.return_value.__enter__.return_value = mock_sct

        capture = ScreenshotCapture(screenshot_delay=0)
        image = capture.capture_screen()

        assert image is not None
        mock_sleep.assert_not_called()

    @patch('src.capture.screenshot.mss.mss')
    def test_capture_screen_error(self, mock_mss):
        """スクリーンショットエラーのテスト"""
        mock_mss.side_effect = Exception("Test error")

        capture = ScreenshotCapture()

        with pytest.raises(RuntimeError, match="Error while capturing screenshot"):
            capture.capture_screen()

    def test_save_screenshot_png(self, tmp_path):
        """PNG形式での保存テスト"""
        # テスト画像を作成
        test_image = Image.new("RGB", (100, 100), color="red")
        file_path = tmp_path / "test_screenshot.png"

        capture = ScreenshotCapture()
        result = capture.save_screenshot(test_image, file_path)

        assert result is True
        assert file_path.exists()

        # 保存された画像を読み込んで確認
        saved_image = Image.open(file_path)
        assert saved_image.size == (100, 100)

    def test_save_screenshot_jpeg(self, tmp_path):
        """JPEG形式での保存テスト"""
        test_image = Image.new("RGB", (100, 100), color="blue")
        file_path = tmp_path / "test_screenshot.jpg"

        capture = ScreenshotCapture()
        result = capture.save_screenshot(test_image, file_path, quality=90)

        assert result is True
        assert file_path.exists()

        saved_image = Image.open(file_path)
        assert saved_image.size == (100, 100)

    def test_save_screenshot_creates_directory(self, tmp_path):
        """ディレクトリ自動作成のテスト"""
        test_image = Image.new("RGB", (100, 100), color="green")
        nested_dir = tmp_path / "nested" / "dir"
        file_path = nested_dir / "test.png"

        capture = ScreenshotCapture()
        result = capture.save_screenshot(test_image, file_path)

        assert result is True
        assert file_path.exists()
        assert nested_dir.exists()

    def test_save_screenshot_rgba_to_jpeg(self, tmp_path):
        """RGBA画像をJPEGで保存するテスト"""
        test_image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        file_path = tmp_path / "test.jpg"

        capture = ScreenshotCapture()
        result = capture.save_screenshot(test_image, file_path)

        assert result is True
        assert file_path.exists()

    @patch('src.capture.screenshot.pyautogui.press')
    def test_turn_page_forward(self, mock_press):
        """ページ送り（前方）のテスト"""
        capture = ScreenshotCapture(page_turn_key="right")
        result = capture.turn_page("forward")

        assert result is True
        mock_press.assert_called_once_with("right")

    @patch('src.capture.screenshot.pyautogui.press')
    def test_turn_page_backward(self, mock_press):
        """ページ送り（後方）のテスト"""
        capture = ScreenshotCapture(page_turn_key="right")
        result = capture.turn_page("backward")

        assert result is True
        mock_press.assert_called_once_with("left")

    @patch('src.capture.screenshot.pyautogui.press')
    def test_turn_page_invalid_direction(self, mock_press):
        """無効な方向のテスト"""
        capture = ScreenshotCapture()
        result = capture.turn_page("invalid")

        assert result is False
        mock_press.assert_not_called()

    @patch('src.capture.screenshot.pyautogui.press')
    def test_turn_page_error(self, mock_press):
        """ページ送りエラーのテスト"""
        mock_press.side_effect = Exception("Test error")

        capture = ScreenshotCapture()
        result = capture.turn_page("forward")

        assert result is False

    @patch('src.capture.screenshot.time.sleep')
    def test_wait_for_page_load_default(self, mock_sleep):
        """デフォルト待機時間のテスト"""
        capture = ScreenshotCapture(page_load_delay=2.0)
        capture.wait_for_page_load()

        mock_sleep.assert_called_once_with(2.0)

    @patch('src.capture.screenshot.time.sleep')
    def test_wait_for_page_load_custom(self, mock_sleep):
        """カスタム待機時間のテスト"""
        capture = ScreenshotCapture(page_load_delay=2.0)
        capture.wait_for_page_load(custom_delay=3.5)

        mock_sleep.assert_called_once_with(3.5)

    @patch('src.capture.screenshot.ScreenshotCapture.capture_screen')
    @patch('src.capture.screenshot.ScreenshotCapture.save_screenshot')
    def test_capture_and_save_success(self, mock_save, mock_capture):
        """capture_and_save成功のテスト"""
        mock_image = Mock(spec=Image.Image)
        mock_capture.return_value = mock_image
        mock_save.return_value = True

        region = Region(left=0, top=0, width=800, height=600)
        capture = ScreenshotCapture()
        result = capture.capture_and_save(region, "test.png")

        assert result is True
        mock_capture.assert_called_once_with(region)
        mock_save.assert_called_once()

    @patch('src.capture.screenshot.ScreenshotCapture.capture_screen')
    def test_capture_and_save_capture_failed(self, mock_capture):
        """capture_and_saveでキャプチャ失敗のテスト"""
        mock_capture.return_value = None

        capture = ScreenshotCapture()
        result = capture.capture_and_save(None, "test.png")

        assert result is False

    @patch('src.capture.screenshot.ScreenshotCapture.capture_and_save')
    @patch('src.capture.screenshot.ScreenshotCapture.turn_page')
    @patch('src.capture.screenshot.ScreenshotCapture.wait_for_page_load')
    def test_capture_page_sequence_success(
        self,
        mock_wait,
        mock_turn,
        mock_capture_save,
        tmp_path
    ):
        """ページシーケンスキャプチャ成功のテスト"""
        mock_capture_save.return_value = True
        mock_turn.return_value = True

        region = Region(left=0, top=0, width=800, height=600)
        capture = ScreenshotCapture()

        result = capture.capture_page_sequence(
            region=region,
            output_dir=tmp_path,
            start_page=1,
            end_page=3,
            filename_template="page_{:04d}.png"
        )

        assert result["success_count"] == 3
        assert result["failed_pages"] == []
        assert result["total_pages"] == 3
        assert mock_capture_save.call_count == 3
        assert mock_turn.call_count == 2  # 最後のページではページ送りしない

    @patch('src.capture.screenshot.ScreenshotCapture.capture_and_save')
    @patch('src.capture.screenshot.ScreenshotCapture.turn_page')
    @patch('src.capture.screenshot.ScreenshotCapture.wait_for_page_load')
    def test_capture_page_sequence_partial_failure(
        self,
        mock_wait,
        mock_turn,
        mock_capture_save,
        tmp_path
    ):
        """ページシーケンスキャプチャ部分失敗のテスト"""
        # 2ページ目のキャプチャが失敗する
        mock_capture_save.side_effect = [True, False, True]
        mock_turn.return_value = True

        region = Region(left=0, top=0, width=800, height=600)
        capture = ScreenshotCapture()

        result = capture.capture_page_sequence(
            region=region,
            output_dir=tmp_path,
            start_page=1,
            end_page=3
        )

        assert result["success_count"] == 2
        assert result["failed_pages"] == [2]
        assert result["total_pages"] == 3

    @patch('src.capture.screenshot.ScreenshotCapture.capture_and_save')
    def test_capture_page_sequence_creates_directory(
        self,
        mock_capture_save,
        tmp_path
    ):
        """ページシーケンスキャプチャでのディレクトリ作成テスト"""
        mock_capture_save.return_value = True

        output_dir = tmp_path / "screenshots"
        region = Region(left=0, top=0, width=800, height=600)
        capture = ScreenshotCapture()

        capture.capture_page_sequence(
            region=region,
            output_dir=output_dir,
            start_page=1,
            end_page=1
        )

        assert output_dir.exists()


class TestHelperFunctions:
    """ヘルパー関数のテスト"""

    @patch('src.capture.screenshot.ScreenshotCapture.capture_and_save')
    def test_quick_screenshot_success(self, mock_capture_and_save):
        """quick_screenshot成功のテスト"""
        mock_capture_and_save.return_value = True

        result = quick_screenshot(output_path="test.png")

        assert result is True
        mock_capture_and_save.assert_called_once()

    @patch('src.capture.screenshot.ScreenshotCapture.capture_and_save')
    def test_quick_screenshot_with_region(self, mock_capture_and_save):
        """領域指定quick_screenshotのテスト"""
        mock_capture_and_save.return_value = True
        region = Region(left=100, top=200, width=800, height=600)

        result = quick_screenshot(region=region, output_path="test.png")

        assert result is True
        call_args = mock_capture_and_save.call_args[0]
        assert call_args[0] == region
