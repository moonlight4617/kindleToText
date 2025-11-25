"""
formatter.py モジュールのユニットテスト
"""

import pytest
from src.output.formatter import TextFormatter, quick_format
from src.ocr.ocr_interface import LayoutData, TextBlock, BoundingBox


class TestTextFormatter:
    """TextFormatterクラスのテスト"""

    def test_init_default(self):
        """デフォルト初期化のテスト"""
        formatter = TextFormatter()

        assert formatter.remove_extra_spaces is True
        assert formatter.normalize_linebreaks is True
        assert formatter.remove_hyphenation is True
        assert formatter.detect_headings is True

    def test_init_custom(self):
        """カスタム設定での初期化テスト"""
        formatter = TextFormatter(
            remove_extra_spaces=False,
            normalize_linebreaks=False,
            remove_hyphenation=False,
            detect_headings=False
        )

        assert formatter.remove_extra_spaces is False
        assert formatter.normalize_linebreaks is False
        assert formatter.remove_hyphenation is False
        assert formatter.detect_headings is False

    def test_clean_text_empty(self):
        """空テキストのクリーニングテスト"""
        formatter = TextFormatter()
        result = formatter.clean_text("")

        assert result == ""

    def test_clean_text_remove_hyphenation(self):
        """ハイフン結合解除のテスト"""
        formatter = TextFormatter()
        text = "これはテス-\nトです。"
        result = formatter.clean_text(text)

        assert "これはテストです。" in result

    def test_clean_text_normalize_linebreaks(self):
        """改行正規化のテスト"""
        formatter = TextFormatter()
        text = "行1\r\n行2\r行3\n行4"
        result = formatter.clean_text(text)

        # すべての改行が\nに統一される
        assert "\r\n" not in result
        assert "\r" not in result
        assert result.count("\n") == 3

    def test_clean_text_remove_extra_spaces(self):
        """余分なスペース削除のテスト"""
        formatter = TextFormatter()
        text = "これは    テスト   です。"
        result = formatter.clean_text(text)

        assert result == "これは テスト です。"

    def test_format_headings_without_layout(self):
        """レイアウト情報なしの見出し整形テスト"""
        formatter = TextFormatter()
        text = "第一章\n\nこれは本文です。"
        result = formatter.format_headings(text, layout=None, markdown=True)

        assert "##" in result  # 見出しマークが付加される

    def test_format_headings_disabled(self):
        """見出し検出無効時のテスト"""
        formatter = TextFormatter(detect_headings=False)
        text = "第一章\n\nこれは本文です。"
        result = formatter.format_headings(text)

        assert result == text  # 変更なし

    def test_format_headings_with_layout(self):
        """レイアウト情報ありの見出し整形テスト"""
        formatter = TextFormatter()

        # テストデータを作成
        bbox1 = BoundingBox(left=0, top=0, width=200, height=40)
        block1 = TextBlock(
            text="見出し",
            bounding_box=bbox1,
            confidence=0.9,
            block_type="heading"
        )

        bbox2 = BoundingBox(left=0, top=50, width=600, height=20)
        block2 = TextBlock(
            text="本文テキスト",
            bounding_box=bbox2,
            confidence=0.9,
            block_type="text"
        )

        layout = LayoutData(
            full_text="見出し\n本文テキスト",
            blocks=[block1, block2],
            page_width=800,
            page_height=600
        )

        text = "見出し\n本文テキスト"
        result = formatter.format_headings(text, layout, markdown=True)

        assert "#" in result
        assert "見出し" in result

    def test_organize_paragraphs(self):
        """段落整理のテスト"""
        formatter = TextFormatter()
        text = "段落1の文章です。\n\n\n段落2の文章です。"
        result = formatter.organize_paragraphs(text)

        # 3つ以上の改行は2つに統一される
        assert "\n\n\n" not in result
        assert result.count("\n\n") == 1

    def test_organize_paragraphs_with_headings(self):
        """見出しを含む段落整理のテスト"""
        formatter = TextFormatter()
        text = "# 見出し\n\n段落1です。これは長い文章なので50文字を超えるようにします。\nこれは続きです。\n\n段落2です。"
        result = formatter.organize_paragraphs(text)

        assert "# 見出し" in result
        # 長い段落は結合される
        assert "段落1です" in result and "これは続きです" in result

    def test_remove_artifacts(self):
        """アーティファクト除去のテスト"""
        formatter = TextFormatter()
        text = "テキスト\n123\nさらにテキスト\n-----\n続くテキスト"
        result = formatter.remove_artifacts(text)

        # ページ番号（単独の数字行）が除去される
        assert "\n123\n" not in result
        # 記号行が除去される
        assert "-----" not in result

    def test_remove_artifacts_repeated_chars(self):
        """連続文字除去のテスト"""
        formatter = TextFormatter()
        text = "通常のテキストaaaaa異常な繰り返し"
        result = formatter.remove_artifacts(text)

        # 5文字以上の繰り返しが除去される
        assert "aaaaa" not in result

    def test_format_full_text(self):
        """全体整形のテスト"""
        formatter = TextFormatter()
        text = "見出し\n\n\n本文テキスト   です。\nこれは-\n続きです。"
        result = formatter.format_full_text(text, layout=None, markdown=True)

        # クリーニング、見出し整形、段落整理が適用される
        assert result  # 空でない
        assert len(result) > 0

    def test_format_full_text_empty(self):
        """空テキストの全体整形テスト"""
        formatter = TextFormatter()
        result = formatter.format_full_text("")

        assert result == ""

    def test_calculate_average_height(self):
        """平均高さ計算のテスト"""
        formatter = TextFormatter()

        bbox1 = BoundingBox(left=0, top=0, width=100, height=20)
        bbox2 = BoundingBox(left=0, top=0, width=100, height=30)

        block1 = TextBlock(text="test1", bounding_box=bbox1, confidence=0.9)
        block2 = TextBlock(text="test2", bounding_box=bbox2, confidence=0.9)

        avg = formatter._calculate_average_height([block1, block2])

        assert avg == 25.0  # (20 + 30) / 2

    def test_calculate_average_height_empty(self):
        """空リストの平均高さ計算テスト"""
        formatter = TextFormatter()

        avg = formatter._calculate_average_height([])

        assert avg == 0.0

    def test_is_heading_by_height(self):
        """高さによる見出し判定のテスト"""
        formatter = TextFormatter()

        bbox = BoundingBox(left=0, top=0, width=100, height=30)
        block = TextBlock(text="見出し", bounding_box=bbox, confidence=0.9)

        # 平均高さ20に対して30は見出し
        assert formatter._is_heading(block, 20.0) is True

    def test_is_heading_by_length(self):
        """テキスト長による見出し判定のテスト"""
        formatter = TextFormatter()

        bbox = BoundingBox(left=0, top=0, width=100, height=20)
        block = TextBlock(text="短いテキスト", bounding_box=bbox, confidence=0.9)

        assert formatter._is_heading(block, 20.0) is True

    def test_is_heading_by_type(self):
        """ブロックタイプによる見出し判定のテスト"""
        formatter = TextFormatter()

        bbox = BoundingBox(left=0, top=0, width=100, height=20)
        block = TextBlock(
            text="見出し",
            bounding_box=bbox,
            confidence=0.9,
            block_type="heading"
        )

        assert formatter._is_heading(block, 20.0) is True

    def test_determine_heading_level(self):
        """見出しレベル判定のテスト"""
        formatter = TextFormatter()

        # レベル1（非常に大きい）
        bbox1 = BoundingBox(left=0, top=0, width=100, height=40)
        block1 = TextBlock(text="大見出し", bounding_box=bbox1, confidence=0.9)
        assert formatter._determine_heading_level(block1, 20.0) == 1

        # レベル2（大きい）
        bbox2 = BoundingBox(left=0, top=0, width=100, height=30)
        block2 = TextBlock(text="中見出し", bounding_box=bbox2, confidence=0.9)
        assert formatter._determine_heading_level(block2, 20.0) == 2

        # レベル3（やや大きい）
        bbox3 = BoundingBox(left=0, top=0, width=100, height=25)
        block3 = TextBlock(text="小見出し", bounding_box=bbox3, confidence=0.9)
        assert formatter._determine_heading_level(block3, 20.0) == 3


class TestHelperFunctions:
    """ヘルパー関数のテスト"""

    def test_quick_format(self):
        """quick_format関数のテスト"""
        text = "テスト   テキスト\n\n\nです。"
        result = quick_format(text)

        assert result
        assert len(result) > 0

    def test_quick_format_with_layout(self):
        """レイアウト情報ありのquick_formatテスト"""
        bbox = BoundingBox(left=0, top=0, width=100, height=30)
        block = TextBlock(
            text="見出し",
            bounding_box=bbox,
            confidence=0.9,
            block_type="heading"
        )

        layout = LayoutData(
            full_text="見出し\n本文",
            blocks=[block],
            page_width=800,
            page_height=600
        )

        text = "見出し\n本文"
        result = quick_format(text, layout, markdown=True)

        assert result
        assert "#" in result

    def test_quick_format_no_markdown(self):
        """Markdownなしのquick_formatテスト"""
        text = "見出し\n本文"
        result = quick_format(text, markdown=False)

        assert result
        # Markdown記号がないことを確認
        assert not result.startswith("#")


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_very_long_text(self):
        """非常に長いテキストのテスト"""
        formatter = TextFormatter()
        text = "テキスト" * 10000
        result = formatter.clean_text(text)

        assert len(result) > 0

    def test_special_characters(self):
        """特殊文字を含むテキストのテスト"""
        formatter = TextFormatter()
        text = "特殊文字: 😀 ♥ ★ © ® ™"
        result = formatter.clean_text(text)

        assert "😀" in result
        assert "♥" in result

    def test_mixed_languages(self):
        """多言語混在テキストのテスト"""
        formatter = TextFormatter()
        text = "日本語 English 中文 한글"
        result = formatter.clean_text(text)

        assert "日本語" in result
        assert "English" in result
        assert "中文" in result
        assert "한글" in result

    def test_control_characters_removal(self):
        """制御文字除去のテスト"""
        formatter = TextFormatter()
        text = "テキスト\x00\x01\x02です"
        result = formatter.clean_text(text)

        # 制御文字が除去される
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result
        assert "テキストです" in result
