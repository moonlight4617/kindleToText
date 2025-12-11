"""
最終ページ検出モジュール

連続して同じページが検出されたら最終ページと判断します。
"""

from PIL import Image
from typing import Optional, List
from collections import deque
from loguru import logger

from .image_similarity import ImageSimilarityChecker


class EndPageDetector:
    """最終ページを検出するクラス"""

    def __init__(
        self,
        consecutive_same_pages: int = 3,
        similarity_threshold: int = 5
    ):
        """
        初期化

        Args:
            consecutive_same_pages: 連続して同じページと判定する回数
            similarity_threshold: 画像類似度の閾値
        """
        self.consecutive_same_pages = consecutive_same_pages
        self.similarity_checker = ImageSimilarityChecker(
            hash_size=16,
            similarity_threshold=similarity_threshold
        )

        # 最近のページ画像を保持するキュー（メモリ効率のため）
        self.recent_images: deque = deque(maxlen=consecutive_same_pages)
        self.same_page_count = 0

        logger.info(
            f"EndPageDetector initialized: "
            f"consecutive_same_pages={consecutive_same_pages}, "
            f"similarity_threshold={similarity_threshold}"
        )

    def check_page(self, image: Image.Image) -> bool:
        """
        ページをチェックして、最終ページに到達したか判定

        Args:
            image: チェックする画像

        Returns:
            bool: 最終ページに到達した場合はTrue
        """
        # 最初のページの場合
        if len(self.recent_images) == 0:
            self.recent_images.append(image.copy())
            self.same_page_count = 0
            logger.debug("First page recorded")
            return False

        # 直前のページと比較
        previous_image = self.recent_images[-1]
        is_similar = self.similarity_checker.are_images_similar(
            previous_image, image
        )

        if is_similar:
            # 同じページが続いている
            self.same_page_count += 1
            logger.debug(
                f"Same page detected: count={self.same_page_count}/"
                f"{self.consecutive_same_pages}"
            )

            # 規定回数連続で同じページなら最終ページと判定
            # 注: 最初のページは記録時にcount=0、2回目でcount=1、3回目でcount=2
            # したがって3回連続には count >= consecutive_same_pages - 1 で判定
            if self.same_page_count >= (self.consecutive_same_pages - 1):
                logger.info(
                    f"End page detected: {self.consecutive_same_pages} "
                    f"consecutive same pages found"
                )
                return True
        else:
            # 異なるページ：カウントをリセット
            if self.same_page_count > 0:
                logger.debug(
                    f"Different page detected, resetting count from {self.same_page_count}"
                )
            self.same_page_count = 0
            self.recent_images.append(image.copy())

        return False

    def reset(self):
        """検出器の状態をリセット"""
        self.recent_images.clear()
        self.same_page_count = 0
        logger.debug("EndPageDetector reset")

    def get_similarity_score(self, image: Image.Image) -> Optional[float]:
        """
        直前のページとの類似度スコアを取得

        Args:
            image: チェックする画像

        Returns:
            float: 類似度スコア（0.0-1.0）。直前のページがない場合はNone
        """
        if len(self.recent_images) == 0:
            return None

        previous_image = self.recent_images[-1]
        return self.similarity_checker.calculate_similarity_score(
            previous_image, image
        )

    def get_current_count(self) -> int:
        """
        現在の連続同一ページカウントを取得

        Returns:
            int: 連続同一ページカウント
        """
        return self.same_page_count
