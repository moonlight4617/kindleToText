"""
text_writer.py モジュールのユニットテスト
"""

import pytest
from pathlib import Path
from datetime import datetime
from src.output.text_writer import TextWriter, MarkdownWriter, quick_write


class TestTextWriter:
    """TextWriterクラスのテスト"""

    def test_init_default(self):
        """デフォルト初期化のテスト"""
        writer = TextWriter()

        assert writer.encoding == "utf-8"
        assert writer.add_bom is False
        assert writer.newline is None

    def test_init_with_bom(self):
        """UTF-8 BOM付き初期化のテスト"""
        writer = TextWriter(encoding="utf-8", add_bom=True)

        assert writer.encoding == "utf-8-sig"

    def test_init_custom(self):
        """カスタム設定での初期化テスト"""
        writer = TextWriter(
            encoding="shift_jis",
            newline="\r\n"
        )

        assert writer.encoding == "shift_jis"
        assert writer.newline == "\r\n"

    def test_create_file(self, tmp_path):
        """ファイル作成のテスト"""
        writer = TextWriter()
        file_path = tmp_path / "test.txt"
        content = "テストコンテンツ"

        result = writer.create_file(file_path, content)

        assert result is True
        assert file_path.exists()

        # 内容を確認
        text = file_path.read_text(encoding="utf-8")
        assert text == content

    def test_create_file_with_metadata(self, tmp_path):
        """メタデータ付きファイル作成のテスト"""
        writer = TextWriter()
        file_path = tmp_path / "test_metadata.txt"
        content = "本文"
        metadata = {
            "title": "テストタイトル",
            "author": "テスト太郎",
            "date": "2025-10-29"
        }

        result = writer.create_file(file_path, content, metadata)

        assert result is True
        assert file_path.exists()

        # 内容を確認
        text = file_path.read_text(encoding="utf-8")
        assert "---" in text
        assert "Title: テストタイトル" in text
        assert "Author: テスト太郎" in text
        assert "本文" in text

    def test_create_file_overwrite_false(self, tmp_path):
        """既存ファイルへの上書き禁止テスト"""
        writer = TextWriter()
        file_path = tmp_path / "existing.txt"

        # 最初のファイルを作成
        writer.create_file(file_path, "最初の内容")

        # 上書き禁止で再作成
        result = writer.create_file(file_path, "新しい内容", overwrite=False)

        assert result is False

        # 内容が変わっていないことを確認
        text = file_path.read_text(encoding="utf-8")
        assert text == "最初の内容"

    def test_create_file_overwrite_true(self, tmp_path):
        """既存ファイルへの上書き許可テスト"""
        writer = TextWriter()
        file_path = tmp_path / "overwrite.txt"

        # 最初のファイルを作成
        writer.create_file(file_path, "最初の内容")

        # 上書き許可で再作成
        result = writer.create_file(file_path, "新しい内容", overwrite=True)

        assert result is True

        # 内容が更新されていることを確認
        text = file_path.read_text(encoding="utf-8")
        assert text == "新しい内容"

    def test_create_file_auto_create_directory(self, tmp_path):
        """ディレクトリ自動作成のテスト"""
        writer = TextWriter()
        file_path = tmp_path / "nested" / "dir" / "test.txt"

        result = writer.create_file(file_path, "テスト")

        assert result is True
        assert file_path.exists()
        assert file_path.parent.exists()

    def test_append_text(self, tmp_path):
        """テキスト追記のテスト"""
        writer = TextWriter()
        file_path = tmp_path / "append.txt"

        # 最初のファイルを作成
        writer.create_file(file_path, "最初の行")

        # テキストを追記
        result = writer.append_text(file_path, "追加の行")

        assert result is True

        # 内容を確認
        text = file_path.read_text(encoding="utf-8")
        assert "最初の行" in text
        assert "追加の行" in text

    def test_append_text_to_nonexistent_file(self, tmp_path):
        """存在しないファイルへの追記テスト"""
        writer = TextWriter()
        file_path = tmp_path / "new_append.txt"

        # 存在しないファイルに追記（自動作成される）
        result = writer.append_text(file_path, "最初の内容")

        assert result is True
        assert file_path.exists()

    def test_append_text_custom_separator(self, tmp_path):
        """カスタムセパレータでの追記テスト"""
        writer = TextWriter()
        file_path = tmp_path / "separator.txt"

        writer.create_file(file_path, "行1")
        writer.append_text(file_path, "行2", separator="\n---\n")

        text = file_path.read_text(encoding="utf-8")
        assert "---" in text

    def test_write_text_create_mode(self, tmp_path):
        """createモードでの書き込みテスト"""
        writer = TextWriter()
        file_path = tmp_path / "create_mode.txt"

        result = writer.write_text(file_path, "テスト", mode="create")

        assert result is True
        assert file_path.exists()

    def test_write_text_append_mode(self, tmp_path):
        """appendモードでの書き込みテスト"""
        writer = TextWriter()
        file_path = tmp_path / "append_mode.txt"

        writer.write_text(file_path, "最初", mode="create")
        result = writer.write_text(file_path, "追加", mode="append")

        assert result is True

        text = file_path.read_text(encoding="utf-8")
        assert "最初" in text
        assert "追加" in text

    def test_write_text_overwrite_mode(self, tmp_path):
        """overwriteモードでの書き込みテスト"""
        writer = TextWriter()
        file_path = tmp_path / "overwrite_mode.txt"

        writer.write_text(file_path, "最初", mode="create")
        result = writer.write_text(file_path, "上書き", mode="overwrite")

        assert result is True

        text = file_path.read_text(encoding="utf-8")
        assert text == "上書き"
        assert "最初" not in text

    def test_write_text_invalid_mode(self, tmp_path):
        """無効なモードでの書き込みテスト"""
        writer = TextWriter()
        file_path = tmp_path / "invalid_mode.txt"

        result = writer.write_text(file_path, "テスト", mode="invalid")

        assert result is False

    def test_add_metadata_top(self, tmp_path):
        """メタデータ追加（先頭）のテスト"""
        writer = TextWriter()
        file_path = tmp_path / "metadata_top.txt"

        # ファイルを作成
        writer.create_file(file_path, "本文")

        # メタデータを追加
        metadata = {"title": "タイトル", "author": "著者"}
        result = writer.add_metadata(file_path, metadata, position="top")

        assert result is True

        text = file_path.read_text(encoding="utf-8")
        # メタデータが先頭にあることを確認
        assert text.startswith("---")
        assert "本文" in text

    def test_add_metadata_bottom(self, tmp_path):
        """メタデータ追加（末尾）のテスト"""
        writer = TextWriter()
        file_path = tmp_path / "metadata_bottom.txt"

        writer.create_file(file_path, "本文")

        metadata = {"title": "タイトル"}
        result = writer.add_metadata(file_path, metadata, position="bottom")

        assert result is True

        text = file_path.read_text(encoding="utf-8")
        # メタデータが末尾にあることを確認
        assert text.endswith("---")

    def test_add_metadata_to_nonexistent_file(self, tmp_path):
        """存在しないファイルへのメタデータ追加テスト"""
        writer = TextWriter()
        file_path = tmp_path / "nonexistent.txt"

        metadata = {"title": "タイトル"}
        result = writer.add_metadata(file_path, metadata)

        assert result is False

    def test_write_pages(self, tmp_path):
        """複数ページ書き込みのテスト"""
        writer = TextWriter()
        file_path = tmp_path / "pages.txt"

        pages = {
            1: "ページ1の内容",
            2: "ページ2の内容",
            3: "ページ3の内容"
        }

        result = writer.write_pages(file_path, pages)

        assert result is True
        assert file_path.exists()

        text = file_path.read_text(encoding="utf-8")
        assert "ページ1の内容" in text
        assert "ページ2の内容" in text
        assert "ページ3の内容" in text
        assert "---" in text  # デフォルトセパレータ

    def test_write_pages_with_metadata(self, tmp_path):
        """メタデータ付き複数ページ書き込みのテスト"""
        writer = TextWriter()
        file_path = tmp_path / "pages_metadata.txt"

        pages = {1: "ページ1", 2: "ページ2"}
        metadata = {"title": "書籍タイトル"}

        result = writer.write_pages(file_path, pages, metadata)

        assert result is True

        text = file_path.read_text(encoding="utf-8")
        assert "Title: 書籍タイトル" in text
        assert "ページ1" in text

    def test_write_pages_custom_separator(self, tmp_path):
        """カスタムセパレータでのページ書き込みテスト"""
        writer = TextWriter()
        file_path = tmp_path / "pages_separator.txt"

        pages = {1: "ページ1", 2: "ページ2"}

        result = writer.write_pages(
            file_path,
            pages,
            page_separator="\n\n===PAGE BREAK===\n\n"
        )

        assert result is True

        text = file_path.read_text(encoding="utf-8")
        assert "===PAGE BREAK===" in text

    def test_get_file_info(self, tmp_path):
        """ファイル情報取得のテスト"""
        writer = TextWriter()
        file_path = tmp_path / "info.txt"

        writer.create_file(file_path, "テスト")

        info = writer.get_file_info(file_path)

        assert info is not None
        assert info["path"] == str(file_path)
        assert info["size"] > 0
        assert isinstance(info["created"], datetime)
        assert isinstance(info["modified"], datetime)
        assert info["encoding"] == "utf-8"

    def test_get_file_info_nonexistent(self, tmp_path):
        """存在しないファイルの情報取得テスト"""
        writer = TextWriter()
        file_path = tmp_path / "nonexistent.txt"

        info = writer.get_file_info(file_path)

        assert info is None


class TestMarkdownWriter:
    """MarkdownWriterクラスのテスト"""

    def test_init(self):
        """初期化のテスト"""
        writer = MarkdownWriter()

        assert writer.encoding == "utf-8"

    def test_create_markdown_file(self, tmp_path):
        """Markdownファイル作成のテスト"""
        writer = MarkdownWriter()
        file_path = tmp_path / "test.md"
        title = "テストドキュメント"
        content = "これは本文です。"

        result = writer.create_markdown_file(file_path, title, content)

        assert result is True
        assert file_path.exists()

        text = file_path.read_text(encoding="utf-8")
        assert f"# {title}" in text
        assert content in text

    def test_create_markdown_file_auto_extension(self, tmp_path):
        """拡張子自動付与のテスト"""
        writer = MarkdownWriter()
        file_path = tmp_path / "test"  # 拡張子なし

        writer.create_markdown_file(file_path, "タイトル", "本文")

        # .mdが自動付与される
        expected_path = tmp_path / "test.md"
        assert expected_path.exists()

    def test_create_markdown_file_with_metadata(self, tmp_path):
        """メタデータ付きMarkdownファイル作成のテスト"""
        writer = MarkdownWriter()
        file_path = tmp_path / "metadata.md"
        metadata = {
            "author": "著者名",
            "date": "2025-10-29"
        }

        result = writer.create_markdown_file(
            file_path,
            "タイトル",
            "本文",
            metadata
        )

        assert result is True

        text = file_path.read_text(encoding="utf-8")
        assert "---" in text
        assert "Author: 著者名" in text

    def test_create_markdown_file_with_toc(self, tmp_path):
        """目次付きMarkdownファイル作成のテスト"""
        writer = MarkdownWriter()
        file_path = tmp_path / "toc.md"
        content = "## 第一章\n\n本文\n\n## 第二章\n\n本文"

        result = writer.create_markdown_file(
            file_path,
            "タイトル",
            content,
            add_toc=True
        )

        assert result is True

        text = file_path.read_text(encoding="utf-8")
        assert "## 目次" in text
        assert "第一章" in text
        assert "第二章" in text

    def test_generate_toc(self):
        """目次生成のテスト"""
        writer = MarkdownWriter()
        content = "# 大見出し\n\n## 中見出し1\n\n### 小見出し\n\n## 中見出し2"

        toc = writer._generate_toc(content)

        assert "大見出し" in toc
        assert "中見出し1" in toc
        assert "小見出し" in toc
        assert "中見出し2" in toc
        # インデントが正しいか確認
        assert "  -" in toc  # レベル2のインデント


class TestHelperFunctions:
    """ヘルパー関数のテスト"""

    def test_quick_write_plain_text(self, tmp_path):
        """プレーンテキストのクイック書き込みテスト"""
        file_path = tmp_path / "quick.txt"
        text = "クイックテスト"

        result = quick_write(file_path, text)

        assert result is True
        assert file_path.exists()

    def test_quick_write_markdown(self, tmp_path):
        """Markdownのクイック書き込みテスト"""
        file_path = tmp_path / "quick.md"
        text = "Markdownテスト"

        result = quick_write(file_path, text, markdown=True)

        assert result is True
        assert file_path.exists()

        content = file_path.read_text(encoding="utf-8")
        assert "# Quick" in content  # ファイル名から生成されたタイトル

    def test_quick_write_with_metadata(self, tmp_path):
        """メタデータ付きクイック書き込みテスト"""
        file_path = tmp_path / "quick_meta.txt"
        text = "テスト"
        metadata = {"author": "テスト太郎"}

        result = quick_write(file_path, text, metadata)

        assert result is True

        content = file_path.read_text(encoding="utf-8")
        assert "Author: テスト太郎" in content
