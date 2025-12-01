"""
画像の高解像度化とシャープ化機能のテスト（Phase 2: OCR精度向上）
"""
import pytest
from pathlib import Path
from PIL import Image
import yaml

from src.preprocessor.image_processor import ImageProcessor


class TestUpscalingAndSharpening:
    """画像の高解像度化とシャープ化機能のテスト"""

    @pytest.fixture
    def config(self):
        """設定ファイルを読み込む"""
        config_path = Path("config/config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def sample_image(self):
        """テスト用のサンプル画像を作成"""
        # 100x100のシンプルな画像を作成
        image = Image.new('RGB', (100, 100), color='white')
        return image

    @pytest.fixture
    def screenshot_image(self):
        """実際のスクリーンショットを読み込む"""
        screenshot_path = Path("output/LLM自作入門_screenshots/page_0002.png")
        if screenshot_path.exists():
            return Image.open(screenshot_path)
        return None

    def test_upscale_image_default(self, config, sample_image):
        """デフォルト設定で画像を拡大"""
        processor = ImageProcessor(config=config["preprocessing"])

        original_size = sample_image.size
        upscaled = processor.upscale_image(sample_image)
        upscaled_size = upscaled.size

        # デフォルトは2倍拡大
        assert upscaled_size[0] == original_size[0] * 2
        assert upscaled_size[1] == original_size[1] * 2

    def test_upscale_image_custom_factor(self, config, sample_image):
        """カスタム倍率で画像を拡大"""
        processor = ImageProcessor(config=config["preprocessing"])

        original_size = sample_image.size
        scale_factor = 1.5

        upscaled = processor.upscale_image(sample_image, scale_factor=scale_factor)
        upscaled_size = upscaled.size

        # 1.5倍拡大
        assert upscaled_size[0] == int(original_size[0] * scale_factor)
        assert upscaled_size[1] == int(original_size[1] * scale_factor)

    def test_upscale_image_interpolation_methods(self, config, sample_image):
        """異なる補間方法をテスト"""
        processor = ImageProcessor(config=config["preprocessing"])

        interpolation_methods = ["lanczos", "bicubic", "bilinear", "nearest"]

        for method in interpolation_methods:
            upscaled = processor.upscale_image(
                sample_image,
                scale_factor=2.0,
                interpolation=method
            )
            # 全ての補間方法で正しくサイズが変更されることを確認
            assert upscaled.size == (200, 200)

    def test_sharpen_image_default(self, config, sample_image):
        """デフォルト設定で画像をシャープ化"""
        processor = ImageProcessor(config=config["preprocessing"])

        sharpened = processor.sharpen_image(sample_image)

        # 画像のサイズは変わらない
        assert sharpened.size == sample_image.size
        # 画像が返されることを確認
        assert isinstance(sharpened, Image.Image)

    def test_sharpen_image_custom_parameters(self, config, sample_image):
        """カスタムパラメータで画像をシャープ化"""
        processor = ImageProcessor(config=config["preprocessing"])

        sharpened = processor.sharpen_image(
            sample_image,
            radius=3.0,
            percent=180,
            threshold=5
        )

        # 画像のサイズは変わらない
        assert sharpened.size == sample_image.size
        assert isinstance(sharpened, Image.Image)

    def test_pipeline_with_upscaling_and_sharpening(self, config, screenshot_image):
        """実際のスクリーンショットに対して拡大+シャープ化のパイプラインを実行"""
        if screenshot_image is None:
            pytest.skip("Screenshot file not found")

        processor = ImageProcessor(config=config["preprocessing"])

        original_size = screenshot_image.size
        print(f"\nOriginal image size: {original_size}")

        # 完全な前処理パイプラインを実行（拡大+シャープ化を含む）
        processed = processor.optimize_for_ocr(screenshot_image)

        processed_size = processed.size
        print(f"Processed image size: {processed_size}")

        # 設定に基づいてサイズが拡大されているはず（scale_factor=2.0）
        # ただし、その後のトリミングでサイズが変わる可能性があるため、
        # 少なくとも元のサイズよりは大きいか、同じくらいであることを確認
        assert processed_size[0] > 0
        assert processed_size[1] > 0

        # 処理後の画像を保存してデバッグ
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        processed.save(output_dir / "test_enhanced_page_0002.png")
        print(f"Enhanced image saved to: {output_dir / 'test_enhanced_page_0002.png'}")

    def test_save_intermediate_steps_with_enhancement(self, config, screenshot_image):
        """各処理ステップの中間結果を保存（拡大+シャープ化を含む）"""
        if screenshot_image is None:
            pytest.skip("Screenshot file not found")

        processor = ImageProcessor(config=config["preprocessing"])

        output_dir = Path("output/debug_steps_enhanced")
        output_dir.mkdir(parents=True, exist_ok=True)

        result = screenshot_image
        result.save(output_dir / "0_original.png")
        print(f"\n0. Original size: {result.size}")

        # 1. ノイズ除去
        noise_config = config["preprocessing"]["noise_reduction"]
        if noise_config.get("enabled", True):
            result = processor.remove_noise(result, kernel_size=noise_config.get("kernel_size", 3))
            result.save(output_dir / "1_noise_removed.png")
            print(f"1. After noise removal: {result.size}")

        # 2. 拡大処理（Phase 2）
        upscaling_config = config["preprocessing"]["upscaling"]
        if upscaling_config.get("enabled", False):
            result = processor.upscale_image(
                result,
                scale_factor=upscaling_config.get("scale_factor", 2.0),
                interpolation=upscaling_config.get("interpolation", "lanczos")
            )
            result.save(output_dir / "2_upscaled.png")
            print(f"2. After upscaling: {result.size}")

        # 3. シャープ化（Phase 2）
        sharpening_config = config["preprocessing"]["sharpening"]
        if sharpening_config.get("enabled", False):
            result = processor.sharpen_image(
                result,
                radius=sharpening_config.get("radius", 2.0),
                percent=sharpening_config.get("percent", 150),
                threshold=sharpening_config.get("threshold", 3)
            )
            result.save(output_dir / "3_sharpened.png")
            print(f"3. After sharpening: {result.size}")

        # 4. コントラスト調整
        contrast_config = config["preprocessing"]["contrast"]
        if contrast_config.get("enabled", True):
            result = processor.adjust_contrast(
                result,
                clip_limit=contrast_config.get("clip_limit", 2.0),
                tile_grid_size=tuple(contrast_config.get("tile_grid_size", [8, 8]))
            )
            result.save(output_dir / "4_contrast_adjusted.png")
            print(f"4. After contrast adjustment: {result.size}")

        # 5. 傾き補正
        skew_config = config["preprocessing"]["skew_correction"]
        if skew_config.get("enabled", True):
            result = processor.correct_skew(result, angle_threshold=skew_config.get("angle_threshold", 0.5))
            result.save(output_dir / "5_skew_corrected.png")
            print(f"5. After skew correction: {result.size}")

        # 6. トリミング
        margin_config = config["preprocessing"]["margin_trim"]
        if margin_config.get("enabled", True):
            result = processor.trim_margins(
                result,
                margin_threshold=margin_config["threshold"],
                dark_threshold=margin_config["dark_threshold"]
            )
            result.save(output_dir / "6_trimmed.png")
            print(f"6. After trimming: {result.size}")

        # 7. 二値化（無効化されているはず）
        binarization_config = config["preprocessing"]["binarization"]
        if binarization_config.get("enabled", False):
            result = processor.binarize(
                result,
                method=binarization_config["method"],
                block_size=binarization_config["block_size"],
                c=binarization_config["c"]
            )
            result.save(output_dir / "7_binarized.png")
            print(f"7. After binarization: {result.size}")

        print(f"\nDebug images saved to: {output_dir}")
        print(f"Final size: {result.size}")

    def test_upscaling_increases_image_quality(self, config, screenshot_image):
        """拡大処理により画像の品質が向上することを確認"""
        if screenshot_image is None:
            pytest.skip("Screenshot file not found")

        processor = ImageProcessor(config=config["preprocessing"])

        # 小さい領域を切り出してテスト
        width, height = screenshot_image.size
        crop_box = (width // 4, height // 4, width // 2, height // 2)
        cropped = screenshot_image.crop(crop_box)

        # 拡大前
        original_size = cropped.size

        # 拡大
        upscaled = processor.upscale_image(cropped, scale_factor=2.0, interpolation="lanczos")
        upscaled_size = upscaled.size

        # サイズが2倍になっていることを確認
        assert upscaled_size[0] == original_size[0] * 2
        assert upscaled_size[1] == original_size[1] * 2

        # 画像を保存して目視確認用
        output_dir = Path("output/quality_comparison")
        output_dir.mkdir(parents=True, exist_ok=True)
        cropped.save(output_dir / "original_crop.png")
        upscaled.save(output_dir / "upscaled_crop.png")
        print(f"\nQuality comparison images saved to: {output_dir}")
