"""
スクリーンショット撮影モジュール

このモジュールは、Kindle for PCのウィンドウをスクリーンショット撮影し、
画像として保存する機能を提供します。
"""

import time
from pathlib import Path
from typing import Optional, Union
from PIL import Image
import mss
import pyautogui
from loguru import logger

from .window_manager import Region


class ScreenshotCapture:
    """
    スクリーンショット撮影とページ操作を行うクラス

    Kindle for PCのウィンドウのスクリーンショットを撮影し、
    ページ送り操作などを実行します。
    """

    def __init__(
        self,
        page_turn_key: str = "right",
        page_load_delay: float = 1.5,
        screenshot_delay: float = 0.5
    ):
        """
        ScreenshotCaptureの初期化

        Args:
            page_turn_key: ページ送りに使用するキー（デフォルト: "right"）
            page_load_delay: ページ読み込み待機時間（秒）
            screenshot_delay: スクリーンショット前の待機時間（秒）
        """
        self.page_turn_key = page_turn_key
        self.page_load_delay = page_load_delay
        self.screenshot_delay = screenshot_delay
        logger.info(
            f"ScreenshotCapture initialized: "
            f"page_turn_key={page_turn_key}, "
            f"page_load_delay={page_load_delay}s, "
            f"screenshot_delay={screenshot_delay}s"
        )

    def capture_screen(self, region: Optional[Region] = None) -> Optional[Image.Image]:
        """
        画面またはウィンドウ領域のスクリーンショットを撮影する

        Args:
            region: 撮影する領域。Noneの場合は全画面を撮影

        Returns:
            Image.Image: 撮影された画像。失敗した場合はNone

        Raises:
            RuntimeError: スクリーンショットの撮影中にエラーが発生した場合
        """
        try:
            # スクリーンショット前の待機時間
            if self.screenshot_delay > 0:
                time.sleep(self.screenshot_delay)

            logger.debug("Capturing screenshot...")

            with mss.mss() as sct:
                if region:
                    # 指定された領域をキャプチャ
                    monitor = {
                        "left": region.left,
                        "top": region.top,
                        "width": region.width,
                        "height": region.height
                    }
                    screenshot = sct.grab(monitor)
                else:
                    # 全画面をキャプチャ
                    monitor = sct.monitors[1]  # プライマリモニター
                    screenshot = sct.grab(monitor)

                # mssのスクリーンショットをPIL Imageに変換
                image = Image.frombytes(
                    "RGB",
                    screenshot.size,
                    screenshot.bgra,
                    "raw",
                    "BGRX"
                )

                logger.debug(f"Screenshot captured: size={image.size}")
                return image

        except Exception as e:
            error_msg = f"Error while capturing screenshot: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def save_screenshot(
        self,
        image: Image.Image,
        file_path: Union[str, Path],
        quality: int = 95
    ) -> bool:
        """
        スクリーンショット画像をファイルに保存する

        Args:
            image: 保存する画像
            file_path: 保存先のファイルパス
            quality: JPEG品質（1-100、デフォルト: 95）

        Returns:
            bool: 保存に成功した場合はTrue、失敗した場合はFalse
        """
        try:
            file_path = Path(file_path)

            # ディレクトリが存在しない場合は作成
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # ファイル形式を判定
            file_extension = file_path.suffix.lower()

            if file_extension in [".jpg", ".jpeg"]:
                # JPEGの場合はRGBモードで保存
                if image.mode != "RGB":
                    image = image.convert("RGB")
                image.save(file_path, "JPEG", quality=quality, optimize=True)
            elif file_extension == ".png":
                # PNGの場合はそのまま保存
                image.save(file_path, "PNG", optimize=True)
            else:
                # デフォルトはPNG
                image.save(file_path, "PNG")

            logger.info(f"Screenshot saved: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return False

    def turn_page(self, direction: str = "forward") -> bool:
        """
        ページを送る

        Args:
            direction: ページ送りの方向（"forward" or "backward"）

        Returns:
            bool: ページ送りに成功した場合はTrue、失敗した場合はFalse
        """
        try:
            if direction == "forward":
                key = self.page_turn_key
            elif direction == "backward":
                if self.page_turn_key == "right":
                    key = "left"
                elif self.page_turn_key == "left":
                    key = "right"
                else:
                    key = self.page_turn_key
            else:
                logger.error(f"Invalid direction: {direction}")
                return False

            logger.debug(f"Turning page: direction={direction}, key={key}")

            # キーを押す（pyautoguiは小文字のキー名を期待）
            pyautogui.press(key.lower())

            logger.debug("Page turn command sent")
            return True

        except Exception as e:
            logger.error(f"Failed to turn page: {e}")
            return False

    def wait_for_page_load(self, custom_delay: Optional[float] = None) -> None:
        """
        ページの読み込みを待つ

        Args:
            custom_delay: カスタム待機時間（秒）。Noneの場合はデフォルト値を使用
        """
        delay = custom_delay if custom_delay is not None else self.page_load_delay
        logger.debug(f"Waiting for page load: {delay}s")
        time.sleep(delay)

    def capture_and_save(
        self,
        region: Optional[Region],
        file_path: Union[str, Path],
        quality: int = 95
    ) -> bool:
        """
        スクリーンショットを撮影して保存する（一括処理）

        Args:
            region: 撮影する領域
            file_path: 保存先のファイルパス
            quality: JPEG品質（1-100）

        Returns:
            bool: 成功した場合はTrue、失敗した場合はFalse
        """
        try:
            image = self.capture_screen(region)
            if image:
                return self.save_screenshot(image, file_path, quality)
            return False
        except Exception as e:
            logger.error(f"Failed to capture and save screenshot: {e}")
            return False

    def capture_page_sequence(
        self,
        region: Region,
        output_dir: Path,
        start_page: int,
        end_page: int,
        filename_template: str = "page_{:04d}.png"
    ) -> dict:
        """
        複数ページのスクリーンショットを連続撮影する

        Args:
            region: 撮影する領域
            output_dir: 出力ディレクトリ
            start_page: 開始ページ番号
            end_page: 終了ページ番号
            filename_template: ファイル名テンプレート（ページ番号を含む）

        Returns:
            dict: 撮影結果
                - success_count: 成功した撮影数
                - failed_pages: 失敗したページ番号のリスト
                - total_pages: 総ページ数
        """
        logger.info(
            f"Starting page sequence capture: "
            f"pages {start_page}-{end_page}"
        )

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        success_count = 0
        failed_pages = []
        total_pages = end_page - start_page + 1

        for page_num in range(start_page, end_page + 1):
            try:
                # ファイル名を生成
                filename = filename_template.format(page_num)
                file_path = output_dir / filename

                # スクリーンショットを撮影して保存
                if self.capture_and_save(region, file_path):
                    success_count += 1
                    logger.info(f"Page {page_num} captured successfully")
                else:
                    failed_pages.append(page_num)
                    logger.warning(f"Failed to capture page {page_num}")

                # 最後のページでなければページを送る
                if page_num < end_page:
                    self.turn_page("forward")
                    self.wait_for_page_load()

            except Exception as e:
                logger.error(f"Error capturing page {page_num}: {e}")
                failed_pages.append(page_num)

        result = {
            "success_count": success_count,
            "failed_pages": failed_pages,
            "total_pages": total_pages
        }

        logger.info(
            f"Page sequence capture completed: "
            f"{success_count}/{total_pages} pages successful"
        )

        return result


# 使用例とテスト用のヘルパー関数
def quick_screenshot(
    region: Optional[Region] = None,
    output_path: str = "screenshot.png"
) -> bool:
    """
    クイックスクリーンショット撮影の便利関数

    Args:
        region: 撮影する領域
        output_path: 出力ファイルパス

    Returns:
        bool: 成功した場合はTrue
    """
    capture = ScreenshotCapture()
    return capture.capture_and_save(region, output_path)
