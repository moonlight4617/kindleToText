"""
image_processor.py モジュールのユニットテスト
"""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import patch, Mock
from src.preprocessor.image_processor import (
    ImageProcessor,
    quick_optimize
)


class TestImageProcessor:
    """ImageProcessorクラスのテスト"""

    def test_init_default(self):
        """デフォルト設定での初期化テスト"""
        processor = ImageProcessor()

        assert processor.enable_noise_removal is True
        assert processor.enable_contrast_adjustment is True
        assert processor.enable_skew_correction is True
        assert processor.enable_binarization is True

    def test_init_custom(self):
        """カスタム設定での初期化テスト"""
        processor = ImageProcessor(
            enable_noise_removal=False,
            enable_contrast_adjustment=True,
            enable_skew_correction=False,
            enable_binarization=False
        )

        assert processor.enable_noise_removal is False
        assert processor.enable_contrast_adjustment is True
        assert processor.enable_skew_correction is False
        assert processor.enable_binarization is False

    def test_pil_to_cv2(self):
        """PIL ImageからOpenCV形式への変換テスト"""
        # テスト画像を作成
        pil_image = Image.new("RGB", (100, 100), color=(255, 0, 0))

        processor = ImageProcessor()
        cv2_image = processor.pil_to_cv2(pil_image)

        assert isinstance(cv2_image, np.ndarray)
        assert cv2_image.shape == (100, 100, 3)
        # OpenCVはBGR形式なので、赤はB=0, G=0, R=255
        assert cv2_image[0, 0, 2] == 255  # R
        assert cv2_image[0, 0, 1] == 0    # G
        assert cv2_image[0, 0, 0] == 0    # B

    def test_cv2_to_pil(self):
        """OpenCV形式からPIL Imageへの変換テスト"""
        # OpenCV形式のテスト画像を作成（BGR）
        cv2_image = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2_image[:, :] = [0, 0, 255]  # BGR: 赤

        processor = ImageProcessor()
        pil_image = processor.cv2_to_pil(cv2_image)

        assert isinstance(pil_image, Image.Image)
        assert pil_image.size == (100, 100)
        # PIL ImageはRGB形式
        assert pil_image.getpixel((0, 0)) == (255, 0, 0)  # RGB

    def test_remove_noise(self):
        """ノイズ除去テスト"""
        # テスト画像を作成
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        processor = ImageProcessor()
        result = processor.remove_noise(test_image, kernel_size=3)

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_remove_noise_different_kernel_sizes(self):
        """異なるカーネルサイズでのノイズ除去テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))
        processor = ImageProcessor()

        for kernel_size in [3, 5, 7]:
            result = processor.remove_noise(test_image, kernel_size=kernel_size)
            assert isinstance(result, Image.Image)
            assert result.size == test_image.size

    def test_adjust_contrast(self):
        """コントラスト調整テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        processor = ImageProcessor()
        result = processor.adjust_contrast(
            test_image,
            clip_limit=2.0,
            tile_grid_size=(8, 8)
        )

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_correct_skew(self):
        """傾き補正テスト"""
        test_image = Image.new("RGB", (200, 200), color="white")

        processor = ImageProcessor()
        result = processor.correct_skew(test_image, angle_threshold=0.5)

        assert isinstance(result, Image.Image)
        # 直線が検出されない場合は元の画像が返される
        assert result.size == test_image.size

    def test_trim_margins(self):
        """余白トリミングテスト"""
        # 中央に黒い領域がある白い画像を作成
        test_image = Image.new("RGB", (200, 200), color="white")
        # 中央に黒い矩形を描画
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_image)
        draw.rectangle([50, 50, 150, 150], fill="black")

        processor = ImageProcessor()
        result = processor.trim_margins(test_image, margin_threshold=240)

        assert isinstance(result, Image.Image)
        # トリミングされるはず
        assert result.size[0] <= test_image.size[0]
        assert result.size[1] <= test_image.size[1]

    def test_trim_margins_no_content(self):
        """コンテンツがない場合のトリミングテスト"""
        # 全体が白い画像
        test_image = Image.new("RGB", (100, 100), color="white")

        processor = ImageProcessor()
        result = processor.trim_margins(test_image)

        assert isinstance(result, Image.Image)
        # 変化なし
        assert result.size == test_image.size

    def test_binarize_otsu(self):
        """大津の二値化テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        processor = ImageProcessor()
        result = processor.binarize(test_image, method="otsu")

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_binarize_adaptive(self):
        """適応的二値化テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        processor = ImageProcessor()
        result = processor.binarize(test_image, method="adaptive")

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_binarize_simple(self):
        """単純二値化テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        processor = ImageProcessor()
        result = processor.binarize(test_image, method="simple", threshold=127)

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_optimize_for_ocr_all_enabled(self):
        """すべての処理を有効にしたOCR最適化テスト"""
        test_image = Image.new("RGB", (200, 200), color="white")

        processor = ImageProcessor(
            enable_noise_removal=True,
            enable_contrast_adjustment=True,
            enable_skew_correction=True,
            enable_binarization=True
        )

        result = processor.optimize_for_ocr(test_image)

        assert isinstance(result, Image.Image)

    def test_optimize_for_ocr_partial_enabled(self):
        """一部の処理のみ有効にしたOCR最適化テスト"""
        test_image = Image.new("RGB", (200, 200), color="white")

        processor = ImageProcessor(
            enable_noise_removal=True,
            enable_contrast_adjustment=False,
            enable_skew_correction=False,
            enable_binarization=True
        )

        result = processor.optimize_for_ocr(test_image)

        assert isinstance(result, Image.Image)

    def test_optimize_for_ocr_with_custom_settings(self):
        """カスタム設定でのOCR最適化テスト"""
        test_image = Image.new("RGB", (200, 200), color="white")

        processor = ImageProcessor()

        custom_settings = {
            "noise_kernel_size": 5,
            "contrast_clip_limit": 3.0,
            "binarization_method": "adaptive",
            "enable_trimming": True,
            "margin_threshold": 250
        }

        result = processor.optimize_for_ocr(test_image, custom_settings)

        assert isinstance(result, Image.Image)

    def test_optimize_for_ocr_no_processing(self):
        """処理なしのOCR最適化テスト"""
        test_image = Image.new("RGB", (100, 100), color="white")

        processor = ImageProcessor(
            enable_noise_removal=False,
            enable_contrast_adjustment=False,
            enable_skew_correction=False,
            enable_binarization=False
        )

        result = processor.optimize_for_ocr(test_image)

        assert isinstance(result, Image.Image)

    def test_pil_to_cv2_rgba(self):
        """RGBA画像の変換テスト"""
        pil_image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))

        processor = ImageProcessor()
        cv2_image = processor.pil_to_cv2(pil_image)

        assert isinstance(cv2_image, np.ndarray)
        assert cv2_image.shape == (100, 100, 3)

    def test_cv2_to_pil_grayscale(self):
        """グレースケール画像の変換テスト"""
        cv2_image = np.ones((100, 100), dtype=np.uint8) * 128

        processor = ImageProcessor()
        pil_image = processor.cv2_to_pil(cv2_image)

        assert isinstance(pil_image, Image.Image)
        assert pil_image.size == (100, 100)


class TestHelperFunctions:
    """ヘルパー関数のテスト"""

    def test_quick_optimize_default(self):
        """デフォルトプリセットのクイック最適化テスト"""
        test_image = Image.new("RGB", (100, 100), color="white")

        result = quick_optimize(test_image, preset="default")

        assert isinstance(result, Image.Image)

    def test_quick_optimize_light(self):
        """lightプリセットのクイック最適化テスト"""
        test_image = Image.new("RGB", (100, 100), color="white")

        result = quick_optimize(test_image, preset="light")

        assert isinstance(result, Image.Image)

    def test_quick_optimize_aggressive(self):
        """aggressiveプリセットのクイック最適化テスト"""
        test_image = Image.new("RGB", (100, 100), color="white")

        result = quick_optimize(test_image, preset="aggressive")

        assert isinstance(result, Image.Image)

    def test_quick_optimize_unknown_preset(self):
        """不明なプリセットの場合、デフォルトを使用"""
        test_image = Image.new("RGB", (100, 100), color="white")

        result = quick_optimize(test_image, preset="unknown")

        assert isinstance(result, Image.Image)


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    @patch('src.preprocessor.image_processor.cv2.medianBlur')
    def test_remove_noise_error(self, mock_blur):
        """ノイズ除去エラーのテスト"""
        mock_blur.side_effect = Exception("Test error")

        test_image = Image.new("RGB", (100, 100), color="white")
        processor = ImageProcessor()

        result = processor.remove_noise(test_image)

        # エラーが発生しても元の画像が返される
        assert result == test_image

    @patch('src.preprocessor.image_processor.cv2.createCLAHE')
    def test_adjust_contrast_error(self, mock_clahe):
        """コントラスト調整エラーのテスト"""
        mock_clahe.side_effect = Exception("Test error")

        test_image = Image.new("RGB", (100, 100), color="white")
        processor = ImageProcessor()

        result = processor.adjust_contrast(test_image)

        # エラーが発生しても元の画像が返される
        assert result == test_image
