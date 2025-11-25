"""
Tesseract OCRエンジン実装

このモジュールは、Tesseract OCRを使用した
テキスト抽出機能を提供します（フォールバック用）。
"""

import time
from typing import Optional, List
import pytesseract
from PIL import Image
from loguru import logger

from .ocr_interface import (
    OCRInterface,
    OCRResult,
    LayoutData,
    TextBlock,
    BoundingBox,
    OCREngineFactory
)


class TesseractEngine(OCRInterface):
    """
    Tesseract OCRエンジン

    汎用的なOCRエンジン（Yomitokuが利用できない場合のフォールバック）
    """

    def __init__(self, config: Optional[dict] = None):
        """
        TesseractEngineの初期化

        Args:
            config: エンジン設定
                - lang: 言語コード（デフォルト: "jpn+eng"）
                - tesseract_cmd: Tesseract実行ファイルパス（オプション）
                - psm: ページセグメンテーションモード（デフォルト: 3）
                - oem: OCRエンジンモード（デフォルト: 3）
                - confidence_threshold: 信頼度閾値（デフォルト: 0.0）
        """
        self.config = config or {}
        self.lang = self.config.get("lang", "jpn+eng")
        self.psm = self.config.get("psm", 3)  # 3 = Fully automatic page segmentation
        self.oem = self.config.get("oem", 3)  # 3 = Default, based on what is available
        self.confidence_threshold = self.config.get("confidence_threshold", 0.0)
        self._initialized = False

        # Tesseract実行ファイルパスが指定されている場合は設定
        tesseract_cmd = self.config.get("tesseract_cmd")
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        logger.info(
            f"TesseractEngine created: lang={self.lang}, "
            f"psm={self.psm}, oem={self.oem}, threshold={self.confidence_threshold}"
        )

    def initialize(self) -> bool:
        """
        Tesseractエンジンを初期化する

        Returns:
            bool: 初期化に成功した場合はTrue
        """
        try:
            logger.info("Initializing Tesseract engine...")

            # Tesseractのバージョンを確認
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")

            # 言語データが利用可能か確認
            available_langs = pytesseract.get_languages()
            logger.info(f"Available languages: {available_langs}")

            # 必要な言語が利用可能か確認
            required_langs = self.lang.split('+')
            for lang in required_langs:
                if lang not in available_langs:
                    logger.warning(f"Language '{lang}' is not available")

            self._initialized = True
            logger.info("Tesseract engine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Tesseract: {e}")
            self._initialized = False
            return False

    def extract_text(self, image: Image.Image) -> OCRResult:
        """
        画像からテキストを抽出する

        Args:
            image: 入力画像

        Returns:
            OCRResult: OCR結果
        """
        if not self._initialized:
            logger.warning("Tesseract not initialized, attempting to initialize...")
            if not self.initialize():
                return OCRResult(
                    text="",
                    confidence=0.0,
                    engine_name=self.get_engine_name(),
                    success=False,
                    error_message="Engine not initialized"
                )

        try:
            start_time = time.time()
            logger.debug("Starting text extraction with Tesseract...")

            # Tesseract設定
            custom_config = f'--psm {self.psm} --oem {self.oem}'

            # OCR実行
            text = pytesseract.image_to_string(
                image,
                lang=self.lang,
                config=custom_config
            )

            # 信頼度を取得
            data = pytesseract.image_to_data(
                image,
                lang=self.lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )

            avg_confidence = self._calculate_average_confidence(data)

            processing_time = time.time() - start_time

            logger.info(
                f"Text extraction completed: "
                f"length={len(text)}, "
                f"confidence={avg_confidence:.2f}, "
                f"time={processing_time:.2f}s"
            )

            return OCRResult(
                text=text,
                confidence=avg_confidence,
                engine_name=self.get_engine_name(),
                processing_time=processing_time,
                success=True
            )

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                engine_name=self.get_engine_name(),
                success=False,
                error_message=str(e)
            )

    def extract_with_layout(self, image: Image.Image) -> OCRResult:
        """
        画像からテキストとレイアウト情報を抽出する

        Args:
            image: 入力画像

        Returns:
            OCRResult: レイアウト情報を含むOCR結果
        """
        if not self._initialized:
            logger.warning("Tesseract not initialized, attempting to initialize...")
            if not self.initialize():
                return OCRResult(
                    text="",
                    confidence=0.0,
                    engine_name=self.get_engine_name(),
                    success=False,
                    error_message="Engine not initialized"
                )

        try:
            start_time = time.time()
            logger.debug("Starting layout extraction with Tesseract...")

            # Tesseract設定
            custom_config = f'--psm {self.psm} --oem {self.oem}'

            # レイアウト情報を含むOCR実行
            data = pytesseract.image_to_data(
                image,
                lang=self.lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )

            # テキストブロックを抽出
            text_blocks = self._extract_text_blocks(data)

            # 全テキストを結合
            full_text = "\n".join([block.text for block in text_blocks])

            # 平均信頼度を計算
            avg_confidence = self._calculate_average_confidence(data)

            # レイアウトデータを作成
            layout = LayoutData(
                full_text=full_text,
                blocks=text_blocks,
                page_width=image.width,
                page_height=image.height,
                language=self.lang,
                average_confidence=avg_confidence
            )

            processing_time = time.time() - start_time

            logger.info(
                f"Layout extraction completed: "
                f"blocks={len(text_blocks)}, "
                f"confidence={avg_confidence:.2f}, "
                f"time={processing_time:.2f}s"
            )

            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                layout=layout,
                engine_name=self.get_engine_name(),
                processing_time=processing_time,
                success=True
            )

        except Exception as e:
            logger.error(f"Layout extraction failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                engine_name=self.get_engine_name(),
                success=False,
                error_message=str(e)
            )

    def get_engine_name(self) -> str:
        """エンジン名を取得"""
        return "tesseract"

    def is_available(self) -> bool:
        """エンジンが利用可能かチェック"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def close(self) -> None:
        """リソースを解放"""
        self._initialized = False
        logger.info("Tesseract engine closed")

    def _extract_text_blocks(self, data: dict) -> List[TextBlock]:
        """
        Tesseract結果からテキストブロックを抽出

        Args:
            data: Tesseract結果（辞書形式）

        Returns:
            List[TextBlock]: テキストブロックのリスト
        """
        blocks = []

        try:
            n_boxes = len(data['text'])

            for i in range(n_boxes):
                # テキストを取得
                text = data['text'][i].strip()
                if not text:
                    continue

                # 信頼度を取得
                confidence = float(data['conf'][i]) / 100.0  # Tesseractは0-100で返す
                if confidence < 0:
                    confidence = 0.0

                # 信頼度閾値でフィルタリング
                if confidence < self.confidence_threshold:
                    continue

                # バウンディングボックスを作成
                bbox = BoundingBox(
                    left=data['left'][i],
                    top=data['top'][i],
                    width=data['width'][i],
                    height=data['height'][i],
                    confidence=confidence
                )

                # ブロックタイプを判定（レベル情報から）
                level = data['level'][i]
                block_type = "text"
                if level == 2:  # Block level
                    block_type = "block"
                elif level == 3:  # Paragraph level
                    block_type = "paragraph"
                elif level == 4:  # Line level
                    block_type = "line"
                elif level == 5:  # Word level
                    block_type = "word"

                # テキストブロックを作成
                block = TextBlock(
                    text=text,
                    bounding_box=bbox,
                    confidence=confidence,
                    block_type=block_type
                )
                blocks.append(block)

        except Exception as e:
            logger.error(f"Failed to extract text blocks: {e}")

        return blocks

    def _calculate_average_confidence(self, data: dict) -> float:
        """
        平均信頼度を計算

        Args:
            data: Tesseract結果（辞書形式）

        Returns:
            float: 平均信頼度（0.0-1.0）
        """
        try:
            confidences = []

            for conf in data['conf']:
                if conf != '-1':  # -1は信頼度情報なし
                    confidence = float(conf) / 100.0
                    if confidence >= 0:
                        confidences.append(confidence)

            if confidences:
                return sum(confidences) / len(confidences)

        except Exception as e:
            logger.error(f"Failed to calculate average confidence: {e}")

        return 0.0


# エンジンを登録
OCREngineFactory.register_engine("tesseract", TesseractEngine)
