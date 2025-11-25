"""
画像フィルター処理モジュール

このモジュールは、画像に対して様々なフィルター処理を適用します。
"""

from typing import Tuple
import cv2
import numpy as np
from PIL import Image
from loguru import logger


class ImageFilters:
    """
    画像フィルター処理を行うクラス

    様々な画像フィルターを提供し、画像品質の向上や
    特定の特徴の強調を行います。
    """

    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """PIL ImageをOpenCV形式に変換"""
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        numpy_image = np.array(pil_image)
        return cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)

    @staticmethod
    def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
        """OpenCV形式をPIL Imageに変換"""
        if len(cv2_image.shape) == 3:
            rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(rgb_image)

    @staticmethod
    def gaussian_blur(
        image: Image.Image,
        kernel_size: Tuple[int, int] = (5, 5),
        sigma: float = 0
    ) -> Image.Image:
        """
        ガウシアンぼかしフィルターを適用

        Args:
            image: 入力画像
            kernel_size: カーネルサイズ（奇数のタプル）
            sigma: ガウシアンカーネルの標準偏差

        Returns:
            Image.Image: フィルター適用後の画像
        """
        try:
            logger.debug(f"Applying Gaussian blur: kernel={kernel_size}, sigma={sigma}")

            cv2_image = ImageFilters.pil_to_cv2(image)
            blurred = cv2.GaussianBlur(cv2_image, kernel_size, sigma)
            result = ImageFilters.cv2_to_pil(blurred)

            logger.debug("Gaussian blur applied")
            return result

        except Exception as e:
            logger.error(f"Error in Gaussian blur: {e}")
            return image

    @staticmethod
    def bilateral_filter(
        image: Image.Image,
        diameter: int = 9,
        sigma_color: float = 75,
        sigma_space: float = 75
    ) -> Image.Image:
        """
        バイラテラルフィルターを適用（エッジを保持しながらノイズ除去）

        Args:
            image: 入力画像
            diameter: フィルタの直径
            sigma_color: 色空間のシグマ
            sigma_space: 座標空間のシグマ

        Returns:
            Image.Image: フィルター適用後の画像
        """
        try:
            logger.debug(
                f"Applying bilateral filter: d={diameter}, "
                f"sigma_color={sigma_color}, sigma_space={sigma_space}"
            )

            cv2_image = ImageFilters.pil_to_cv2(image)
            filtered = cv2.bilateralFilter(
                cv2_image,
                diameter,
                sigma_color,
                sigma_space
            )
            result = ImageFilters.cv2_to_pil(filtered)

            logger.debug("Bilateral filter applied")
            return result

        except Exception as e:
            logger.error(f"Error in bilateral filter: {e}")
            return image

    @staticmethod
    def sharpen(
        image: Image.Image,
        kernel_type: str = "default",
        strength: float = 1.0
    ) -> Image.Image:
        """
        シャープニングフィルターを適用

        Args:
            image: 入力画像
            kernel_type: カーネルタイプ（"default", "strong", "unsharp"）
            strength: シャープ化の強度

        Returns:
            Image.Image: シャープ化後の画像
        """
        try:
            logger.debug(f"Applying sharpen filter: type={kernel_type}, strength={strength}")

            cv2_image = ImageFilters.pil_to_cv2(image)

            # カーネルを選択
            if kernel_type == "strong":
                kernel = np.array([
                    [-1, -1, -1],
                    [-1,  9, -1],
                    [-1, -1, -1]
                ], dtype=np.float32)
            elif kernel_type == "unsharp":
                kernel = np.array([
                    [ 0, -1,  0],
                    [-1,  5, -1],
                    [ 0, -1,  0]
                ], dtype=np.float32)
            else:  # default
                kernel = np.array([
                    [ 0, -1,  0],
                    [-1,  5, -1],
                    [ 0, -1,  0]
                ], dtype=np.float32)

            # 強度を調整
            if strength != 1.0:
                identity = np.array([
                    [0, 0, 0],
                    [0, 1, 0],
                    [0, 0, 0]
                ], dtype=np.float32)
                kernel = identity + strength * (kernel - identity)

            # フィルターを適用
            sharpened = cv2.filter2D(cv2_image, -1, kernel)
            result = ImageFilters.cv2_to_pil(sharpened)

            logger.debug("Sharpen filter applied")
            return result

        except Exception as e:
            logger.error(f"Error in sharpen filter: {e}")
            return image

    @staticmethod
    def morphological_operation(
        image: Image.Image,
        operation: str = "close",
        kernel_size: Tuple[int, int] = (5, 5),
        iterations: int = 1
    ) -> Image.Image:
        """
        モルフォロジー演算を適用

        Args:
            image: 入力画像
            operation: 演算タイプ（"erode", "dilate", "open", "close"）
            kernel_size: カーネルサイズ
            iterations: 反復回数

        Returns:
            Image.Image: 演算後の画像
        """
        try:
            logger.debug(
                f"Applying morphological operation: {operation}, "
                f"kernel={kernel_size}, iterations={iterations}"
            )

            cv2_image = ImageFilters.pil_to_cv2(image)

            # グレースケールに変換
            gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)

            # カーネルを作成
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)

            # 演算を適用
            if operation == "erode":
                result_gray = cv2.erode(gray, kernel, iterations=iterations)
            elif operation == "dilate":
                result_gray = cv2.dilate(gray, kernel, iterations=iterations)
            elif operation == "open":
                result_gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel, iterations=iterations)
            elif operation == "close":
                result_gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel, iterations=iterations)
            else:
                logger.warning(f"Unknown operation: {operation}")
                return image

            # カラーに戻す
            result_cv2 = cv2.cvtColor(result_gray, cv2.COLOR_GRAY2BGR)
            result = ImageFilters.cv2_to_pil(result_cv2)

            logger.debug("Morphological operation applied")
            return result

        except Exception as e:
            logger.error(f"Error in morphological operation: {e}")
            return image

    @staticmethod
    def unsharp_mask(
        image: Image.Image,
        kernel_size: Tuple[int, int] = (5, 5),
        sigma: float = 1.0,
        amount: float = 1.5,
        threshold: int = 0
    ) -> Image.Image:
        """
        アンシャープマスクを適用

        Args:
            image: 入力画像
            kernel_size: ガウシアンぼかしのカーネルサイズ
            sigma: ガウシアンぼかしのシグマ
            amount: シャープ化の量
            threshold: 適用する最小差分

        Returns:
            Image.Image: アンシャープマスク適用後の画像
        """
        try:
            logger.debug(
                f"Applying unsharp mask: kernel={kernel_size}, "
                f"sigma={sigma}, amount={amount}"
            )

            cv2_image = ImageFilters.pil_to_cv2(image)

            # ぼかし画像を作成
            blurred = cv2.GaussianBlur(cv2_image, kernel_size, sigma)

            # アンシャープマスクを適用
            sharpened = cv2.addWeighted(
                cv2_image,
                1.0 + amount,
                blurred,
                -amount,
                0
            )

            # 閾値処理
            if threshold > 0:
                diff = cv2.absdiff(cv2_image, blurred)
                mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)[1]
                sharpened = np.where(mask > 0, sharpened, cv2_image)

            result = ImageFilters.cv2_to_pil(sharpened)

            logger.debug("Unsharp mask applied")
            return result

        except Exception as e:
            logger.error(f"Error in unsharp mask: {e}")
            return image

    @staticmethod
    def enhance_text(image: Image.Image) -> Image.Image:
        """
        テキスト認識用に画像を強調する

        Args:
            image: 入力画像

        Returns:
            Image.Image: 強調後の画像
        """
        try:
            logger.debug("Enhancing text")

            cv2_image = ImageFilters.pil_to_cv2(image)

            # グレースケールに変換
            gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)

            # コントラストを強調
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # ノイズ除去
            denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)

            # 二値化
            _, binary = cv2.threshold(
                denoised,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # カラーに戻す
            result_cv2 = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            result = ImageFilters.cv2_to_pil(result_cv2)

            logger.debug("Text enhancement completed")
            return result

        except Exception as e:
            logger.error(f"Error in text enhancement: {e}")
            return image

    @staticmethod
    def apply_custom_kernel(
        image: Image.Image,
        kernel: np.ndarray
    ) -> Image.Image:
        """
        カスタムカーネルを適用

        Args:
            image: 入力画像
            kernel: 適用するカーネル（NumPy配列）

        Returns:
            Image.Image: フィルター適用後の画像
        """
        try:
            logger.debug(f"Applying custom kernel: shape={kernel.shape}")

            cv2_image = ImageFilters.pil_to_cv2(image)
            filtered = cv2.filter2D(cv2_image, -1, kernel)
            result = ImageFilters.cv2_to_pil(filtered)

            logger.debug("Custom kernel applied")
            return result

        except Exception as e:
            logger.error(f"Error in custom kernel: {e}")
            return image


# 使用例とヘルパー関数
def apply_preset_filter(
    image: Image.Image,
    preset: str = "ocr"
) -> Image.Image:
    """
    プリセットフィルターを適用する便利関数

    Args:
        image: 入力画像
        preset: プリセット名（"ocr", "denoise", "sharpen"）

    Returns:
        Image.Image: フィルター適用後の画像
    """
    filters = ImageFilters()

    if preset == "ocr":
        return filters.enhance_text(image)
    elif preset == "denoise":
        return filters.bilateral_filter(image)
    elif preset == "sharpen":
        return filters.sharpen(image, kernel_type="default", strength=1.0)
    else:
        logger.warning(f"Unknown preset: {preset}")
        return image
