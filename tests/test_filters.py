"""
filters.py モジュールのユニットテスト
"""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import patch
from src.preprocessor.filters import ImageFilters, apply_preset_filter


class TestImageFilters:
    """ImageFiltersクラスのテスト"""

    def test_pil_to_cv2(self):
        """PIL ImageからOpenCV形式への変換テスト"""
        pil_image = Image.new("RGB", (100, 100), color=(255, 0, 0))

        cv2_image = ImageFilters.pil_to_cv2(pil_image)

        assert isinstance(cv2_image, np.ndarray)
        assert cv2_image.shape == (100, 100, 3)

    def test_cv2_to_pil(self):
        """OpenCV形式からPIL Imageへの変換テスト"""
        cv2_image = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2_image[:, :] = [0, 0, 255]

        pil_image = ImageFilters.cv2_to_pil(cv2_image)

        assert isinstance(pil_image, Image.Image)
        assert pil_image.size == (100, 100)

    def test_gaussian_blur(self):
        """ガウシアンぼかしテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.gaussian_blur(
            test_image,
            kernel_size=(5, 5),
            sigma=0
        )

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_gaussian_blur_different_kernel_sizes(self):
        """異なるカーネルサイズでのガウシアンぼかしテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        for kernel_size in [(3, 3), (5, 5), (7, 7)]:
            result = ImageFilters.gaussian_blur(test_image, kernel_size=kernel_size)
            assert isinstance(result, Image.Image)

    def test_bilateral_filter(self):
        """バイラテラルフィルターテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.bilateral_filter(
            test_image,
            diameter=9,
            sigma_color=75,
            sigma_space=75
        )

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_sharpen_default(self):
        """デフォルトシャープニングテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.sharpen(test_image, kernel_type="default")

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_sharpen_strong(self):
        """強いシャープニングテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.sharpen(test_image, kernel_type="strong")

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_sharpen_unsharp(self):
        """アンシャープシャープニングテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.sharpen(test_image, kernel_type="unsharp")

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_sharpen_with_strength(self):
        """強度指定シャープニングテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.sharpen(
            test_image,
            kernel_type="default",
            strength=1.5
        )

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_morphological_operation_erode(self):
        """収縮モルフォロジー演算テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.morphological_operation(
            test_image,
            operation="erode",
            kernel_size=(5, 5)
        )

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_morphological_operation_dilate(self):
        """膨張モルフォロジー演算テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.morphological_operation(
            test_image,
            operation="dilate",
            kernel_size=(5, 5)
        )

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_morphological_operation_open(self):
        """オープニングモルフォロジー演算テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.morphological_operation(
            test_image,
            operation="open",
            kernel_size=(5, 5)
        )

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_morphological_operation_close(self):
        """クロージングモルフォロジー演算テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.morphological_operation(
            test_image,
            operation="close",
            kernel_size=(5, 5)
        )

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_morphological_operation_unknown(self):
        """不明なモルフォロジー演算テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.morphological_operation(
            test_image,
            operation="unknown"
        )

        # 不明な演算の場合は元の画像が返される
        assert result == test_image

    def test_morphological_operation_iterations(self):
        """反復回数指定モルフォロジー演算テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.morphological_operation(
            test_image,
            operation="erode",
            iterations=3
        )

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_unsharp_mask(self):
        """アンシャープマスクテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.unsharp_mask(
            test_image,
            kernel_size=(5, 5),
            sigma=1.0,
            amount=1.5
        )

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_unsharp_mask_with_threshold(self):
        """閾値指定アンシャープマスクテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.unsharp_mask(
            test_image,
            threshold=10
        )

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_enhance_text(self):
        """テキスト強調テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = ImageFilters.enhance_text(test_image)

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_apply_custom_kernel(self):
        """カスタムカーネル適用テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        # カスタムカーネルを作成（単純なぼかし）
        kernel = np.ones((3, 3), dtype=np.float32) / 9

        result = ImageFilters.apply_custom_kernel(test_image, kernel)

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_apply_custom_kernel_sharpen(self):
        """シャープニングカスタムカーネルテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        # シャープニングカーネル
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ], dtype=np.float32)

        result = ImageFilters.apply_custom_kernel(test_image, kernel)

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size


class TestHelperFunctions:
    """ヘルパー関数のテスト"""

    def test_apply_preset_filter_ocr(self):
        """OCRプリセットフィルターテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = apply_preset_filter(test_image, preset="ocr")

        assert isinstance(result, Image.Image)

    def test_apply_preset_filter_denoise(self):
        """ノイズ除去プリセットフィルターテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = apply_preset_filter(test_image, preset="denoise")

        assert isinstance(result, Image.Image)

    def test_apply_preset_filter_sharpen(self):
        """シャープ化プリセットフィルターテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = apply_preset_filter(test_image, preset="sharpen")

        assert isinstance(result, Image.Image)

    def test_apply_preset_filter_unknown(self):
        """不明なプリセットフィルターテスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        result = apply_preset_filter(test_image, preset="unknown")

        # 不明なプリセットの場合は元の画像が返される
        assert result == test_image


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    @patch('src.preprocessor.filters.cv2.GaussianBlur')
    def test_gaussian_blur_error(self, mock_blur):
        """ガウシアンぼかしエラーテスト"""
        mock_blur.side_effect = Exception("Test error")

        test_image = Image.new("RGB", (100, 100), color="white")

        result = ImageFilters.gaussian_blur(test_image)

        # エラーが発生しても元の画像が返される
        assert result == test_image

    @patch('src.preprocessor.filters.cv2.bilateralFilter')
    def test_bilateral_filter_error(self, mock_filter):
        """バイラテラルフィルターエラーテスト"""
        mock_filter.side_effect = Exception("Test error")

        test_image = Image.new("RGB", (100, 100), color="white")

        result = ImageFilters.bilateral_filter(test_image)

        # エラーが発生しても元の画像が返される
        assert result == test_image

    @patch('src.preprocessor.filters.cv2.filter2D')
    def test_sharpen_error(self, mock_filter):
        """シャープニングエラーテスト"""
        mock_filter.side_effect = Exception("Test error")

        test_image = Image.new("RGB", (100, 100), color="white")

        result = ImageFilters.sharpen(test_image)

        # エラーが発生しても元の画像が返される
        assert result == test_image

    @patch('src.preprocessor.filters.cv2.morphologyEx')
    def test_morphological_operation_error(self, mock_morph):
        """モルフォロジー演算エラーテスト"""
        mock_morph.side_effect = Exception("Test error")

        test_image = Image.new("RGB", (100, 100), color="white")

        result = ImageFilters.morphological_operation(test_image, operation="open")

        # エラーが発生しても元の画像が返される
        assert result == test_image

    @patch('src.preprocessor.filters.cv2.addWeighted')
    def test_unsharp_mask_error(self, mock_weighted):
        """アンシャープマスクエラーテスト"""
        mock_weighted.side_effect = Exception("Test error")

        test_image = Image.new("RGB", (100, 100), color="white")

        result = ImageFilters.unsharp_mask(test_image)

        # エラーが発生しても元の画像が返される
        assert result == test_image

    @patch('src.preprocessor.filters.cv2.createCLAHE')
    def test_enhance_text_error(self, mock_clahe):
        """テキスト強調エラーテスト"""
        mock_clahe.side_effect = Exception("Test error")

        test_image = Image.new("RGB", (100, 100), color="white")

        result = ImageFilters.enhance_text(test_image)

        # エラーが発生しても元の画像が返される
        assert result == test_image

    @patch('src.preprocessor.filters.cv2.filter2D')
    def test_apply_custom_kernel_error(self, mock_filter):
        """カスタムカーネルエラーテスト"""
        mock_filter.side_effect = Exception("Test error")

        test_image = Image.new("RGB", (100, 100), color="white")
        kernel = np.ones((3, 3), dtype=np.float32) / 9

        result = ImageFilters.apply_custom_kernel(test_image, kernel)

        # エラーが発生しても元の画像が返される
        assert result == test_image


class TestImageProcessingQuality:
    """画像処理品質のテスト"""

    def test_pil_cv2_roundtrip(self):
        """PIL-OpenCV変換の往復テスト"""
        original = Image.new("RGB", (100, 100), color=(123, 45, 67))

        cv2_image = ImageFilters.pil_to_cv2(original)
        result = ImageFilters.cv2_to_pil(cv2_image)

        # 変換往復後も色が保持されているか確認
        assert result.getpixel((50, 50)) == original.getpixel((50, 50))

    def test_filter_chain(self):
        """複数フィルターの連続適用テスト"""
        test_image = Image.new("RGB", (100, 100), color=(128, 128, 128))

        # フィルターチェーン
        result = ImageFilters.gaussian_blur(test_image)
        result = ImageFilters.sharpen(result)
        result = ImageFilters.bilateral_filter(result)

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size
