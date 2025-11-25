"""
State モジュールの統合テスト
"""

import tempfile
import time
from pathlib import Path

import pytest

from src.state import ProgressTracker, StateData, StateManager


class TestStateIntegration:
    """State モジュールの統合テスト"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def state_manager(self, temp_dir):
        """StateManager インスタンスを作成"""
        return StateManager(state_dir=temp_dir)

    def test_full_workflow(self, state_manager):
        """完全なワークフローテスト"""
        # 1. 初期状態を作成
        initial_state = state_manager.create_initial_state(
            book_title="Integration Test Book",
            total_pages=10,
            output_file="output/test.txt",
            screenshot_dir="output/screenshots",
            start_page=1,
        )

        assert initial_state.current_page == 1
        assert initial_state.status == "in_progress"

        # 2. 状態を保存
        result = state_manager.save_state(initial_state)
        assert result is True

        # 3. 状態を読み込み
        loaded_state = state_manager.load_state("Integration Test Book")
        assert loaded_state is not None
        assert loaded_state.book_title == "Integration Test Book"

        # 4. 進捗を更新
        time.sleep(0.01)
        updates = {
            "current_page": 5,
            "processed_pages": [1, 2, 3, 4, 5],
        }
        updated_state = state_manager.update_state(loaded_state, updates)

        # 5. 更新された状態を保存
        state_manager.save_state(updated_state)

        # 6. 再開可能か確認
        can_resume = state_manager.can_resume("Integration Test Book")
        assert can_resume is True

        # 7. さらに進捗を更新して完了
        time.sleep(0.01)
        completed_updates = {
            "current_page": 10,
            "processed_pages": list(range(1, 11)),
            "status": "completed",
        }
        completed_state = state_manager.update_state(updated_state, completed_updates)
        state_manager.save_state(completed_state)

        # 8. 完了状態では再開不可
        can_resume = state_manager.can_resume("Integration Test Book")
        assert can_resume is False

        # 9. 状態を削除
        delete_result = state_manager.delete_state("Integration Test Book")
        assert delete_result is True

        # 10. 削除後は読み込めない
        deleted_state = state_manager.load_state("Integration Test Book")
        assert deleted_state is None

    def test_progress_tracker_with_state_manager(self, state_manager):
        """ProgressTracker と StateManager の統合テスト"""
        # 初期状態を作成
        initial_state = state_manager.create_initial_state(
            book_title="Progress Test Book",
            total_pages=20,
            output_file="output/progress_test.txt",
            screenshot_dir="output/screenshots_progress",
            start_page=1,
        )

        # ProgressTracker を作成
        tracker = ProgressTracker(total_pages=20, start_page=1)

        # ページを処理しながら状態を更新
        processed_pages = []
        for page in range(1, 11):
            time.sleep(0.001)  # ページ処理をシミュレート
            tracker.update_progress(page)
            processed_pages.append(page)

            # 状態を更新
            updates = {
                "current_page": page,
                "processed_pages": processed_pages.copy(),
            }
            initial_state = state_manager.update_state(initial_state, updates)

        # 進捗確認
        assert tracker.current_page == 10
        assert tracker.get_progress_percentage() == 50.0  # 10/20 = 50%

        # 状態を保存
        state_manager.save_state(initial_state)

        # 状態を読み込んで確認
        loaded_state = state_manager.load_state("Progress Test Book")
        assert loaded_state is not None
        assert loaded_state.current_page == 10
        assert len(loaded_state.processed_pages) == 10

        # 進捗を復元
        restored_tracker = ProgressTracker(
            total_pages=loaded_state.total_pages, start_page=1
        )
        restored_tracker.current_page = loaded_state.current_page
        restored_tracker.page_times = [1.0] * len(loaded_state.processed_pages)

        # 復元された進捗を確認
        assert restored_tracker.get_progress_percentage() == 50.0

    def test_resume_workflow(self, state_manager):
        """処理の中断・再開ワークフローテスト"""
        # 1. 処理を開始
        state = state_manager.create_initial_state(
            book_title="Resume Test Book",
            total_pages=50,
            output_file="output/resume_test.txt",
            screenshot_dir="output/screenshots_resume",
            start_page=1,
        )

        tracker = ProgressTracker(total_pages=50, start_page=1)

        # 2. 途中まで処理
        processed_pages = []
        for page in range(1, 21):
            time.sleep(0.001)
            tracker.update_progress(page)
            processed_pages.append(page)

        # 3. 状態を保存（中断をシミュレート）
        updates = {
            "current_page": 20,
            "processed_pages": processed_pages.copy(),
        }
        state = state_manager.update_state(state, updates)
        state_manager.save_state(state)

        # 4. 再開可能か確認
        assert state_manager.can_resume("Resume Test Book") is True

        # 5. 状態を読み込んで再開
        resumed_state = state_manager.load_state("Resume Test Book")
        assert resumed_state is not None

        # 6. ProgressTracker を再作成
        resumed_tracker = ProgressTracker(
            total_pages=resumed_state.total_pages, start_page=1
        )
        resumed_tracker.current_page = resumed_state.current_page
        resumed_tracker.page_times = [1.0] * len(resumed_state.processed_pages)

        # 7. 残りのページを処理
        for page in range(21, 51):
            time.sleep(0.001)
            resumed_tracker.update_progress(page)
            processed_pages.append(page)

        # 8. 最終状態を保存
        final_updates = {
            "current_page": 50,
            "processed_pages": processed_pages.copy(),
            "status": "completed",
        }
        final_state = state_manager.update_state(resumed_state, final_updates)
        state_manager.save_state(final_state)

        # 9. 完了確認
        assert final_state.status == "completed"
        assert len(final_state.processed_pages) == 50

    def test_failed_pages_tracking(self, state_manager):
        """失敗ページの追跡テスト"""
        # 初期状態を作成
        state = state_manager.create_initial_state(
            book_title="Failed Pages Test",
            total_pages=30,
            output_file="output/failed_test.txt",
            screenshot_dir="output/screenshots_failed",
            start_page=1,
        )

        tracker = ProgressTracker(total_pages=30, start_page=1)

        # ページを処理（一部は失敗）
        processed_pages = []
        failed_pages = []

        for page in range(1, 31):
            time.sleep(0.001)
            # 5の倍数は失敗とする
            if page % 5 == 0:
                tracker.update_progress(page, failed=True)
                failed_pages.append(page)
            else:
                tracker.update_progress(page, failed=False)
                processed_pages.append(page)

        # 状態を更新
        updates = {
            "current_page": 30,
            "processed_pages": processed_pages.copy(),
            "failed_pages": failed_pages.copy(),
            "status": "completed",
        }
        state = state_manager.update_state(state, updates)
        state_manager.save_state(state)

        # 確認
        assert len(state.processed_pages) == 24  # 30 - 6 (5の倍数)
        assert len(state.failed_pages) == 6
        assert tracker.failed_pages == failed_pages

    def test_multiple_books_management(self, state_manager):
        """複数の書籍の状態管理テスト"""
        # 複数の書籍の状態を作成
        books = [
            ("Book A", 100),
            ("Book B", 200),
            ("Book C", 150),
        ]

        for book_title, total_pages in books:
            state = state_manager.create_initial_state(
                book_title=book_title,
                total_pages=total_pages,
                output_file=f"output/{book_title}.txt",
                screenshot_dir=f"output/screenshots_{book_title}",
                start_page=1,
            )
            state_manager.save_state(state)

        # 全ての状態を一覧取得
        all_states = state_manager.list_states()
        assert len(all_states) == 3

        # 各書籍の状態を確認
        titles = [s.book_title for s in all_states]
        assert "Book A" in titles
        assert "Book B" in titles
        assert "Book C" in titles

        # 個別に読み込み確認
        state_a = state_manager.load_state("Book A")
        assert state_a is not None
        assert state_a.total_pages == 100

    def test_progress_summary(self):
        """進捗サマリーの詳細テスト"""
        tracker = ProgressTracker(total_pages=100, start_page=1)

        # いくつかのページを処理
        for page in range(1, 31):
            time.sleep(0.001)
            if page in [5, 15, 25]:
                tracker.update_progress(page, failed=True)
            else:
                tracker.update_progress(page, failed=False)

        # サマリーを取得
        summary = tracker.get_summary()

        assert summary["current_page"] == 30
        assert summary["total_pages"] == 100
        assert summary["progress_percentage"] == 30.0
        assert summary["failed_pages_count"] == 3
        assert summary["average_page_time"] is not None
        assert summary["pages_per_minute"] is not None

    def test_state_persistence(self, state_manager):
        """状態の永続化テスト"""
        # 複雑な状態を作成
        state = state_manager.create_initial_state(
            book_title="Persistence Test",
            total_pages=100,
            output_file="output/persistence.txt",
            screenshot_dir="output/screenshots_persistence",
            start_page=1,
        )

        # 状態を何度も更新・保存
        for i in range(1, 11):
            time.sleep(0.001)
            updates = {
                "current_page": i * 10,
                "processed_pages": list(range(1, i * 10 + 1)),
            }
            state = state_manager.update_state(state, updates)
            state_manager.save_state(state)

        # 最終状態を読み込み
        final_state = state_manager.load_state("Persistence Test")

        assert final_state is not None
        assert final_state.current_page == 100
        assert len(final_state.processed_pages) == 100
