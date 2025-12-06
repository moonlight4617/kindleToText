"""
Kindle for PC ウィンドウ管理モジュール

このモジュールは、Kindle for PCアプリケーションのウィンドウを検出し、
アクティブ化し、ウィンドウ情報を取得する機能を提供します。
"""

from dataclasses import dataclass
from typing import Optional, List
import time
import pygetwindow as gw
from loguru import logger


@dataclass
class WindowInfo:
    """ウィンドウ情報を保持するデータクラス"""
    title: str
    left: int
    top: int
    width: int
    height: int
    handle: Optional[object] = None


@dataclass
class Region:
    """画面領域を表すデータクラス"""
    left: int
    top: int
    width: int
    height: int


class WindowManager:
    """
    Kindleウィンドウの検出・管理を行うクラス

    Kindle for PCアプリケーションのウィンドウを検出し、
    ウィンドウのアクティブ化や位置情報の取得を行います。
    """

    # Kindle for PCのウィンドウタイトルに含まれるキーワード
    KINDLE_KEYWORDS = ["kindle", "Kindle"]

    def __init__(self, window_title_pattern: Optional[str] = None):
        """
        WindowManagerの初期化

        Args:
            window_title_pattern: ウィンドウタイトルのパターン（オプション）
                                 指定しない場合はデフォルトのKindleキーワードを使用
        """
        self.window_title_pattern = window_title_pattern
        logger.info("WindowManager initialized")

    def find_kindle_window(self) -> Optional[WindowInfo]:
        """
        Kindle for PCのウィンドウを検出する

        Returns:
            WindowInfo: 検出されたウィンドウ情報。見つからない場合はNone

        Raises:
            RuntimeError: ウィンドウの検出中にエラーが発生した場合
        """
        try:
            logger.debug("Searching for Kindle window...")
            all_windows = gw.getAllWindows()

            # カスタムパターンが指定されている場合はそれを使用
            if self.window_title_pattern:
                for window in all_windows:
                    if self.window_title_pattern.lower() in window.title.lower():
                        window_info = self._create_window_info(window)
                        logger.info(f"Kindle window found: {window_info.title}")
                        return window_info
            else:
                # デフォルトのKindleキーワードで検索
                for window in all_windows:
                    if any(keyword in window.title for keyword in self.KINDLE_KEYWORDS):
                        window_info = self._create_window_info(window)
                        logger.info(f"Kindle window found: {window_info.title}")
                        return window_info

            logger.warning("Kindle window not found")
            return None

        except Exception as e:
            error_msg = f"Error while searching for Kindle window: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def activate_window(self, window_info: WindowInfo) -> bool:
        """
        指定されたウィンドウをアクティブ化する

        Args:
            window_info: アクティブ化するウィンドウ情報

        Returns:
            bool: アクティブ化に成功した場合はTrue、失敗した場合はFalse
        """
        try:
            import win32gui
            import win32con

            logger.debug(f"Activating window: {window_info.title}")

            # ウィンドウハンドルを取得
            hwnd = win32gui.FindWindow(None, window_info.title)
            if not hwnd:
                logger.error(f"Window handle not found: {window_info.title}")
                return False

            # 複数回リトライ
            max_retries = 3
            for attempt in range(max_retries):
                # 方法1: pygetwindow
                try:
                    windows = gw.getWindowsWithTitle(window_info.title)
                    if windows:
                        target_window = windows[0]
                        if target_window.isMinimized:
                            target_window.restore()
                            time.sleep(0.3)
                        target_window.activate()
                except Exception as e:
                    logger.debug(f"pygetwindow activation failed (attempt {attempt+1}): {e}")

                # 方法2: win32gui (フォールバック)
                try:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                except Exception as e:
                    logger.debug(f"win32gui activation failed (attempt {attempt+1}): {e}")

                time.sleep(0.3)

                # アクティブ化の検証
                current_hwnd = win32gui.GetForegroundWindow()
                if current_hwnd == hwnd:
                    logger.info(f"Window activated successfully: {window_info.title}")
                    return True

                logger.warning(f"Window activation verification failed (attempt {attempt+1}/{max_retries})")
                time.sleep(0.5)

            # すべてのリトライが失敗
            logger.error(f"Failed to activate window after {max_retries} attempts: {window_info.title}")
            return False

        except Exception as e:
            logger.error(f"Failed to activate window: {e}")
            return False

    def maximize_window(self, window_info: WindowInfo) -> bool:
        """
        指定されたウィンドウを最大化する（KindleのF11フルスクリーン）

        Args:
            window_info: 最大化するウィンドウ情報

        Returns:
            bool: 最大化に成功した場合はTrue、失敗した場合はFalse
        """
        try:
            import pyautogui

            logger.debug(f"Maximizing window with F11: {window_info.title}")

            # ウィンドウがアクティブであることを確認
            if not self.activate_window(window_info):
                logger.warning("Failed to activate window before maximizing")
                return False

            # F11キーでフルスクリーン化
            pyautogui.press('f11')
            time.sleep(3.0)  # フルスクリーン化が完了するまで待機

            logger.info(f"Window maximized with F11 successfully: {window_info.title}")
            return True

        except Exception as e:
            logger.error(f"Failed to maximize window: {e}")
            return False

    def get_window_region(self, window_info: WindowInfo, client_only: bool = True) -> Region:
        """
        ウィンドウの領域情報を取得する

        Args:
            window_info: 領域を取得するウィンドウ情報
            client_only: True の場合、クライアント領域（コンテンツ部分）のみを取得

        Returns:
            Region: ウィンドウの領域情報
        """
        logger.debug(f"Getting window region for: {window_info.title}, client_only={client_only}")

        if client_only:
            # クライアント領域（タイトルバー・ツールバーを除く）を取得
            try:
                import win32gui
                hwnd = win32gui.FindWindow(None, window_info.title)
                if hwnd:
                    # ウィンドウ全体の矩形（スクリーン座標）
                    window_rect = win32gui.GetWindowRect(hwnd)
                    # クライアント領域の矩形（ウィンドウ座標）
                    client_rect = win32gui.GetClientRect(hwnd)

                    # クライアント領域の左上をスクリーン座標に変換
                    client_screen_pos = win32gui.ClientToScreen(hwnd, (0, 0))

                    # クライアント領域のサイズ（物理ピクセル）
                    # ClientToScreen で取得した実際の座標を使用
                    left = client_screen_pos[0]
                    top = client_screen_pos[1]
                    width = client_rect[2] - client_rect[0]
                    height = client_rect[3] - client_rect[1]

                    region = Region(
                        left=left,
                        top=top,
                        width=width,
                        height=height
                    )
                    logger.debug(f"Client region: left={region.left}, top={region.top}, "
                                f"width={region.width}, height={region.height}")
                    logger.debug(f"Window rect: {window_rect}, Client rect: {client_rect}")
                    return region
                else:
                    logger.warning(f"Could not get client region, using window region")
            except Exception as e:
                logger.warning(f"Failed to get client region: {e}, using window region")

        # フォールバック: ウィンドウ全体の領域
        region = Region(
            left=window_info.left,
            top=window_info.top,
            width=window_info.width,
            height=window_info.height
        )

        logger.debug(f"Window region: left={region.left}, top={region.top}, "
                    f"width={region.width}, height={region.height}")

        return region

    def list_all_windows(self) -> List[WindowInfo]:
        """
        現在開いているすべてのウィンドウのリストを取得する

        Returns:
            List[WindowInfo]: すべてのウィンドウ情報のリスト
        """
        try:
            logger.debug("Listing all windows...")
            all_windows = gw.getAllWindows()

            window_list = []
            for window in all_windows:
                if window.title:  # タイトルが空でないウィンドウのみ
                    window_info = self._create_window_info(window)
                    window_list.append(window_info)

            logger.info(f"Found {len(window_list)} windows")
            return window_list

        except Exception as e:
            logger.error(f"Error while listing windows: {e}")
            return []

    def _create_window_info(self, window) -> WindowInfo:
        """
        pygetwindowのWindowオブジェクトからWindowInfoを作成する

        Args:
            window: pygetwindowのWindowオブジェクト

        Returns:
            WindowInfo: ウィンドウ情報
        """
        return WindowInfo(
            title=window.title,
            left=window.left,
            top=window.top,
            width=window.width,
            height=window.height,
            handle=window
        )


# 使用例とテスト用のヘルパー関数
def find_and_activate_kindle() -> Optional[WindowInfo]:
    """
    Kindleウィンドウを検出してアクティブ化する便利関数

    Returns:
        WindowInfo: アクティブ化されたウィンドウ情報。失敗した場合はNone
    """
    manager = WindowManager()
    window_info = manager.find_kindle_window()

    if window_info:
        if manager.activate_window(window_info):
            return window_info

    return None
