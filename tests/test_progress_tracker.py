"""
ProgressTracker モジュールのユニットテスト
"""

import time
from datetime import timedelta

import pytest

from src.state.progress_tracker import ProgressTracker


class TestProgressTracker:
    """ProgressTracker クラスのテスト"""

    @pytest.fixture
    def tracker(self):
        """ProgressTracker インスタンスを作成"""
        return ProgressTracker(total_pages=100, start_page=1)

    def test_init(self, tracker):
        """初期化テスト"""
        assert tracker.total_pages == 100
        assert tracker.start_page == 1
        assert tracker.current_page == 0  # 初期状態では start_page - 1
        assert tracker.page_times == []
        assert tracker.failed_pages == []

    def test_init_with_custom_start_page(self):
        """カスタム開始ページでの初期化テスト"""
        tracker = ProgressTracker(total_pages=100, start_page=10)
        assert tracker.start_page == 10
        assert tracker.current_page == 9  # 初期状態では start_page - 1

    def test_update_progress(self, tracker):
        """進捗更新テスト"""
        # 少し待機して時間を経過させる
        time.sleep(0.01)
        tracker.update_progress(2)

        assert tracker.current_page == 2
        assert len(tracker.page_times) == 1
        assert tracker.page_times[0] > 0

    def test_update_progress_failed(self, tracker):
        """失敗ページの進捗更新テスト"""
        tracker.update_progress(2, failed=True)

        assert tracker.current_page == 2
        assert len(tracker.page_times) == 0  # 失敗時は記録されない
        assert 2 in tracker.failed_pages

    def test_get_progress_percentage_start(self, tracker):
        """開始時の進捗率テスト"""
        percentage = tracker.get_progress_percentage()
        assert percentage == 0.0

    def test_get_progress_percentage_middle(self, tracker):
        """途中の進捗率テスト"""
        tracker.current_page = 50
        percentage = tracker.get_progress_percentage()
        # 50ページ処理済み = 50/100 = 50%
        assert percentage == pytest.approx(50.0, abs=0.1)

    def test_get_progress_percentage_end(self, tracker):
        """終了時の進捗率テスト"""
        tracker.current_page = 100
        percentage = tracker.get_progress_percentage()
        assert percentage == 100.0

    def test_get_progress_percentage_over_100(self, tracker):
        """100%を超える進捗率テスト"""
        tracker.current_page = 150
        percentage = tracker.get_progress_percentage()
        assert percentage == 100.0  # 100.0 を超えないことを確認

    def test_get_progress_percentage_zero_total(self):
        """総ページ数0の場合の進捗率テスト"""
        tracker = ProgressTracker(total_pages=0)
        percentage = tracker.get_progress_percentage()
        assert percentage == 0.0

    def test_estimate_remaining_time_no_data(self, tracker):
        """データなしの場合の残り時間推定テスト"""
        remaining = tracker.estimate_remaining_time()
        assert remaining is None

    def test_estimate_remaining_time_with_data(self, tracker):
        """データありの場合の残り時間推定テスト"""
        # ページ処理時間をシミュレート
        tracker.page_times = [1.0, 1.0, 1.0]  # 平均1秒/ページ
        tracker.current_page = 3

        remaining = tracker.estimate_remaining_time()

        assert remaining is not None
        # 残り97ページ × 1秒/ページ = 97秒
        assert remaining.total_seconds() == pytest.approx(97.0, abs=1.0)

    def test_estimate_remaining_time_completed(self, tracker):
        """完了時の残り時間推定テスト"""
        tracker.page_times = [1.0, 1.0]
        tracker.current_page = 100

        remaining = tracker.estimate_remaining_time()

        assert remaining is not None
        assert remaining.total_seconds() == 0.0

    def test_get_elapsed_time(self, tracker):
        """経過時間取得テスト"""
        time.sleep(0.01)
        elapsed = tracker.get_elapsed_time()

        assert isinstance(elapsed, timedelta)
        assert elapsed.total_seconds() > 0

    def test_get_average_page_time_no_data(self, tracker):
        """データなしの場合の平均処理時間テスト"""
        avg_time = tracker.get_average_page_time()
        assert avg_time is None

    def test_get_average_page_time_with_data(self, tracker):
        """データありの場合の平均処理時間テスト"""
        tracker.page_times = [1.0, 2.0, 3.0]
        avg_time = tracker.get_average_page_time()

        assert avg_time == 2.0

    def test_get_pages_per_minute_no_data(self, tracker):
        """データなしの場合のページ数/分テスト"""
        ppm = tracker.get_pages_per_minute()
        assert ppm is None

    def test_get_pages_per_minute_with_data(self, tracker):
        """データありの場合のページ数/分テスト"""
        tracker.page_times = [1.0, 1.0, 1.0]  # 1秒/ページ
        ppm = tracker.get_pages_per_minute()

        assert ppm == 60.0  # 60ページ/分

    def test_get_pages_per_minute_zero_time(self, tracker):
        """処理時間0の場合のページ数/分テスト"""
        tracker.page_times = [0.0]
        ppm = tracker.get_pages_per_minute()

        assert ppm is None

    def test_display_progress_basic(self, tracker):
        """基本的な進捗表示テスト"""
        tracker.current_page = 50
        tracker.page_times = [1.0] * 49

        display = tracker.display_progress()

        assert "50/100" in display
        assert "%" in display
        assert "Elapsed:" in display
        assert "Remaining:" in display

    def test_display_progress_verbose(self, tracker):
        """詳細進捗表示テスト"""
        tracker.current_page = 50
        tracker.page_times = [1.0] * 49

        display = tracker.display_progress(verbose=True)

        assert "Avg time per page:" in display
        assert "Pages per minute:" in display

    def test_display_progress_with_failed_pages(self, tracker):
        """失敗ページありの進捗表示テスト"""
        tracker.current_page = 50
        tracker.page_times = [1.0] * 47
        tracker.failed_pages = [5, 10, 15]

        display = tracker.display_progress(verbose=True)

        assert "Failed pages: 3" in display

    def test_get_progress_bar(self, tracker):
        """プログレスバー生成テスト"""
        tracker.current_page = 50
        bar = tracker.get_progress_bar(width=10)

        assert "[" in bar
        assert "]" in bar
        assert "%" in bar
        assert "█" in bar or "░" in bar

    def test_get_progress_bar_empty(self, tracker):
        """空のプログレスバーテスト"""
        bar = tracker.get_progress_bar(width=10)

        # 初期状態（current_page=0）では 0% なので全て空
        assert bar.count("░") == 10

    def test_get_progress_bar_full(self, tracker):
        """満杯のプログレスバーテスト"""
        tracker.current_page = 100
        bar = tracker.get_progress_bar(width=10)

        # 100ページ処理済みで 100% なので全て埋まる
        assert bar.count("█") == 10

    def test_format_timedelta_seconds(self, tracker):
        """秒単位の時間フォーマットテスト"""
        td = timedelta(seconds=30)
        formatted = tracker._format_timedelta(td)

        assert formatted == "30s"

    def test_format_timedelta_minutes(self, tracker):
        """分単位の時間フォーマットテスト"""
        td = timedelta(minutes=5, seconds=30)
        formatted = tracker._format_timedelta(td)

        assert formatted == "5m 30s"

    def test_format_timedelta_hours(self, tracker):
        """時間単位の時間フォーマットテスト"""
        td = timedelta(hours=2, minutes=30, seconds=45)
        formatted = tracker._format_timedelta(td)

        assert formatted == "2h 30m 45s"

    def test_get_summary(self, tracker):
        """サマリー取得テスト"""
        tracker.current_page = 50
        tracker.page_times = [1.0] * 49

        summary = tracker.get_summary()

        assert isinstance(summary, dict)
        assert summary["current_page"] == 50
        assert summary["total_pages"] == 100
        assert summary["progress_percentage"] > 0
        assert summary["elapsed_time"] is not None
        assert summary["average_page_time"] == 1.0
        assert summary["failed_pages_count"] == 0

    def test_get_summary_with_failed_pages(self, tracker):
        """失敗ページありのサマリー取得テスト"""
        tracker.failed_pages = [5, 10, 15]

        summary = tracker.get_summary()

        assert summary["failed_pages_count"] == 3
        assert summary["failed_pages"] == [5, 10, 15]

    def test_reset(self, tracker):
        """リセットテスト"""
        # 進捗を進める
        tracker.current_page = 50
        tracker.page_times = [1.0] * 49
        tracker.failed_pages = [5, 10]

        # リセット
        tracker.reset()

        assert tracker.current_page == 0  # start_page - 1
        assert tracker.page_times == []
        assert tracker.failed_pages == []

    def test_reset_with_new_start_page(self, tracker):
        """新しい開始ページでのリセットテスト"""
        tracker.current_page = 50
        tracker.page_times = [1.0] * 49

        tracker.reset(new_start_page=10)

        assert tracker.start_page == 10
        assert tracker.current_page == 9  # start_page - 1
        assert tracker.page_times == []

    def test_multiple_progress_updates(self, tracker):
        """複数回の進捗更新テスト"""
        for i in range(1, 11):
            time.sleep(0.001)
            tracker.update_progress(i)

        assert tracker.current_page == 10
        assert len(tracker.page_times) == 10

    def test_mixed_success_and_failure(self, tracker):
        """成功と失敗が混在する進捗更新テスト"""
        tracker.update_progress(1, failed=False)
        tracker.update_progress(2, failed=True)
        tracker.update_progress(3, failed=False)
        tracker.update_progress(4, failed=True)

        assert tracker.current_page == 4
        assert len(tracker.page_times) == 2  # 成功のみカウント
        assert len(tracker.failed_pages) == 2  # 失敗のみカウント
        assert tracker.failed_pages == [2, 4]
