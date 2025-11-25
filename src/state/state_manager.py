"""
状態管理モジュール

書籍のOCR処理状態を保存・読み込み・更新する機能を提供します。
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger


@dataclass
class StateData:
    """処理状態データクラス"""

    book_title: str
    start_datetime: str  # ISO format datetime string
    last_update: str  # ISO format datetime string
    current_page: int
    total_pages: int
    processed_pages: List[int]
    failed_pages: List[int]
    output_file: str
    screenshot_dir: str
    status: str  # "in_progress", "completed", "failed"

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StateData":
        """辞書から StateData を作成"""
        return cls(**data)


class StateManager:
    """
    状態管理クラス

    書籍のOCR処理状態を保存・読み込み・更新する機能を提供します。
    """

    def __init__(self, state_dir: str = "output/state"):
        """
        初期化

        Args:
            state_dir: 状態ファイルを保存するディレクトリパス
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"StateManager initialized with state_dir: {self.state_dir}")

    def get_state_file_path(self, book_title: str) -> Path:
        """
        書籍タイトルから状態ファイルパスを取得

        Args:
            book_title: 書籍タイトル

        Returns:
            状態ファイルのパス
        """
        # ファイル名として使用できない文字を置換
        safe_title = "".join(
            c if c.isalnum() or c in (" ", "_", "-") else "_" for c in book_title
        )
        safe_title = safe_title.strip().replace(" ", "_")
        return self.state_dir / f"{safe_title}_state.json"

    def save_state(self, state: StateData) -> bool:
        """
        状態をファイルに保存

        Args:
            state: 保存する状態データ

        Returns:
            成功した場合 True、失敗した場合 False
        """
        try:
            file_path = self.get_state_file_path(state.book_title)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"State saved successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    def load_state(self, book_title: str) -> Optional[StateData]:
        """
        状態をファイルから読み込み

        Args:
            book_title: 書籍タイトル

        Returns:
            読み込んだ状態データ。ファイルが存在しない場合は None
        """
        try:
            file_path = self.get_state_file_path(book_title)
            if not file_path.exists():
                logger.warning(f"State file not found: {file_path}")
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            state = StateData.from_dict(data)
            logger.info(f"State loaded successfully: {file_path}")
            return state
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None

    def update_state(self, state: StateData, updates: dict) -> StateData:
        """
        状態を更新

        Args:
            state: 現在の状態データ
            updates: 更新する内容を含む辞書

        Returns:
            更新された状態データ
        """
        try:
            # 現在の状態を辞書に変換
            state_dict = state.to_dict()

            # 更新内容を適用
            for key, value in updates.items():
                if key in state_dict:
                    state_dict[key] = value
                else:
                    logger.warning(f"Unknown state key: {key}")

            # last_update を更新
            state_dict["last_update"] = datetime.now().isoformat()

            # 新しい StateData を作成
            updated_state = StateData.from_dict(state_dict)
            logger.debug(f"State updated: {updates}")
            return updated_state
        except Exception as e:
            logger.error(f"Failed to update state: {e}")
            return state

    def can_resume(self, book_title: str) -> bool:
        """
        処理を再開可能か判定

        Args:
            book_title: 書籍タイトル

        Returns:
            再開可能な場合 True、そうでない場合 False
        """
        try:
            state = self.load_state(book_title)
            if state is None:
                return False

            # 状態が "in_progress" の場合のみ再開可能
            if state.status != "in_progress":
                logger.info(f"Cannot resume: status is {state.status}")
                return False

            # 現在のページが総ページ数より小さい場合は再開可能
            if state.current_page < state.total_pages:
                logger.info(f"Can resume from page {state.current_page}")
                return True

            logger.info("Cannot resume: all pages processed")
            return False
        except Exception as e:
            logger.error(f"Failed to check resume capability: {e}")
            return False

    def delete_state(self, book_title: str) -> bool:
        """
        状態ファイルを削除

        Args:
            book_title: 書籍タイトル

        Returns:
            成功した場合 True、失敗した場合 False
        """
        try:
            file_path = self.get_state_file_path(book_title)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"State file deleted: {file_path}")
                return True
            else:
                logger.warning(f"State file not found: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete state file: {e}")
            return False

    def list_states(self) -> List[StateData]:
        """
        すべての状態ファイルを一覧表示

        Returns:
            状態データのリスト
        """
        try:
            states = []
            for file_path in self.state_dir.glob("*_state.json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                states.append(StateData.from_dict(data))
            logger.info(f"Found {len(states)} state files")
            return states
        except Exception as e:
            logger.error(f"Failed to list states: {e}")
            return []

    def create_initial_state(
        self,
        book_title: str,
        total_pages: int,
        output_file: str,
        screenshot_dir: str,
        start_page: int = 1,
    ) -> StateData:
        """
        初期状態を作成

        Args:
            book_title: 書籍タイトル
            total_pages: 総ページ数
            output_file: 出力ファイルパス
            screenshot_dir: スクリーンショット保存ディレクトリ
            start_page: 開始ページ（デフォルト: 1）

        Returns:
            作成された初期状態データ
        """
        now = datetime.now().isoformat()
        state = StateData(
            book_title=book_title,
            start_datetime=now,
            last_update=now,
            current_page=start_page - 1,  # 初期値は開始ページの1つ前（まだ処理していない）
            total_pages=total_pages,
            processed_pages=[],
            failed_pages=[],
            output_file=output_file,
            screenshot_dir=screenshot_dir,
            status="in_progress",
        )
        logger.info(f"Initial state created for: {book_title}")
        return state
