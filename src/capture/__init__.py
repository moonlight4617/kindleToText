"""
Screenshot capture module

このモジュールは、Kindle for PCのウィンドウ管理とスクリーンショット撮影機能を提供します。
"""

from .window_manager import WindowManager, WindowInfo, Region, find_and_activate_kindle
from .screenshot import ScreenshotCapture, quick_screenshot

__all__ = [
    "WindowManager",
    "WindowInfo",
    "Region",
    "ScreenshotCapture",
    "find_and_activate_kindle",
    "quick_screenshot",
]
