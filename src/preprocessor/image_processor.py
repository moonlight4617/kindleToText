"""
画像前処理モジュール

このモジュールは、OCR処理の精度を向上させるために、
スクリーンショット画像に対して各種前処理を行います。
"""

from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image
from loguru import logger


class ImageProcessor:
    """
    画像前処理を行うクラス

    OCRの精度向上のために、ノイズ除去、コントラスト調整、
    傾き補正、トリミング、二値化などの処理を行います。
    """

    def __init__(
        self,
        config: Optional[dict] = None,
        enable_noise_removal: Optional[bool] = None,
        enable_contrast_adjustment: Optional[bool] = None,
        enable_skew_correction: Optional[bool] = None,
        enable_binarization: Optional[bool] = None
    ):
        """
        ImageProcessorの初期化

        Args:
            config: 設定辞書（preprocessing設定全体）
            enable_noise_removal: ノイズ除去を有効にするか
            enable_contrast_adjustment: コントラスト調整を有効にするか
            enable_skew_correction: 傾き補正を有効にするか
            enable_binarization: 二値化を有効にするか
        """
        # 設定辞書から値を抽出（優先順位: 引数 > 設定辞書 > デフォルト）
        if config:
            self.enable_noise_removal = enable_noise_removal if enable_noise_removal is not None else config.get("noise_reduction", {}).get("enabled", True)
            self.enable_contrast_adjustment = enable_contrast_adjustment if enable_contrast_adjustment is not None else config.get("contrast", {}).get("enabled", True)
            self.enable_skew_correction = enable_skew_correction if enable_skew_correction is not None else config.get("skew_correction", {}).get("enabled", True)
            self.enable_binarization = enable_binarization if enable_binarization is not None else config.get("binarization", {}).get("enabled", True)
            self.config = config
        else:
            self.enable_noise_removal = enable_noise_removal if enable_noise_removal is not None else True
            self.enable_contrast_adjustment = enable_contrast_adjustment if enable_contrast_adjustment is not None else True
            self.enable_skew_correction = enable_skew_correction if enable_skew_correction is not None else True
            self.enable_binarization = enable_binarization if enable_binarization is not None else True
            self.config = {}

        logger.info(
            f"ImageProcessor initialized: "
            f"noise_removal={self.enable_noise_removal}, "
            f"contrast={self.enable_contrast_adjustment}, "
            f"skew_correction={self.enable_skew_correction}, "
            f"binarization={self.enable_binarization}"
        )

    def pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """
        PIL ImageをOpenCV形式に変換する

        Args:
            pil_image: PIL Image

        Returns:
            np.ndarray: OpenCV形式の画像
        """
        # RGBモードに変換
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # NumPy配列に変換
        numpy_image = np.array(pil_image)

        # RGBからBGRに変換（OpenCVの形式）
        opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)

        return opencv_image

    def cv2_to_pil(self, cv2_image: np.ndarray) -> Image.Image:
        """
        OpenCV形式をPIL Imageに変換する

        Args:
            cv2_image: OpenCV形式の画像

        Returns:
            Image.Image: PIL Image
        """
        # BGRからRGBに変換
        if len(cv2_image.shape) == 3:
            rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        else:
            # グレースケールの場合
            rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_GRAY2RGB)

        # PIL Imageに変換
        pil_image = Image.fromarray(rgb_image)

        return pil_image

    def remove_noise(
        self,
        image: Image.Image,
        kernel_size: int = 3
    ) -> Image.Image:
        """
        画像からノイズを除去する

        Args:
            image: 入力画像
            kernel_size: フィルタのカーネルサイズ（奇数）

        Returns:
            Image.Image: ノイズ除去後の画像
        """
        try:
            logger.debug(f"Removing noise: kernel_size={kernel_size}")

            # PIL ImageをOpenCV形式に変換
            cv2_image = self.pil_to_cv2(image)

            # メディアンフィルタでノイズ除去
            denoised = cv2.medianBlur(cv2_image, kernel_size)

            # PIL Imageに戻す
            result = self.cv2_to_pil(denoised)

            logger.debug("Noise removal completed")
            return result

        except Exception as e:
            logger.error(f"Error in noise removal: {e}")
            return image

    def adjust_contrast(
        self,
        image: Image.Image,
        clip_limit: float = 2.0,
        tile_grid_size: Tuple[int, int] = (8, 8)
    ) -> Image.Image:
        """
        画像のコントラストを調整する（CLAHE使用）

        Args:
            image: 入力画像
            clip_limit: コントラスト制限の閾値
            tile_grid_size: タイルのグリッドサイズ

        Returns:
            Image.Image: コントラスト調整後の画像
        """
        try:
            logger.debug(
                f"Adjusting contrast: clip_limit={clip_limit}, "
                f"tile_grid_size={tile_grid_size}"
            )

            # PIL ImageをOpenCV形式に変換
            cv2_image = self.pil_to_cv2(image)

            # グレースケールに変換
            gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)

            # CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(
                clipLimit=clip_limit,
                tileGridSize=tile_grid_size
            )
            enhanced = clahe.apply(gray)

            # カラーに戻す
            result_cv2 = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

            # PIL Imageに戻す
            result = self.cv2_to_pil(result_cv2)

            logger.debug("Contrast adjustment completed")
            return result

        except Exception as e:
            logger.error(f"Error in contrast adjustment: {e}")
            return image

    def correct_skew(
        self,
        image: Image.Image,
        angle_threshold: float = 0.5
    ) -> Image.Image:
        """
        画像の傾きを補正する

        Args:
            image: 入力画像
            angle_threshold: 補正を適用する最小角度（度）

        Returns:
            Image.Image: 傾き補正後の画像
        """
        try:
            logger.debug(f"Correcting skew: threshold={angle_threshold}")

            # PIL ImageをOpenCV形式に変換
            cv2_image = self.pil_to_cv2(image)

            # グレースケールに変換
            gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)

            # エッジ検出
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # ハフ変換で直線を検出
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

            if lines is None:
                logger.debug("No lines detected, skipping skew correction")
                return image

            # 角度を計算
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                if -45 < angle < 45:  # 有効な範囲の角度のみ
                    angles.append(angle)

            if not angles:
                logger.debug("No valid angles found")
                return image

            # 中央値を傾き角度とする
            skew_angle = np.median(angles)

            if abs(skew_angle) < angle_threshold:
                logger.debug(f"Skew angle {skew_angle:.2f}° is below threshold")
                return image

            # 画像を回転
            (h, w) = cv2_image.shape[:2]
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
            rotated = cv2.warpAffine(
                cv2_image,
                rotation_matrix,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )

            # PIL Imageに戻す
            result = self.cv2_to_pil(rotated)

            logger.debug(f"Skew corrected by {skew_angle:.2f}°")
            return result

        except Exception as e:
            logger.error(f"Error in skew correction: {e}")
            return image

    def trim_margins(
        self,
        image: Image.Image,
        margin_threshold: int = 240,
        dark_threshold: int = 50
    ) -> Image.Image:
        """
        画像の余白をトリミングする（白い余白と黒い余白の両方に対応）

        Args:
            image: 入力画像
            margin_threshold: 白い余白と判定する輝度の閾値（0-255）
            dark_threshold: 黒い余白と判定する輝度の閾値（0-255）

        Returns:
            Image.Image: トリミング後の画像
        """
        try:
            logger.debug(f"Trimming margins: white_threshold={margin_threshold}, dark_threshold={dark_threshold}")

            # PIL ImageをOpenCV形式に変換
            cv2_image = self.pil_to_cv2(image)
            img_height, img_width = cv2_image.shape[:2]

            # グレースケールに変換
            gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)

            # 明るい領域（白い背景＝ページコンテンツ領域）を検出
            # 閾値以上の輝度を持つ領域を白色ページとみなす
            _, white_mask = cv2.threshold(gray, margin_threshold - 50, 255, cv2.THRESH_BINARY)

            # ノイズ除去
            kernel = np.ones((10, 10), np.uint8)
            white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
            white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)

            # 最大の連続した白い矩形領域を検出
            contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                logger.debug("No content area found, skipping trimming")
                return image

            # 最大面積の輪郭を取得
            largest_contour = max(contours, key=cv2.contourArea)
            x_start, y_start, new_width, new_height = cv2.boundingRect(largest_contour)
            x_end = x_start + new_width
            y_end = y_start + new_height

            # パディングを追加（コンテンツの一部が切れないように）
            padding = 10
            x_start = max(0, x_start - padding)
            x_end = min(img_width, x_end + padding)
            y_start = max(0, y_start - padding)
            y_end = min(img_height, y_end + padding)

            # トリミング後のサイズを計算
            new_width = x_end - x_start
            new_height = y_end - y_start

            # 画像サイズの変更が小さすぎる場合はスキップ
            if new_width > img_width * 0.95 and new_height > img_height * 0.95:
                logger.debug("Trimming area too small, skipping")
                return image

            # トリミング
            cropped = cv2_image[y_start:y_end, x_start:x_end]

            # PIL Imageに戻す
            result = self.cv2_to_pil(cropped)

            width_reduction = img_width - new_width
            height_reduction = img_height - new_height
            logger.debug(
                f"Margins trimmed: x={x_start}, y={y_start}, w={new_width}, h={new_height} "
                f"(reduced: {width_reduction}x{height_reduction})"
            )
            return result

        except Exception as e:
            logger.error(f"Error in margin trimming: {e}")
            return image

    def binarize(
        self,
        image: Image.Image,
        method: str = "otsu",
        threshold: int = 127,
        block_size: int = 11,
        c: int = 2
    ) -> Image.Image:
        """
        画像を二値化する

        Args:
            image: 入力画像
            method: 二値化手法（"otsu", "adaptive", "simple"）
            threshold: 閾値（simpleの場合のみ使用）
            block_size: 適応的二値化のブロックサイズ（奇数）
            c: 適応的二値化の定数

        Returns:
            Image.Image: 二値化後の画像
        """
        try:
            logger.debug(f"Binarizing image: method={method}")

            # PIL ImageをOpenCV形式に変換
            cv2_image = self.pil_to_cv2(image)

            # グレースケールに変換
            gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)

            if method == "otsu":
                # 大津の二値化
                _, binary = cv2.threshold(
                    gray,
                    0,
                    255,
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
            elif method == "adaptive":
                # 適応的二値化
                # block_sizeは奇数でなければならない
                if block_size % 2 == 0:
                    block_size += 1
                binary = cv2.adaptiveThreshold(
                    gray,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    block_size,
                    c
                )
            else:  # simple
                # 単純な閾値処理
                _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

            # カラーに戻す
            result_cv2 = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

            # PIL Imageに戻す
            result = self.cv2_to_pil(result_cv2)

            logger.debug("Binarization completed")
            return result

        except Exception as e:
            logger.error(f"Error in binarization: {e}")
            return image

    def optimize_for_ocr(
        self,
        image: Image.Image,
        custom_settings: Optional[dict] = None
    ) -> Image.Image:
        """
        OCR用に画像を最適化する（統合処理）

        Args:
            image: 入力画像
            custom_settings: カスタム設定（各処理のパラメータ）

        Returns:
            Image.Image: 最適化後の画像
        """
        try:
            logger.info("Starting OCR optimization pipeline")

            result = image

            # 設定ファイルから値を取得（custom_settingsで上書き可能）
            settings = custom_settings or {}

            # 1. ノイズ除去
            if self.enable_noise_removal:
                kernel_size = settings.get("noise_kernel_size") or self.config.get("noise_reduction", {}).get("kernel_size", 3)
                result = self.remove_noise(result, kernel_size=kernel_size)

            # 2. コントラスト調整
            if self.enable_contrast_adjustment:
                clip_limit = settings.get("contrast_clip_limit") or self.config.get("contrast", {}).get("clip_limit", 2.0)
                tile_size = settings.get("contrast_tile_size") or tuple(self.config.get("contrast", {}).get("tile_grid_size", [8, 8]))
                result = self.adjust_contrast(
                    result,
                    clip_limit=clip_limit,
                    tile_grid_size=tile_size
                )

            # 3. 傾き補正
            if self.enable_skew_correction:
                angle_threshold = settings.get("skew_threshold") or self.config.get("skew_correction", {}).get("angle_threshold", 0.5)
                result = self.correct_skew(result, angle_threshold=angle_threshold)

            # 4. 余白トリミング
            margin_trim_config = self.config.get("margin_trim", {})
            enable_trimming = settings.get("enable_trimming")
            if enable_trimming is None:
                enable_trimming = margin_trim_config.get("enabled", True)

            if enable_trimming:
                margin_threshold = settings.get("margin_threshold") or margin_trim_config.get("threshold", 240)
                dark_threshold = settings.get("dark_threshold") or margin_trim_config.get("dark_threshold", 50)
                result = self.trim_margins(result, margin_threshold=margin_threshold, dark_threshold=dark_threshold)

            # 5. 二値化
            if self.enable_binarization:
                binarization_config = self.config.get("binarization", {})
                method = settings.get("binarization_method") or binarization_config.get("method", "otsu")
                threshold = settings.get("binarization_threshold") or binarization_config.get("threshold", 127)
                block_size = settings.get("binarization_block_size") or binarization_config.get("block_size", 11)
                c = settings.get("binarization_c") or binarization_config.get("c", 2)
                result = self.binarize(result, method=method, threshold=threshold, block_size=block_size, c=c)

            logger.info("OCR optimization pipeline completed")
            return result

        except Exception as e:
            logger.error(f"Error in OCR optimization: {e}")
            return image


# 使用例とヘルパー関数
def quick_optimize(
    image: Image.Image,
    preset: str = "default"
) -> Image.Image:
    """
    クイック最適化の便利関数

    Args:
        image: 入力画像
        preset: プリセット設定（"default", "light", "aggressive"）

    Returns:
        Image.Image: 最適化後の画像
    """
    presets = {
        "default": {
            "enable_noise_removal": True,
            "enable_contrast_adjustment": True,
            "enable_skew_correction": True,
            "enable_binarization": True
        },
        "light": {
            "enable_noise_removal": False,
            "enable_contrast_adjustment": True,
            "enable_skew_correction": False,
            "enable_binarization": False
        },
        "aggressive": {
            "enable_noise_removal": True,
            "enable_contrast_adjustment": True,
            "enable_skew_correction": True,
            "enable_binarization": True
        }
    }

    config = presets.get(preset, presets["default"])
    processor = ImageProcessor(**config)

    custom_settings = {}
    if preset == "aggressive":
        custom_settings = {
            "noise_kernel_size": 5,
            "contrast_clip_limit": 3.0,
            "binarization_method": "adaptive"
        }

    return processor.optimize_for_ocr(image, custom_settings)
