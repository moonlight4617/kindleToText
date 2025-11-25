"""
StateManager モジュールのユニットテスト
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.state.state_manager import StateData, StateManager


class TestStateData:
    """StateData クラスのテスト"""

    def test_create_state_data(self):
        """StateData の作成テスト"""
        now = datetime.now().isoformat()
        state = StateData(
            book_title="Test Book",
            start_datetime=now,
            last_update=now,
            current_page=1,
            total_pages=100,
            processed_pages=[],
            failed_pages=[],
            output_file="output/test.txt",
            screenshot_dir="output/screenshots",
            status="in_progress",
        )

        assert state.book_title == "Test Book"
        assert state.current_page == 1
        assert state.total_pages == 100
        assert state.status == "in_progress"

    def test_to_dict(self):
        """to_dict メソッドのテスト"""
        now = datetime.now().isoformat()
        state = StateData(
            book_title="Test Book",
            start_datetime=now,
            last_update=now,
            current_page=1,
            total_pages=100,
            processed_pages=[1, 2, 3],
            failed_pages=[4],
            output_file="output/test.txt",
            screenshot_dir="output/screenshots",
            status="in_progress",
        )

        state_dict = state.to_dict()

        assert isinstance(state_dict, dict)
        assert state_dict["book_title"] == "Test Book"
        assert state_dict["current_page"] == 1
        assert state_dict["processed_pages"] == [1, 2, 3]
        assert state_dict["failed_pages"] == [4]

    def test_from_dict(self):
        """from_dict メソッドのテスト"""
        now = datetime.now().isoformat()
        data = {
            "book_title": "Test Book",
            "start_datetime": now,
            "last_update": now,
            "current_page": 1,
            "total_pages": 100,
            "processed_pages": [1, 2, 3],
            "failed_pages": [4],
            "output_file": "output/test.txt",
            "screenshot_dir": "output/screenshots",
            "status": "in_progress",
        }

        state = StateData.from_dict(data)

        assert state.book_title == "Test Book"
        assert state.current_page == 1
        assert state.processed_pages == [1, 2, 3]
        assert state.failed_pages == [4]


class TestStateManager:
    """StateManager クラスのテスト"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def state_manager(self, temp_dir):
        """StateManager インスタンスを作成"""
        return StateManager(state_dir=temp_dir)

    @pytest.fixture
    def sample_state(self):
        """サンプル StateData を作成"""
        now = datetime.now().isoformat()
        return StateData(
            book_title="Test Book",
            start_datetime=now,
            last_update=now,
            current_page=1,
            total_pages=100,
            processed_pages=[],
            failed_pages=[],
            output_file="output/test.txt",
            screenshot_dir="output/screenshots",
            status="in_progress",
        )

    def test_init(self, temp_dir):
        """初期化テスト"""
        manager = StateManager(state_dir=temp_dir)
        assert manager.state_dir == Path(temp_dir)
        assert manager.state_dir.exists()

    def test_get_state_file_path(self, state_manager):
        """状態ファイルパス取得テスト"""
        path = state_manager.get_state_file_path("Test Book")
        assert path.name == "Test_Book_state.json"

    def test_get_state_file_path_with_special_chars(self, state_manager):
        """特殊文字を含むタイトルのファイルパス取得テスト"""
        path = state_manager.get_state_file_path("Test/Book:Name*?")
        assert path.name == "Test_Book_Name___state.json"

    def test_save_state(self, state_manager, sample_state):
        """状態保存テスト"""
        result = state_manager.save_state(sample_state)
        assert result is True

        # ファイルが作成されたことを確認
        file_path = state_manager.get_state_file_path(sample_state.book_title)
        assert file_path.exists()

    def test_load_state(self, state_manager, sample_state):
        """状態読み込みテスト"""
        # 保存
        state_manager.save_state(sample_state)

        # 読み込み
        loaded_state = state_manager.load_state(sample_state.book_title)

        assert loaded_state is not None
        assert loaded_state.book_title == sample_state.book_title
        assert loaded_state.current_page == sample_state.current_page
        assert loaded_state.total_pages == sample_state.total_pages

    def test_load_state_not_found(self, state_manager):
        """存在しない状態の読み込みテスト"""
        loaded_state = state_manager.load_state("Non Existent Book")
        assert loaded_state is None

    def test_update_state(self, state_manager, sample_state):
        """状態更新テスト"""
        import time

        updates = {"current_page": 10, "processed_pages": [1, 2, 3, 4, 5]}

        # 時間を少し待機して last_update が確実に異なるようにする
        time.sleep(0.01)
        updated_state = state_manager.update_state(sample_state, updates)

        assert updated_state.current_page == 10
        assert updated_state.processed_pages == [1, 2, 3, 4, 5]
        # last_update が更新されていることを確認
        assert updated_state.last_update != sample_state.last_update

    def test_update_state_with_invalid_key(self, state_manager, sample_state):
        """無効なキーでの状態更新テスト"""
        updates = {"invalid_key": "value"}

        updated_state = state_manager.update_state(sample_state, updates)

        # 無効なキーは無視され、元の状態が保持される
        assert updated_state.book_title == sample_state.book_title

    def test_can_resume_true(self, state_manager, sample_state):
        """再開可能判定テスト（True）"""
        # 進行中の状態を保存
        sample_state.status = "in_progress"
        sample_state.current_page = 50
        state_manager.save_state(sample_state)

        result = state_manager.can_resume(sample_state.book_title)
        assert result is True

    def test_can_resume_false_completed(self, state_manager, sample_state):
        """再開可能判定テスト（完了状態で False）"""
        # 完了状態を保存
        sample_state.status = "completed"
        sample_state.current_page = 100
        state_manager.save_state(sample_state)

        result = state_manager.can_resume(sample_state.book_title)
        assert result is False

    def test_can_resume_false_all_pages_processed(self, state_manager, sample_state):
        """再開可能判定テスト（全ページ処理済みで False）"""
        # 全ページ処理済みの状態を保存
        sample_state.status = "in_progress"
        sample_state.current_page = 100
        state_manager.save_state(sample_state)

        result = state_manager.can_resume(sample_state.book_title)
        assert result is False

    def test_can_resume_false_no_state(self, state_manager):
        """再開可能判定テスト（状態なしで False）"""
        result = state_manager.can_resume("Non Existent Book")
        assert result is False

    def test_delete_state(self, state_manager, sample_state):
        """状態ファイル削除テスト"""
        # 保存
        state_manager.save_state(sample_state)

        # 削除
        result = state_manager.delete_state(sample_state.book_title)
        assert result is True

        # ファイルが削除されたことを確認
        file_path = state_manager.get_state_file_path(sample_state.book_title)
        assert not file_path.exists()

    def test_delete_state_not_found(self, state_manager):
        """存在しない状態ファイルの削除テスト"""
        result = state_manager.delete_state("Non Existent Book")
        assert result is False

    def test_list_states(self, state_manager):
        """状態一覧取得テスト"""
        # 複数の状態を保存
        now = datetime.now().isoformat()
        state1 = StateData(
            book_title="Book 1",
            start_datetime=now,
            last_update=now,
            current_page=1,
            total_pages=100,
            processed_pages=[],
            failed_pages=[],
            output_file="output/book1.txt",
            screenshot_dir="output/screenshots1",
            status="in_progress",
        )
        state2 = StateData(
            book_title="Book 2",
            start_datetime=now,
            last_update=now,
            current_page=1,
            total_pages=200,
            processed_pages=[],
            failed_pages=[],
            output_file="output/book2.txt",
            screenshot_dir="output/screenshots2",
            status="in_progress",
        )

        state_manager.save_state(state1)
        state_manager.save_state(state2)

        # 一覧取得
        states = state_manager.list_states()

        assert len(states) == 2
        titles = [s.book_title for s in states]
        assert "Book 1" in titles
        assert "Book 2" in titles

    def test_create_initial_state(self, state_manager):
        """初期状態作成テスト"""
        state = state_manager.create_initial_state(
            book_title="Test Book",
            total_pages=100,
            output_file="output/test.txt",
            screenshot_dir="output/screenshots",
            start_page=1,
        )

        assert state.book_title == "Test Book"
        assert state.total_pages == 100
        assert state.current_page == 1
        assert state.status == "in_progress"
        assert state.processed_pages == []
        assert state.failed_pages == []

    def test_create_initial_state_with_custom_start_page(self, state_manager):
        """カスタム開始ページでの初期状態作成テスト"""
        state = state_manager.create_initial_state(
            book_title="Test Book",
            total_pages=100,
            output_file="output/test.txt",
            screenshot_dir="output/screenshots",
            start_page=10,
        )

        assert state.current_page == 10

    def test_save_and_load_with_complex_data(self, state_manager):
        """複雑なデータの保存・読み込みテスト"""
        now = datetime.now().isoformat()
        state = StateData(
            book_title="Complex Book",
            start_datetime=now,
            last_update=now,
            current_page=50,
            total_pages=200,
            processed_pages=list(range(1, 50)),
            failed_pages=[5, 10, 15],
            output_file="output/complex.txt",
            screenshot_dir="output/screenshots_complex",
            status="in_progress",
        )

        # 保存
        state_manager.save_state(state)

        # 読み込み
        loaded_state = state_manager.load_state("Complex Book")

        assert loaded_state is not None
        assert loaded_state.processed_pages == list(range(1, 50))
        assert loaded_state.failed_pages == [5, 10, 15]
