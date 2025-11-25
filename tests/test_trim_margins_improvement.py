"""
改善されたtrim_marginsメソッドのテスト
"""
import pytest
from pathlib import Path
from PIL import Image
import yaml

from src.preprocessor.image_processor import ImageProcessor


class TestTrimMarginsImprovement:
    """改善されたtrim_marginsメソッドのテスト"""

    @pytest.fixture
    def config(self):
        """設定ファイルを読み込む"""
        config_path = Path("config/config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def screenshot_image(self):
        """実際のスクリーンショットを読み込む"""
        screenshot_path = Path("output/LLM自作入門_screenshots/page_0002.png")
        if screenshot_path.exists():
            return Image.open(screenshot_path)
        return None

    def test_trim_margins_with_black_borders(self, config, screenshot_image):
        """黒い余白を含むスクリーンショットをトリミング"""
        if screenshot_image is None:
            pytest.skip("Screenshot file not found")

        processor = ImageProcessor(config=config["preprocessing"])

        original_size = screenshot_image.size
        print(f"\nOriginal image size: {original_size}")

        # 改善されたトリミングを実行
        margin_config = config["preprocessing"]["margin_trim"]
        trimmed = processor.trim_margins(
            screenshot_image,
            margin_threshold=margin_config["threshold"],
            dark_threshold=margin_config["dark_threshold"]
        )

        trimmed_size = trimmed.size
        print(f"Trimmed image size: {trimmed_size}")

        # サイズが大幅に変わっていることを確認
        width_reduction = original_size[0] - trimmed_size[0]
        height_reduction = original_size[1] - trimmed_size[1]

        print(f"Width reduction: {width_reduction} pixels ({width_reduction / original_size[0] * 100:.1f}%)")
        print(f"Height reduction: {height_reduction} pixels ({height_reduction / original_size[1] * 100:.1f}%)")

        # 少なくとも幅が10%以上削減されることを期待
        assert width_reduction > original_size[0] * 0.1, "Expected significant width reduction"

    def test_full_pipeline_with_real_screenshot(self, config, screenshot_image):
        """実際のスクリーンショットに対して完全な前処理パイプラインを実行"""
        if screenshot_image is None:
            pytest.skip("Screenshot file not found")

        processor = ImageProcessor(config=config["preprocessing"])

        original_size = screenshot_image.size
        print(f"\nOriginal image size: {original_size}")

        # 完全な前処理パイプラインを実行
        processed = processor.optimize_for_ocr(screenshot_image)

        processed_size = processed.size
        print(f"Processed image size: {processed_size}")

        # 処理後の画像を保存してデバッグ
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        processed.save(output_dir / "test_processed_page_0002.png")
        print(f"Processed image saved to: {output_dir / 'test_processed_page_0002.png'}")

        # 画像が返されることを確認
        assert processed is not None
        assert isinstance(processed, Image.Image)

    def test_save_intermediate_steps(self, config, screenshot_image):
        """各処理ステップの中間結果を保存"""
        if screenshot_image is None:
            pytest.skip("Screenshot file not found")

        processor = ImageProcessor(config=config["preprocessing"])

        output_dir = Path("output/debug_steps")
        output_dir.mkdir(parents=True, exist_ok=True)

        result = screenshot_image
        result.save(output_dir / "0_original.png")

        # 1. ノイズ除去
        result = processor.remove_noise(result)
        result.save(output_dir / "1_noise_removed.png")

        # 2. コントラスト調整
        result = processor.adjust_contrast(result)
        result.save(output_dir / "2_contrast_adjusted.png")

        # 3. 傾き補正
        result = processor.correct_skew(result)
        result.save(output_dir / "3_skew_corrected.png")

        # 4. トリミング（改善版）
        margin_config = config["preprocessing"]["margin_trim"]
        result = processor.trim_margins(
            result,
            margin_threshold=margin_config["threshold"],
            dark_threshold=margin_config["dark_threshold"]
        )
        result.save(output_dir / "4_trimmed.png")
        print(f"\n After trimming size: {result.size}")

        # 5. 二値化
        binarization_config = config["preprocessing"]["binarization"]
        result = processor.binarize(
            result,
            method=binarization_config["method"],
            block_size=binarization_config["block_size"],
            c=binarization_config["c"]
        )
        result.save(output_dir / "5_binarized.png")

        print(f"\nDebug images saved to: {output_dir}")
        print(f"Final size: {result.size}")
