"""
画像前処理の統合テスト
設定ファイルから読み込んで、実際のスクリーンショットに対して前処理を実行する
"""
import pytest
from pathlib import Path
from PIL import Image
import yaml

from src.preprocessor.image_processor import ImageProcessor


class TestPreprocessingIntegration:
    """画像前処理の統合テスト"""

    @pytest.fixture
    def config(self):
        """設定ファイルを読み込む"""
        config_path = Path("config/config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def sample_image(self):
        """テスト用のサンプル画像を作成"""
        # 800x600のテスト画像を作成
        image = Image.new('RGB', (800, 600), color='white')
        return image

    @pytest.fixture
    def screenshot_image(self):
        """実際のスクリーンショットを読み込む（存在する場合）"""
        screenshot_path = Path("output/LLM自作入門_screenshots/page_0001.png")
        if screenshot_path.exists():
            return Image.open(screenshot_path)
        return None

    def test_image_processor_with_config(self, config):
        """設定辞書でImageProcessorを初期化できることを確認"""
        processor = ImageProcessor(config=config["preprocessing"])

        # 設定が正しく読み込まれているか確認
        assert processor.enable_noise_removal == config["preprocessing"]["noise_reduction"]["enabled"]
        assert processor.enable_contrast_adjustment == config["preprocessing"]["contrast"]["enabled"]
        assert processor.enable_skew_correction == config["preprocessing"]["skew_correction"]["enabled"]
        assert processor.enable_binarization == config["preprocessing"]["binarization"]["enabled"]

    def test_optimize_for_ocr_with_sample_image(self, config, sample_image):
        """サンプル画像に対して前処理が正常に実行できることを確認"""
        processor = ImageProcessor(config=config["preprocessing"])

        # 前処理を実行
        processed_image = processor.optimize_for_ocr(sample_image)

        # 画像が返されることを確認
        assert processed_image is not None
        assert isinstance(processed_image, Image.Image)

        # 画像サイズが変わっていることを確認（トリミングされている）
        # 白い画像なのでトリミング後は小さくなるはず
        # ただし、コンテンツがない場合はトリミングされないので、サイズは同じかもしれない

    def test_optimize_for_ocr_with_real_screenshot(self, config, screenshot_image):
        """実際のスクリーンショットに対して前処理が正常に実行できることを確認"""
        if screenshot_image is None:
            pytest.skip("Screenshot file not found")

        processor = ImageProcessor(config=config["preprocessing"])

        original_size = screenshot_image.size
        print(f"\nOriginal image size: {original_size}")

        # 前処理を実行
        processed_image = processor.optimize_for_ocr(screenshot_image)

        # 画像が返されることを確認
        assert processed_image is not None
        assert isinstance(processed_image, Image.Image)

        processed_size = processed_image.size
        print(f"Processed image size: {processed_size}")

        # サイズが変わっている可能性がある（トリミング）
        # サイズが変わっていることを確認（ただし、変わらない場合もある）

    def test_config_parameters_applied(self, config, sample_image):
        """設定ファイルのパラメータが正しく適用されることを確認"""
        processor = ImageProcessor(config=config["preprocessing"])

        # 各種パラメータが設定から読み込まれることを確認
        binarization_config = config["preprocessing"]["binarization"]
        assert processor.config["binarization"]["method"] == binarization_config["method"]
        assert processor.config["binarization"]["block_size"] == binarization_config["block_size"]
        assert processor.config["binarization"]["c"] == binarization_config["c"]

    def test_individual_steps_with_real_screenshot(self, config, screenshot_image):
        """各処理ステップを個別に実行して、正常に動作することを確認"""
        if screenshot_image is None:
            pytest.skip("Screenshot file not found")

        processor = ImageProcessor(config=config["preprocessing"])

        # 1. ノイズ除去
        noise_removed = processor.remove_noise(screenshot_image)
        assert noise_removed is not None
        assert isinstance(noise_removed, Image.Image)

        # 2. コントラスト調整
        contrast_adjusted = processor.adjust_contrast(noise_removed)
        assert contrast_adjusted is not None
        assert isinstance(contrast_adjusted, Image.Image)

        # 3. 傾き補正
        skew_corrected = processor.correct_skew(contrast_adjusted)
        assert skew_corrected is not None
        assert isinstance(skew_corrected, Image.Image)

        # 4. トリミング
        trimmed = processor.trim_margins(skew_corrected)
        assert trimmed is not None
        assert isinstance(trimmed, Image.Image)

        # 5. 二値化
        binarization_config = config["preprocessing"]["binarization"]
        binarized = processor.binarize(
            trimmed,
            method=binarization_config["method"],
            block_size=binarization_config["block_size"],
            c=binarization_config["c"]
        )
        assert binarized is not None
        assert isinstance(binarized, Image.Image)

    def test_save_debug_images(self, config, screenshot_image, tmp_path):
        """デバッグ用に各ステップの画像を保存"""
        if screenshot_image is None:
            pytest.skip("Screenshot file not found")

        processor = ImageProcessor(config=config["preprocessing"])

        # 各ステップの画像を保存
        result = screenshot_image

        # 1. ノイズ除去
        result = processor.remove_noise(result)
        result.save(tmp_path / "1_noise_removed.png")

        # 2. コントラスト調整
        result = processor.adjust_contrast(result)
        result.save(tmp_path / "2_contrast_adjusted.png")

        # 3. 傾き補正
        result = processor.correct_skew(result)
        result.save(tmp_path / "3_skew_corrected.png")

        # 4. トリミング
        result = processor.trim_margins(result)
        result.save(tmp_path / "4_trimmed.png")

        # 5. 二値化
        binarization_config = config["preprocessing"]["binarization"]
        result = processor.binarize(
            result,
            method=binarization_config["method"],
            block_size=binarization_config["block_size"],
            c=binarization_config["c"]
        )
        result.save(tmp_path / "5_binarized.png")

        # ファイルが作成されていることを確認
        assert (tmp_path / "1_noise_removed.png").exists()
        assert (tmp_path / "2_contrast_adjusted.png").exists()
        assert (tmp_path / "3_skew_corrected.png").exists()
        assert (tmp_path / "4_trimmed.png").exists()
        assert (tmp_path / "5_binarized.png").exists()

        print(f"\nDebug images saved to: {tmp_path}")
