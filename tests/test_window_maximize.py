"""
Kindleウィンドウ最大化テストスクリプト

このスクリプトは、Kindleウィンドウを検出、アクティブ化、最大化して、
スクリーンショットを撮影します。
"""

import sys
import ctypes
from pathlib import Path

# Windows DPI Aware を設定
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from src.capture.window_manager import WindowManager
from src.capture.screenshot import ScreenshotCapture


def main():
    print("=" * 80)
    print("Kindleウィンドウ最大化テスト")
    print("=" * 80)
    print()

    # WindowManagerを初期化
    print("[1] Kindleウィンドウを検索中...")
    window_manager = WindowManager()
    window = window_manager.find_kindle_window()

    if not window:
        print("❌ Kindleウィンドウが見つかりませんでした")
        print()
        print("現在開いているウィンドウ:")
        all_windows = window_manager.list_all_windows()
        for win in all_windows[:10]:  # 最初の10個を表示
            print(f"  - {win.title}")
        return 1

    print(f"✓ Kindleウィンドウを検出: {window.title}")
    print(f"  位置: ({window.left}, {window.top})")
    print(f"  サイズ: {window.width} x {window.height}")
    print()

    # ウィンドウをアクティブ化
    print("[2] ウィンドウをアクティブ化中...")
    if not window_manager.activate_window(window):
        print("❌ アクティブ化に失敗しました")
        return 1
    print("✓ アクティブ化成功")
    print()

    # ウィンドウを最大化（F11でフルスクリーン化）
    print("[3] ウィンドウをフルスクリーン化中（F11）...")
    if not window_manager.maximize_window(window):
        print("❌ フルスクリーン化に失敗しました")
        return 1
    print("✓ フルスクリーン化成功")
    print("  注意: F11でフルスクリーン化されたため、ウィンドウとして検出できなくなる可能性があります")
    print()

    # 最大化後のウィンドウ情報を再取得
    print("[4] フルスクリーン後のウィンドウ情報を取得中...")
    import time
    time.sleep(0.5)  # フルスクリーン化が完了するまで待つ
    window = window_manager.find_kindle_window()

    region = None
    if not window:
        print("  ℹ フルスクリーンモードのため、ウィンドウとして検出できませんでした")
        print("  → 画面全体を撮影領域として使用します")
    else:
        print(f"✓ ウィンドウ情報を更新")
        print(f"  位置: ({window.left}, {window.top})")
        print(f"  サイズ: {window.width} x {window.height}")
        region = window_manager.get_window_region(window)
    print()

    # スクリーンショットを撮影
    print("[5] スクリーンショットを撮影中...")
    screenshot_capture = ScreenshotCapture()

    if region:
        print(f"  撮影領域: left={region.left}, top={region.top}, "
              f"width={region.width}, height={region.height}")
    else:
        print(f"  撮影領域: 画面全体（フルスクリーンモード）")

    image = screenshot_capture.capture_screen(region)
    if not image:
        print("❌ スクリーンショット撮影に失敗しました")
        return 1

    print(f"✓ スクリーンショット撮影成功")
    print(f"  画像サイズ: {image.size}")
    print()

    # スクリーンショットを保存
    output_dir = Path("output/test_maximize")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "test_maximized_screenshot.png"

    if screenshot_capture.save_screenshot(image, output_path):
        print(f"✓ スクリーンショットを保存: {output_path}")
    else:
        print("❌ スクリーンショットの保存に失敗しました")
        return 1

    print()
    print("=" * 80)
    print("✓ すべてのテストが成功しました！")
    print("=" * 80)
    print()
    print(f"保存されたスクリーンショットを確認してください: {output_path}")
    print()

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
