"""
Yomitoku OCRエンジン実装

このモジュールは、Yomitoku（日本語特化OCR）を使用した
テキスト抽出機能を提供します。
"""

import time
from typing import Optional, List
import numpy as np
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


class YomitokuEngine(OCRInterface):
    """
    Yomitoku OCRエンジン

    日本語テキスト認識に最適化されたOCRエンジン
    """

    def __init__(self, config: Optional[dict] = None):
        """
        YomitokuEngineの初期化

        Args:
            config: エンジン設定
                - model_name: モデル名（デフォルト: "yomitoku"）
                - device: 使用デバイス（"cpu" or "cuda"）
                - confidence_threshold: 信頼度閾値（デフォルト: 0.0）
        """
        self.config = config or {}
        self.model_name = self.config.get("model_name", "yomitoku")
        self.device = self.config.get("device", "cpu")
        self.confidence_threshold = self.config.get("confidence_threshold", 0.0)
        self.model = None
        self._initialized = False

        logger.info(
            f"YomitokuEngine created: model={self.model_name}, "
            f"device={self.device}, threshold={self.confidence_threshold}"
        )

    def initialize(self) -> bool:
        """
        Yomitokuモデルを初期化する

        Returns:
            bool: 初期化に成功した場合はTrue
        """
        try:
            logger.info("Initializing Yomitoku model...")

            # Yomitokuをインポート
            try:
                from yomitoku import DocumentAnalyzer
            except ImportError:
                logger.error("Yomitoku is not installed. Please install it first.")
                return False

            # モデルを初期化
            self.model = DocumentAnalyzer(
                configs={
                    "model_name": self.model_name,
                    "device": self.device
                }
            )

            self._initialized = True
            logger.info("Yomitoku model initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Yomitoku: {e}")
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
            logger.warning("Yomitoku not initialized, attempting to initialize...")
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
            logger.debug("Starting text extraction with Yomitoku...")

            # PIL ImageをNumPy配列に変換
            image_array = np.array(image)

            # OCR実行
            results = self.model(image_array)

            # テキストを抽出
            extracted_text = self._extract_text_from_results(results)

            # 平均信頼度を計算
            avg_confidence = self._calculate_average_confidence(results)

            processing_time = time.time() - start_time

            logger.info(
                f"Text extraction completed: "
                f"length={len(extracted_text)}, "
                f"confidence={avg_confidence:.2f}, "
                f"time={processing_time:.2f}s"
            )

            return OCRResult(
                text=extracted_text,
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
            logger.warning("Yomitoku not initialized, attempting to initialize...")
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
            logger.debug("Starting layout extraction with Yomitoku...")

            # PIL ImageをNumPy配列に変換
            image_array = np.array(image)

            # OCR実行
            results = self.model(image_array)

            # テキストブロックを抽出
            text_blocks = self._extract_text_blocks(results)

            # 全テキストを結合
            full_text = "\n".join([block.text for block in text_blocks])

            # 平均信頼度を計算
            avg_confidence = self._calculate_average_confidence(results)

            # レイアウトデータを作成
            layout = LayoutData(
                full_text=full_text,
                blocks=text_blocks,
                page_width=image.width,
                page_height=image.height,
                language="jpn",
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
        return "yomitoku"

    def is_available(self) -> bool:
        """エンジンが利用可能かチェック"""
        try:
            import yomitoku
            return True
        except ImportError:
            return False

    def close(self) -> None:
        """リソースを解放"""
        if self.model is not None:
            del self.model
            self.model = None
            self._initialized = False
            logger.info("Yomitoku engine closed")

    def _extract_text_from_results(self, results) -> str:
        """
        Yomitoku結果からテキストを抽出

        Args:
            results: Yomitoku結果（tuple形式: (DocumentAnalyzerSchema, None, None)）

        Returns:
            str: 抽出されたテキスト
        """
        try:
            # Yomitokuの結果はタプル形式: (DocumentAnalyzerSchema, None, None)
            if isinstance(results, tuple) and len(results) > 0:
                doc_schema = results[0]
                if doc_schema is None:
                    return ""

                # DocumentAnalyzerSchemaからparagraphsを取得
                if hasattr(doc_schema, 'paragraphs'):
                    paragraphs = doc_schema.paragraphs
                    # 各段落をorder順にソートしてテキストを抽出
                    sorted_paragraphs = sorted(paragraphs, key=lambda p: p.order)
                    texts = []
                    for para in sorted_paragraphs:
                        if hasattr(para, 'contents') and para.contents:
                            # 改行を含むcontentsをそのまま追加
                            texts.append(para.contents.strip())
                    return '\n\n'.join(texts)

            # 旧形式への対応（フォールバック）
            if hasattr(results, 'text'):
                return results.text
            elif isinstance(results, dict) and 'text' in results:
                return results['text']
            elif hasattr(results, 'ocr_results'):
                # 各行のテキストを結合
                lines = []
                for line in results.ocr_results:
                    if hasattr(line, 'text'):
                        lines.append(line.text)
                    elif isinstance(line, dict) and 'text' in line:
                        lines.append(line['text'])
                return '\n'.join(lines)
            else:
                logger.warning(f"Unknown Yomitoku result format: {type(results)}")
                return ""
        except Exception as e:
            logger.error(f"Failed to extract text from results: {e}")
            return ""

    def _extract_text_blocks(self, results) -> List[TextBlock]:
        """
        Yomitoku結果からテキストブロックを抽出

        Args:
            results: Yomitoku結果

        Returns:
            List[TextBlock]: テキストブロックのリスト
        """
        blocks = []

        try:
            if hasattr(results, 'ocr_results'):
                for idx, line in enumerate(results.ocr_results):
                    # テキストを取得
                    text = ""
                    if hasattr(line, 'text'):
                        text = line.text
                    elif isinstance(line, dict) and 'text' in line:
                        text = line['text']

                    # 信頼度を取得
                    confidence = 0.0
                    if hasattr(line, 'confidence'):
                        confidence = line.confidence
                    elif isinstance(line, dict) and 'confidence' in line:
                        confidence = line['confidence']

                    # バウンディングボックスを取得
                    bbox = None
                    if hasattr(line, 'bbox'):
                        bbox_data = line.bbox
                        if len(bbox_data) >= 4:
                            bbox = BoundingBox(
                                left=int(bbox_data[0]),
                                top=int(bbox_data[1]),
                                width=int(bbox_data[2] - bbox_data[0]),
                                height=int(bbox_data[3] - bbox_data[1]),
                                confidence=confidence
                            )

                    # バウンディングボックスがない場合はデフォルト値
                    if bbox is None:
                        bbox = BoundingBox(
                            left=0,
                            top=idx * 30,
                            width=800,
                            height=30,
                            confidence=confidence
                        )

                    # 信頼度閾値でフィルタリング
                    if confidence >= self.confidence_threshold:
                        block = TextBlock(
                            text=text,
                            bounding_box=bbox,
                            confidence=confidence,
                            block_type="text"
                        )
                        blocks.append(block)

        except Exception as e:
            logger.error(f"Failed to extract text blocks: {e}")

        return blocks

    def _calculate_average_confidence(self, results) -> float:
        """
        平均信頼度を計算

        Args:
            results: Yomitoku結果

        Returns:
            float: 平均信頼度
        """
        try:
            confidences = []

            if hasattr(results, 'ocr_results'):
                for line in results.ocr_results:
                    if hasattr(line, 'confidence'):
                        confidences.append(line.confidence)
                    elif isinstance(line, dict) and 'confidence' in line:
                        confidences.append(line['confidence'])

            if confidences:
                return sum(confidences) / len(confidences)

        except Exception as e:
            logger.error(f"Failed to calculate average confidence: {e}")

        return 0.0


# エンジンを登録
OCREngineFactory.register_engine("yomitoku", YomitokuEngine)
