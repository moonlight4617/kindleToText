"""
window_manager.py モジュールのユニットテスト
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.capture.window_manager import (
    WindowManager,
    WindowInfo,
    Region,
    find_and_activate_kindle
)


class TestWindowInfo:
    """WindowInfoクラスのテスト"""

    def test_window_info_creation(self):
        """WindowInfoの作成テスト"""
        window_info = WindowInfo(
            title="Kindle",
            left=100,
            top=200,
            width=800,
            height=600
        )

        assert window_info.title == "Kindle"
        assert window_info.left == 100
        assert window_info.top == 200
        assert window_info.width == 800
        assert window_info.height == 600
        assert window_info.handle is None

    def test_window_info_with_handle(self):
        """ハンドル付きWindowInfoの作成テスト"""
        mock_handle = Mock()
        window_info = WindowInfo(
            title="Test Window",
            left=0,
            top=0,
            width=1024,
            height=768,
            handle=mock_handle
        )

        assert window_info.handle is mock_handle


class TestRegion:
    """Regionクラスのテスト"""

    def test_region_creation(self):
        """Regionの作成テスト"""
        region = Region(left=50, top=100, width=640, height=480)

        assert region.left == 50
        assert region.top == 100
        assert region.width == 640
        assert region.height == 480


class TestWindowManager:
    """WindowManagerクラスのテスト"""

    def test_init_default(self):
        """デフォルト設定での初期化テスト"""
        manager = WindowManager()
        assert manager.window_title_pattern is None

    def test_init_with_pattern(self):
        """カスタムパターンでの初期化テスト"""
        pattern = "Custom Pattern"
        manager = WindowManager(window_title_pattern=pattern)
        assert manager.window_title_pattern == pattern

    @patch('src.capture.window_manager.gw.getAllWindows')
    def test_find_kindle_window_success(self, mock_get_all_windows):
        """Kindleウィンドウの検出成功テスト"""
        # モックウィンドウを作成
        mock_window = Mock()
        mock_window.title = "Kindle for PC - Book Title"
        mock_window.left = 100
        mock_window.top = 200
        mock_window.width = 800
        mock_window.height = 600

        mock_get_all_windows.return_value = [mock_window]

        manager = WindowManager()
        result = manager.find_kindle_window()

        assert result is not None
        assert result.title == "Kindle for PC - Book Title"
        assert result.left == 100
        assert result.top == 200
        assert result.width == 800
        assert result.height == 600

    @patch('src.capture.window_manager.gw.getAllWindows')
    def test_find_kindle_window_not_found(self, mock_get_all_windows):
        """Kindleウィンドウが見つからない場合のテスト"""
        mock_window = Mock()
        mock_window.title = "Other Application"

        mock_get_all_windows.return_value = [mock_window]

        manager = WindowManager()
        result = manager.find_kindle_window()

        assert result is None

    @patch('src.capture.window_manager.gw.getAllWindows')
    def test_find_kindle_window_with_custom_pattern(self, mock_get_all_windows):
        """カスタムパターンでのウィンドウ検出テスト"""
        mock_window = Mock()
        mock_window.title = "My Custom App"
        mock_window.left = 0
        mock_window.top = 0
        mock_window.width = 1024
        mock_window.height = 768

        mock_get_all_windows.return_value = [mock_window]

        manager = WindowManager(window_title_pattern="Custom App")
        result = manager.find_kindle_window()

        assert result is not None
        assert result.title == "My Custom App"

    @patch('src.capture.window_manager.gw.getAllWindows')
    def test_find_kindle_window_error(self, mock_get_all_windows):
        """ウィンドウ検出エラーのテスト"""
        mock_get_all_windows.side_effect = Exception("Test error")

        manager = WindowManager()

        with pytest.raises(RuntimeError, match="Error while searching for Kindle window"):
            manager.find_kindle_window()

    @patch('src.capture.window_manager.gw.getWindowsWithTitle')
    @patch('src.capture.window_manager.time.sleep')
    def test_activate_window_success(self, mock_sleep, mock_get_windows):
        """ウィンドウアクティブ化成功テスト"""
        # モックウィンドウを作成
        mock_window = Mock()
        mock_window.isMinimized = False
        mock_window.activate = Mock()

        mock_get_windows.return_value = [mock_window]

        window_info = WindowInfo(
            title="Kindle",
            left=100,
            top=200,
            width=800,
            height=600
        )

        manager = WindowManager()
        result = manager.activate_window(window_info)

        assert result is True
        mock_window.activate.assert_called_once()

    @patch('src.capture.window_manager.gw.getWindowsWithTitle')
    @patch('src.capture.window_manager.time.sleep')
    def test_activate_window_from_minimized(self, mock_sleep, mock_get_windows):
        """最小化されたウィンドウのアクティブ化テスト"""
        mock_window = Mock()
        mock_window.isMinimized = True
        mock_window.restore = Mock()
        mock_window.activate = Mock()

        mock_get_windows.return_value = [mock_window]

        window_info = WindowInfo(
            title="Kindle",
            left=100,
            top=200,
            width=800,
            height=600
        )

        manager = WindowManager()
        result = manager.activate_window(window_info)

        assert result is True
        mock_window.restore.assert_called_once()
        mock_window.activate.assert_called_once()

    @patch('src.capture.window_manager.gw.getWindowsWithTitle')
    def test_activate_window_not_found(self, mock_get_windows):
        """ウィンドウが見つからない場合のアクティブ化テスト"""
        mock_get_windows.return_value = []

        window_info = WindowInfo(
            title="Non-existent Window",
            left=0,
            top=0,
            width=800,
            height=600
        )

        manager = WindowManager()
        result = manager.activate_window(window_info)

        assert result is False

    @patch('src.capture.window_manager.gw.getWindowsWithTitle')
    def test_activate_window_error(self, mock_get_windows):
        """ウィンドウアクティブ化エラーのテスト"""
        mock_get_windows.side_effect = Exception("Test error")

        window_info = WindowInfo(
            title="Kindle",
            left=100,
            top=200,
            width=800,
            height=600
        )

        manager = WindowManager()
        result = manager.activate_window(window_info)

        assert result is False

    def test_get_window_region(self):
        """ウィンドウ領域取得テスト"""
        window_info = WindowInfo(
            title="Kindle",
            left=100,
            top=200,
            width=800,
            height=600
        )

        manager = WindowManager()
        region = manager.get_window_region(window_info)

        assert region.left == 100
        assert region.top == 200
        assert region.width == 800
        assert region.height == 600

    @patch('src.capture.window_manager.gw.getAllWindows')
    def test_list_all_windows(self, mock_get_all_windows):
        """全ウィンドウリスト取得テスト"""
        mock_window1 = Mock()
        mock_window1.title = "Window 1"
        mock_window1.left = 0
        mock_window1.top = 0
        mock_window1.width = 800
        mock_window1.height = 600

        mock_window2 = Mock()
        mock_window2.title = "Window 2"
        mock_window2.left = 100
        mock_window2.top = 100
        mock_window2.width = 1024
        mock_window2.height = 768

        mock_window3 = Mock()
        mock_window3.title = ""  # 空のタイトル

        mock_get_all_windows.return_value = [mock_window1, mock_window2, mock_window3]

        manager = WindowManager()
        windows = manager.list_all_windows()

        assert len(windows) == 2  # 空のタイトルは除外される
        assert windows[0].title == "Window 1"
        assert windows[1].title == "Window 2"

    @patch('src.capture.window_manager.gw.getAllWindows')
    def test_list_all_windows_error(self, mock_get_all_windows):
        """ウィンドウリスト取得エラーのテスト"""
        mock_get_all_windows.side_effect = Exception("Test error")

        manager = WindowManager()
        windows = manager.list_all_windows()

        assert windows == []


class TestHelperFunctions:
    """ヘルパー関数のテスト"""

    @patch('src.capture.window_manager.WindowManager.find_kindle_window')
    @patch('src.capture.window_manager.WindowManager.activate_window')
    def test_find_and_activate_kindle_success(
        self,
        mock_activate,
        mock_find
    ):
        """Kindle検出とアクティブ化成功テスト"""
        mock_window_info = WindowInfo(
            title="Kindle",
            left=100,
            top=200,
            width=800,
            height=600
        )

        mock_find.return_value = mock_window_info
        mock_activate.return_value = True

        result = find_and_activate_kindle()

        assert result is not None
        assert result.title == "Kindle"

    @patch('src.capture.window_manager.WindowManager.find_kindle_window')
    def test_find_and_activate_kindle_not_found(self, mock_find):
        """Kindleが見つからない場合のテスト"""
        mock_find.return_value = None

        result = find_and_activate_kindle()

        assert result is None

    @patch('src.capture.window_manager.WindowManager.find_kindle_window')
    @patch('src.capture.window_manager.WindowManager.activate_window')
    def test_find_and_activate_kindle_activation_failed(
        self,
        mock_activate,
        mock_find
    ):
        """アクティブ化失敗のテスト"""
        mock_window_info = WindowInfo(
            title="Kindle",
            left=100,
            top=200,
            width=800,
            height=600
        )

        mock_find.return_value = mock_window_info
        mock_activate.return_value = False

        result = find_and_activate_kindle()

        assert result is None
