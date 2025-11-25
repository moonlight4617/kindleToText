"""
進捗管理モジュール

OCR処理の進捗を追跡し、表示する機能を提供します。
"""

from datetime import datetime, timedelta
from typing import Optional

from loguru import logger


class ProgressTracker:
    """
    進捗追跡クラス

    OCR処理の進捗を追跡し、残り時間を推定する機能を提供します。
    """

    def __init__(self, total_pages: int, start_page: int = 1):
        """
        初期化

        Args:
            total_pages: 総ページ数
            start_page: 開始ページ（デフォルト: 1）
        """
        self.total_pages = total_pages
        self.start_page = start_page
        # current_page は「処理済みの最後のページ番号」を表す
        # 初期状態ではまだ何も処理していないので start_page - 1
        self.current_page = start_page - 1
        self.start_time = datetime.now()
        self.last_update_time = datetime.now()
        self.page_times = []  # 各ページの処理時間を記録
        self.failed_pages = []
        logger.info(
            f"ProgressTracker initialized: total={total_pages}, start={start_page}"
        )

    def update_progress(self, page: int, failed: bool = False) -> None:
        """
        進捗を更新

        Args:
            page: 現在のページ番号
            failed: ページ処理が失敗した場合 True
        """
        now = datetime.now()
        page_time = (now - self.last_update_time).total_seconds()

        self.current_page = page
        self.last_update_time = now

        if not failed:
            self.page_times.append(page_time)
        else:
            self.failed_pages.append(page)

        logger.debug(
            f"Progress updated: page={page}, time={page_time:.2f}s, failed={failed}"
        )

    def get_progress_percentage(self) -> float:
        """
        進捗率を取得

        Returns:
            進捗率（0.0～100.0）
        """
        if self.total_pages == 0:
            return 0.0

        # current_page は「処理済みの最後のページ番号」を表す
        # 初期状態では start_page - 1 なので、処理済みページ数は 0
        pages_processed = max(0, self.current_page - self.start_page + 1)
        pages_total = self.total_pages - self.start_page + 1
        percentage = (pages_processed / pages_total) * 100.0
        return min(percentage, 100.0)

    def estimate_remaining_time(self) -> Optional[timedelta]:
        """
        残り時間を推定

        Returns:
            推定残り時間。推定できない場合は None
        """
        if not self.page_times:
            return None

        # 平均処理時間を計算
        avg_time_per_page = sum(self.page_times) / len(self.page_times)

        # 残りページ数を計算
        remaining_pages = self.total_pages - self.current_page

        if remaining_pages <= 0:
            return timedelta(0)

        # 残り時間を推定
        estimated_seconds = avg_time_per_page * remaining_pages
        return timedelta(seconds=estimated_seconds)

    def get_elapsed_time(self) -> timedelta:
        """
        経過時間を取得

        Returns:
            処理開始からの経過時間
        """
        return datetime.now() - self.start_time

    def get_average_page_time(self) -> Optional[float]:
        """
        平均ページ処理時間を取得

        Returns:
            平均処理時間（秒）。データがない場合は None
        """
        if not self.page_times:
            return None
        return sum(self.page_times) / len(self.page_times)

    def get_pages_per_minute(self) -> Optional[float]:
        """
        1分あたりの処理ページ数を取得

        Returns:
            1分あたりのページ数。データがない場合は None
        """
        avg_time = self.get_average_page_time()
        if avg_time is None or avg_time == 0:
            return None
        return 60.0 / avg_time

    def display_progress(self, verbose: bool = False) -> str:
        """
        進捗情報を表示用に整形

        Args:
            verbose: 詳細情報を含める場合 True

        Returns:
            表示用の進捗情報文字列
        """
        percentage = self.get_progress_percentage()
        elapsed = self.get_elapsed_time()
        remaining = self.estimate_remaining_time()

        # 基本情報
        lines = [
            f"Progress: {self.current_page}/{self.total_pages} pages "
            f"({percentage:.1f}%)",
            f"Elapsed: {self._format_timedelta(elapsed)}",
        ]

        # 残り時間
        if remaining is not None:
            lines.append(f"Remaining: {self._format_timedelta(remaining)}")
        else:
            lines.append("Remaining: Calculating...")

        # 詳細情報
        if verbose:
            avg_time = self.get_average_page_time()
            if avg_time is not None:
                lines.append(f"Avg time per page: {avg_time:.2f}s")

            pages_per_min = self.get_pages_per_minute()
            if pages_per_min is not None:
                lines.append(f"Pages per minute: {pages_per_min:.1f}")

            if self.failed_pages:
                lines.append(f"Failed pages: {len(self.failed_pages)}")

        return "\n".join(lines)

    def get_progress_bar(self, width: int = 50) -> str:
        """
        プログレスバーを生成

        Args:
            width: プログレスバーの幅（文字数）

        Returns:
            プログレスバー文字列
        """
        percentage = self.get_progress_percentage()
        filled = int(width * percentage / 100.0)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:.1f}%"

    def _format_timedelta(self, td: timedelta) -> str:
        """
        timedelta を読みやすい形式に整形

        Args:
            td: timedelta オブジェクト

        Returns:
            整形された時間文字列
        """
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def get_summary(self) -> dict:
        """
        進捗サマリーを取得

        Returns:
            進捗情報を含む辞書
        """
        return {
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "progress_percentage": self.get_progress_percentage(),
            "elapsed_time": str(self.get_elapsed_time()),
            "remaining_time": (
                str(self.estimate_remaining_time())
                if self.estimate_remaining_time()
                else None
            ),
            "average_page_time": self.get_average_page_time(),
            "pages_per_minute": self.get_pages_per_minute(),
            "failed_pages_count": len(self.failed_pages),
            "failed_pages": self.failed_pages,
        }

    def reset(self, new_start_page: Optional[int] = None) -> None:
        """
        進捗をリセット

        Args:
            new_start_page: 新しい開始ページ（指定しない場合は現在の start_page を使用）
        """
        if new_start_page is not None:
            self.start_page = new_start_page
        # 初期状態に戻す（まだ何も処理していない）
        self.current_page = self.start_page - 1
        self.start_time = datetime.now()
        self.last_update_time = datetime.now()
        self.page_times = []
        self.failed_pages = []
        logger.info(f"ProgressTracker reset: start_page={self.start_page}")
