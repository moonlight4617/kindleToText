"""
画像類似度判定モジュール

2つの画像が類似しているかを判定する機能を提供します。
"""

from PIL import Image
import imagehash
from typing import Optional
from loguru import logger


class ImageSimilarityChecker:
    """画像類似度を判定するクラス"""

    def __init__(self, hash_size: int = 16, similarity_threshold: int = 5):
        """
        初期化

        Args:
            hash_size: パーセプチュアルハッシュのサイズ（大きいほど精度が高い）
            similarity_threshold: 類似と判定するハミング距離の閾値（小さいほど厳密）
        """
        self.hash_size = hash_size
        self.similarity_threshold = similarity_threshold
        logger.debug(
            f"ImageSimilarityChecker initialized: "
            f"hash_size={hash_size}, similarity_threshold={similarity_threshold}"
        )

    def calculate_hash(self, image: Image.Image) -> imagehash.ImageHash:
        """
        画像のパーセプチュアルハッシュを計算

        Args:
            image: PIL Image オブジェクト

        Returns:
            imagehash.ImageHash: 画像のハッシュ値
        """
        # パーセプチュアルハッシュ（pHash）を使用
        # 画像の視覚的特徴を数値化し、わずかな違いに強い
        return imagehash.phash(image, hash_size=self.hash_size)

    def are_images_similar(
        self,
        image1: Image.Image,
        image2: Image.Image
    ) -> bool:
        """
        2つの画像が類似しているか判定

        Args:
            image1: 1つ目の画像
            image2: 2つ目の画像

        Returns:
            bool: 類似している場合はTrue
        """
        hash1 = self.calculate_hash(image1)
        hash2 = self.calculate_hash(image2)

        # ハミング距離を計算（異なるビット数）
        hamming_distance = hash1 - hash2

        # 閾値以下なら類似と判定
        is_similar = hamming_distance <= self.similarity_threshold

        logger.debug(
            f"Image similarity check: hamming_distance={hamming_distance}, "
            f"threshold={self.similarity_threshold}, similar={is_similar}"
        )

        return is_similar

    def calculate_similarity_score(
        self,
        image1: Image.Image,
        image2: Image.Image
    ) -> float:
        """
        2つの画像の類似度スコアを計算（0.0-1.0）

        Args:
            image1: 1つ目の画像
            image2: 2つ目の画像

        Returns:
            float: 類似度スコア（1.0が完全一致、0.0が完全不一致）
        """
        hash1 = self.calculate_hash(image1)
        hash2 = self.calculate_hash(image2)

        hamming_distance = hash1 - hash2
        max_distance = self.hash_size ** 2  # 最大ハミング距離

        # スコアを0-1の範囲に正規化
        similarity = 1.0 - (hamming_distance / max_distance)

        logger.debug(f"Similarity score calculated: {similarity:.4f}")

        return similarity
