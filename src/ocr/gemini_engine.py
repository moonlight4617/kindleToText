"""
Gemini AI OCRエンジン実装

このモジュールは、Google Gemini APIを使用した
AI駆動の高精度なテキスト抽出機能を提供します。
"""

import os
import time
import base64
from typing import Optional
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


class GeminiEngine(OCRInterface):
    """
    Gemini AI OCRエンジン

    Google Gemini APIを使用したAI駆動のテキスト認識エンジン
    自然言語処理能力を活用した高精度な日本語認識
    """

    def __init__(self, config: Optional[dict] = None):
        """
        GeminiEngineの初期化

        Args:
            config: エンジン設定（geminiサブセクションまたは完全なOCR設定）
                - api_key: Gemini APIキー（nullの場合は環境変数を使用）
                - model: 使用するモデル名（デフォルト: gemini-1.5-flash）
                - temperature: 生成の温度パラメータ（0.0-1.0）
                - max_output_tokens: 最大出力トークン数
                - prompt_template: テキスト抽出用のプロンプトテンプレート
        """
        self.config = config or {}

        # If config contains 'gemini' key, extract it (called from main.py with full OCR config)
        # Otherwise, assume config is already the gemini subsection (called from test scripts)
        if 'gemini' in self.config:
            gemini_config = self.config.get('gemini', {})
        else:
            gemini_config = self.config

        self.api_key = gemini_config.get("api_key")
        # モデル名: models/ プレフィックスが必要
        # 利用可能: models/gemini-2.5-flash, models/gemini-flash-latest など
        raw_model = gemini_config.get("model", "gemini-2.5-flash")
        # models/ プレフィックスがない場合は追加
        self.model_name = raw_model if raw_model.startswith("models/") else f"models/{raw_model}"
        self.temperature = gemini_config.get("temperature", 0.0)
        self.max_output_tokens = gemini_config.get("max_output_tokens", 8192)
        self.prompt_template = gemini_config.get(
            "prompt_template",
            """この画像は書籍のページです。
画像内のすべてのテキストを正確に抽出してください。

要件:
- 日本語の文字を正確に認識
- レイアウトや段落構造を保持
- 特殊文字や記号も含める
- テキストのみを出力し、説明や注釈は不要"""
        )

        self.model = None
        self._initialized = False
        self._available = None

        logger.info(
            f"GeminiEngine created: model={self.model_name}, "
            f"temperature={self.temperature}"
        )

    def initialize(self) -> bool:
        """
        Gemini API クライアントを初期化する

        Returns:
            bool: 初期化に成功した場合はTrue
        """
        try:
            logger.info("Initializing Gemini API client...")

            # Gemini SDKをインポート
            try:
                import google.generativeai as genai
                self._genai = genai
            except ImportError:
                logger.error(
                    "google-generativeai is not installed. "
                    "Please install it: pip install google-generativeai"
                )
                return False

            # APIキーの設定
            api_key = self.api_key or os.environ.get("GEMINI_API_KEY")
            if not api_key:
                logger.error(
                    "No API key specified. Please set api_key in config or "
                    "GEMINI_API_KEY environment variable."
                )
                return False

            # APIキーを設定
            self._genai.configure(api_key=api_key)

            # モデルの設定
            generation_config = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
            }

            self.model = self._genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config
            )

            self._initialized = True
            logger.info(f"Gemini API client initialized successfully with model: {self.model_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
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
            logger.warning("Gemini not initialized, attempting to initialize...")
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
            logger.debug("Starting text extraction with Gemini API...")

            # 画像とプロンプトを送信
            response = self.model.generate_content([
                self.prompt_template,
                image
            ])

            # レスポンスを取得
            if not response:
                raise Exception("No response from Gemini API")

            extracted_text = response.text.strip() if response.text else ""

            # Gemini APIは信頼度を返さないため、仮の値を設定
            # テキストが抽出できた場合は高い信頼度とする
            avg_confidence = 0.95 if extracted_text else 0.0

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

        Note: Gemini APIはレイアウト情報を直接提供しないため、
        テキスト抽出のみを行います。将来的にはプロンプトエンジニアリングで
        レイアウト情報も抽出可能になる可能性があります。

        Args:
            image: 入力画像

        Returns:
            OCRResult: OCR結果（レイアウト情報は簡易版）
        """
        # 基本的なテキスト抽出を実行
        result = self.extract_text(image)

        if result.success:
            # 簡易的なレイアウトデータを作成
            # 全テキストを単一ブロックとして扱う
            bbox = BoundingBox(
                left=0,
                top=0,
                width=image.width,
                height=image.height,
                confidence=result.confidence
            )

            text_block = TextBlock(
                text=result.text,
                bounding_box=bbox,
                confidence=result.confidence,
                block_type="text"
            )

            layout = LayoutData(
                full_text=result.text,
                blocks=[text_block],
                page_width=image.width,
                page_height=image.height,
                language="jpn",
                average_confidence=result.confidence
            )

            result.layout = layout

        return result

    def get_engine_name(self) -> str:
        """エンジン名を取得"""
        return "gemini"

    def is_available(self) -> bool:
        """エンジンが利用可能かチェック"""
        if self._available is not None:
            return self._available

        try:
            import google.generativeai

            # APIキーの確認
            api_key = self.api_key or os.environ.get("GEMINI_API_KEY")
            self._available = api_key is not None and len(api_key) > 0

            return self._available
        except ImportError:
            self._available = False
            return False

    def close(self) -> None:
        """リソースを解放"""
        if self.model is not None:
            # Gemini APIクライアントは特別なクローズ処理は不要
            self.model = None
            self._initialized = False
            logger.info("Gemini engine closed")


# エンジンを登録
OCREngineFactory.register_engine("gemini", GeminiEngine)
