"""
Google Cloud Vision API OCRエンジン実装

このモジュールは、Google Cloud Vision APIを使用した
高精度なテキスト抽出機能を提供します。
"""

import os
import time
from typing import Optional, List
from pathlib import Path
import io

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


class GoogleVisionEngine(OCRInterface):
    """
    Google Cloud Vision API OCRエンジン

    商用APIを使用した高精度なテキスト認識エンジン
    日本語の専門用語や複雑なレイアウトに対応
    """

    def __init__(self, config: Optional[dict] = None):
        """
        GoogleVisionEngineの初期化

        Args:
            config: エンジン設定（google_visionサブセクションまたは完全なOCR設定）
                - credentials_path: サービスアカウントキーのパス（nullの場合は環境変数を使用）
                - detection_type: "TEXT_DETECTION" or "DOCUMENT_TEXT_DETECTION"
                - language_hints: 言語ヒントのリスト（例: ["ja", "en"]）
                - enable_text_detection_confidence: Confidenceスコアの有効化
        """
        self.config = config or {}

        # If config contains 'google_vision' key, extract it (called from main.py with full OCR config)
        # Otherwise, assume config is already the google_vision subsection (called from test scripts)
        if 'google_vision' in self.config:
            google_config = self.config.get('google_vision', {})
        else:
            google_config = self.config

        self.credentials_path = google_config.get("credentials_path")
        self.detection_type = google_config.get("detection_type", "DOCUMENT_TEXT_DETECTION")
        self.language_hints = google_config.get("language_hints", ["ja", "en"])
        self.enable_confidence = google_config.get("enable_text_detection_confidence", False)

        self.client = None
        self._initialized = False
        self._available = None

        logger.info(
            f"GoogleVisionEngine created: detection_type={self.detection_type}, "
            f"language_hints={self.language_hints}"
        )

    def initialize(self) -> bool:
        """
        Google Cloud Vision API クライアントを初期化する

        Returns:
            bool: 初期化に成功した場合はTrue
        """
        try:
            logger.info("Initializing Google Cloud Vision API client...")

            # Google Cloud Visionをインポート
            try:
                from google.cloud import vision
                self._vision = vision
            except ImportError:
                logger.error(
                    "google-cloud-vision is not installed. "
                    "Please install it: pip install google-cloud-vision"
                )
                return False

            # 認証情報の設定
            if self.credentials_path:
                credentials_path = Path(self.credentials_path)
                if not credentials_path.exists():
                    logger.error(f"Credentials file not found: {credentials_path}")
                    return False

                # 環境変数に設定
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path.absolute())
                logger.info(f"Using credentials from: {credentials_path}")
            else:
                # 環境変数が設定されているかチェック
                if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
                    logger.warning(
                        "No credentials_path specified and GOOGLE_APPLICATION_CREDENTIALS "
                        "environment variable not set. Using default credentials."
                    )

            # クライアントを初期化
            self.client = vision.ImageAnnotatorClient()

            self._initialized = True
            logger.info("Google Cloud Vision API client initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Vision API: {e}")
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
            logger.warning("Google Vision not initialized, attempting to initialize...")
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
            logger.debug("Starting text extraction with Google Cloud Vision API...")

            # PIL ImageをバイトデータにエンコードすることでGoogleVisionに送信
            image_content = self._image_to_bytes(image)

            # Vision APIのImageオブジェクトを作成
            vision_image = self._vision.Image(content=image_content)

            # ImageContextを設定（言語ヒント）
            image_context = self._vision.ImageContext(language_hints=self.language_hints)

            # TEXT_DETECTIONを実行
            response = self.client.text_detection(
                image=vision_image,
                image_context=image_context
            )

            # エラーチェック
            if response.error.message:
                raise Exception(f"API Error: {response.error.message}")

            # テキストを抽出（最初のアノテーションが全文）
            extracted_text = ""
            if response.text_annotations:
                extracted_text = response.text_annotations[0].description

            # 信頼度は基本的に提供されないため、デフォルト値
            avg_confidence = 0.95  # Google Vision APIは高精度なので仮の値

            processing_time = time.time() - start_time

            logger.info(
                f"Text extraction completed: "
                f"length={len(extracted_text)}, "
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
            logger.warning("Google Vision not initialized, attempting to initialize...")
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
            logger.debug("Starting layout extraction with Google Cloud Vision API...")

            # PIL ImageをバイトデータにエンコードすることでGoogleVisionに送信
            image_content = self._image_to_bytes(image)

            # Vision APIのImageオブジェクトを作成
            vision_image = self._vision.Image(content=image_content)

            # ImageContextを設定（言語ヒント）
            image_context = self._vision.ImageContext(language_hints=self.language_hints)

            # DOCUMENT_TEXT_DETECTIONを実行
            response = self.client.document_text_detection(
                image=vision_image,
                image_context=image_context
            )

            # エラーチェック
            if response.error.message:
                raise Exception(f"API Error: {response.error.message}")

            # 全文テキストを抽出
            full_text = ""
            if response.full_text_annotation:
                full_text = response.full_text_annotation.text

            # テキストブロックを抽出
            text_blocks = self._extract_text_blocks(response, image.width, image.height)

            # 平均信頼度を計算
            avg_confidence = self._calculate_average_confidence(response)

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
        return "google_vision"

    def is_available(self) -> bool:
        """エンジンが利用可能かチェック"""
        if self._available is not None:
            return self._available

        try:
            import google.cloud.vision

            # 認証情報の確認
            if self.credentials_path:
                credentials_path = Path(self.credentials_path)
                self._available = credentials_path.exists()
            else:
                # 環境変数またはデフォルト認証が設定されているか
                self._available = (
                    "GOOGLE_APPLICATION_CREDENTIALS" in os.environ or
                    self._check_default_credentials()
                )

            return self._available
        except ImportError:
            self._available = False
            return False

    def close(self) -> None:
        """リソースを解放"""
        if self.client is not None:
            # Vision APIクライアントは特別なクローズ処理は不要
            self.client = None
            self._initialized = False
            logger.info("Google Vision engine closed")

    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """
        PIL ImageをバイトデータにエンコードしてVision APIに送信

        Args:
            image: PIL Image

        Returns:
            bytes: エンコードされた画像データ
        """
        # PNGフォーマットでエンコード（ロスレス）
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr.read()

    def _extract_text_blocks(
        self,
        response,
        page_width: int,
        page_height: int
    ) -> List[TextBlock]:
        """
        Vision API レスポンスからテキストブロックを抽出

        Args:
            response: Vision API レスポンス
            page_width: ページ幅
            page_height: ページ高さ

        Returns:
            List[TextBlock]: テキストブロックのリスト
        """
        blocks = []

        try:
            if not response.full_text_annotation:
                return blocks

            # ページ内のブロックを解析
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    # ブロック内の全パラグラフのテキストを結合
                    block_text = ""
                    for paragraph in block.paragraphs:
                        para_text = ""
                        for word in paragraph.words:
                            word_text = "".join([symbol.text for symbol in word.symbols])
                            para_text += word_text
                        block_text += para_text + "\n"

                    block_text = block_text.strip()

                    # バウンディングボックスを取得
                    bbox = self._extract_bounding_box(block.bounding_box)

                    # 信頼度を取得（ブロックレベルでは提供されないことが多い）
                    confidence = getattr(block, 'confidence', 0.95)

                    # TextBlockオブジェクトを作成
                    text_block = TextBlock(
                        text=block_text,
                        bounding_box=bbox,
                        confidence=confidence,
                        block_type="text"
                    )
                    blocks.append(text_block)

        except Exception as e:
            logger.error(f"Failed to extract text blocks: {e}")

        return blocks

    def _extract_bounding_box(self, bounding_poly) -> BoundingBox:
        """
        BoundingPolyからBoundingBoxオブジェクトを作成

        Args:
            bounding_poly: Vision API BoundingPoly

        Returns:
            BoundingBox: バウンディングボックス
        """
        # 頂点から矩形の座標を計算
        vertices = bounding_poly.vertices

        if len(vertices) < 4:
            return BoundingBox(left=0, top=0, width=0, height=0, confidence=0.0)

        # 最小・最大座標を取得
        x_coords = [v.x for v in vertices]
        y_coords = [v.y for v in vertices]

        left = min(x_coords)
        top = min(y_coords)
        right = max(x_coords)
        bottom = max(y_coords)

        width = right - left
        height = bottom - top

        return BoundingBox(
            left=left,
            top=top,
            width=width,
            height=height,
            confidence=0.95
        )

    def _calculate_average_confidence(self, response) -> float:
        """
        平均信頼度を計算

        Vision APIは単語レベルでconfidenceを返さないことが多いため、
        デフォルト値を使用

        Args:
            response: Vision API レスポンス

        Returns:
            float: 平均信頼度
        """
        try:
            confidences = []

            if response.full_text_annotation:
                for page in response.full_text_annotation.pages:
                    if hasattr(page, 'confidence'):
                        confidences.append(page.confidence)

            if confidences:
                return sum(confidences) / len(confidences)

            # Google Vision APIは高精度なので、デフォルト値は高めに設定
            return 0.95

        except Exception as e:
            logger.error(f"Failed to calculate average confidence: {e}")
            return 0.95

    def _check_default_credentials(self) -> bool:
        """
        デフォルト認証情報が利用可能かチェック

        Returns:
            bool: デフォルト認証が利用可能な場合はTrue
        """
        try:
            from google.auth import default
            credentials, project = default()
            return credentials is not None
        except Exception:
            return False


# エンジンを登録
OCREngineFactory.register_engine("google_vision", GoogleVisionEngine)
