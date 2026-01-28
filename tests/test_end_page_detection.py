"""
最終ページ検出機能のテストスクリプト

画像類似度判定と最終ページ検出器が正しく動作するかをテストします。
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Windows環境での文字エンコーディング問題を回避
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.image_similarity import ImageSimilarityChecker
from src.utils.end_page_detector import EndPageDetector


def create_test_image(text: str, size=(800, 600), bg_color='white', text_color='black'):
    """テスト用の画像を作成"""
    image = Image.new('RGB', size, color=bg_color)
    draw = ImageDraw.Draw(image)

    # テキストを描画
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 40)
    except:
        font = None

    draw.text((100, 250), text, fill=text_color, font=font)
    return image


def test_image_similarity():
    """画像類似度判定のテスト"""
    print("=" * 80)
    print("Test 1: Image Similarity Checker")
    print("=" * 80)
    print()

    checker = ImageSimilarityChecker(hash_size=16, similarity_threshold=5)

    # テスト1: 同じ画像
    print("[Test 1-1] Comparing identical images...")
    image1 = create_test_image("Page 1")
    image2 = create_test_image("Page 1")

    is_similar = checker.are_images_similar(image1, image2)
    score = checker.calculate_similarity_score(image1, image2)

    print(f"  Result: {'✓ Similar' if is_similar else '✗ Not similar'}")
    print(f"  Similarity score: {score:.4f}")
    assert is_similar, "Identical images should be similar"
    print()

    # テスト2: 異なる画像
    print("[Test 1-2] Comparing different images...")
    image3 = create_test_image("Page 2 - Different content")

    is_similar = checker.are_images_similar(image1, image3)
    score = checker.calculate_similarity_score(image1, image3)

    print(f"  Result: {'✓ Similar' if is_similar else '✗ Not similar'}")
    print(f"  Similarity score: {score:.4f}")
    assert not is_similar, "Different images should not be similar"
    print()

    # テスト3: わずかに異なる画像
    print("[Test 1-3] Comparing slightly different images...")
    image4 = create_test_image("Page 1", bg_color='#FEFEFE')  # ほぼ同じ背景色

    is_similar = checker.are_images_similar(image1, image4)
    score = checker.calculate_similarity_score(image1, image4)

    print(f"  Result: {'✓ Similar' if is_similar else '✗ Not similar'}")
    print(f"  Similarity score: {score:.4f}")
    print()

    print("✓ Image Similarity Checker tests passed!")
    print()


def test_end_page_detector():
    """最終ページ検出器のテスト"""
    print("=" * 80)
    print("Test 2: End Page Detector")
    print("=" * 80)
    print()

    detector = EndPageDetector(consecutive_same_pages=3, similarity_threshold=5)

    # テスト1: 異なるページが続く場合
    print("[Test 2-1] Testing with different pages...")
    for i in range(5):
        image = create_test_image(f"Page {i+1}")
        is_end = detector.check_page(image)
        print(f"  Page {i+1}: {'End detected' if is_end else 'Continue'}")
        assert not is_end, f"Should not detect end at page {i+1}"
    print("  ✓ No false end detection")
    print()

    # テスト2: 同じページが3回続く場合
    print("[Test 2-2] Testing with 3 consecutive same pages...")
    detector.reset()

    # 異なるページを2つ
    for i in range(2):
        image = create_test_image(f"Page {i+1}")
        is_end = detector.check_page(image)
        print(f"  Page {i+1}: {'End detected' if is_end else 'Continue'} (count={detector.get_current_count()})")
        assert not is_end

    # 同じページを3回
    last_page_image = create_test_image("Last Page")
    for i in range(3):
        is_end = detector.check_page(last_page_image)
        count = detector.get_current_count()
        print(f"  Last page attempt {i+1}: {'End detected' if is_end else 'Continue'} (count={count})")

        if i < 2:
            assert not is_end, f"Should not detect end on attempt {i+1}"
        else:
            assert is_end, "Should detect end on 3rd consecutive same page"

    print("  ✓ End page detection working correctly")
    print()

    # テスト3: リセット機能
    print("[Test 2-3] Testing reset function...")
    detector.reset()
    assert detector.get_current_count() == 0, "Count should be 0 after reset"
    assert len(detector.recent_images) == 0, "Recent images should be cleared"
    print("  ✓ Reset function working correctly")
    print()

    print("✓ End Page Detector tests passed!")
    print()


def test_with_actual_screenshots():
    """実際のスクリーンショットでテスト（存在する場合）"""
    print("=" * 80)
    print("Test 3: Testing with Actual Screenshots (if available)")
    print("=" * 80)
    print()

    # スクリーンショットディレクトリを探す
    screenshot_dirs = list(Path("output").glob("*_screenshots"))

    if not screenshot_dirs:
        print("  ℹ No screenshot directories found - skipping actual screenshot test")
        print()
        return

    screenshot_dir = screenshot_dirs[0]
    screenshots = sorted(screenshot_dir.glob("*.png"))

    if len(screenshots) < 5:
        print(f"  ℹ Not enough screenshots ({len(screenshots)}) - skipping test")
        print()
        return

    print(f"  Found {len(screenshots)} screenshots in {screenshot_dir.name}")
    print()

    detector = EndPageDetector(consecutive_same_pages=3, similarity_threshold=5)

    # 最初の5枚をテスト
    print("  Testing first 5 screenshots:")
    for i, screenshot_path in enumerate(screenshots[:5]):
        image = Image.open(screenshot_path)
        is_end = detector.check_page(image)
        similarity = detector.get_similarity_score(image)

        similarity_str = f"{similarity:.2%}" if similarity else "N/A"
        print(f"    {screenshot_path.name}: "
              f"{'END' if is_end else 'Continue'} "
              f"(similarity={similarity_str}, count={detector.get_current_count()})")

    print()
    print("✓ Actual screenshot test completed!")
    print()


def main():
    """メイン処理"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "End Page Detection Test Suite" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    try:
        # テスト1: 画像類似度判定
        test_image_similarity()

        # テスト2: 最終ページ検出器
        test_end_page_detector()

        # テスト3: 実際のスクリーンショット
        test_with_actual_screenshots()

        # 完了
        print("=" * 80)
        print("✓ All tests passed successfully!")
        print("=" * 80)
        print()
        print("The end page detection feature is ready to use.")
        print()
        print("Usage:")
        print("  python main.py --title \"Book Title\" --total-pages 500")
        print()
        print("  (Specify a large number like 500, it will auto-stop at the actual end)")
        print()

        return 0

    except AssertionError as e:
        print()
        print("=" * 80)
        print("✗ Test failed:")
        print(f"  {e}")
        print("=" * 80)
        return 1

    except Exception as e:
        print()
        print("=" * 80)
        print("✗ Unexpected error:")
        print(f"  {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
