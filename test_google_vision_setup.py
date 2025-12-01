"""
Google Cloud Vision API セットアップ検証スクリプト

このスクリプトは、Google Cloud Vision APIが正しくセットアップされているか確認します。
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

# プロジェクトのルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ocr.google_vision_engine import GoogleVisionEngine
from src.config.config_loader import ConfigLoader


def create_test_image():
    """テスト用の日本語画像を作成"""
    # 800x600の白い画像を作成
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)

    # テキストを描画（システムフォントを使用）
    try:
        # Windowsのデフォルト日本語フォントを試す
        font = ImageFont.truetype("msgothic.ttc", 40)
    except:
        # フォントが見つからない場合はデフォルトフォントを使用
        font = ImageFont.load_default()

    # テスト用のテキスト（専門用語を含む）
    test_text = """大規模言語モデル (LLM)
Transformer アーキテクチャ
自然言語処理 (NLP)"""

    # テキストを画像に描画
    draw.text((50, 200), test_text, fill='black', font=font)

    return img


def main():
    """メイン処理"""
    print("=" * 70)
    print("Google Cloud Vision API セットアップ検証")
    print("=" * 70)
    print()

    # 1. 設定ファイルの読み込み
    print("[ステップ1] 設定ファイルの確認")
    try:
        config_loader = ConfigLoader()
        config = config_loader.load()

        ocr_config = config.get('ocr', {})
        primary_engine = ocr_config.get('primary_engine')
        google_vision_config = ocr_config.get('google_vision', {})
        credentials_path = google_vision_config.get('credentials_path')

        print(f"  [OK] プライマリエンジン: {primary_engine}")
        print(f"  [OK] 認証情報パス: {credentials_path}")
        print()

        if primary_engine != "google_vision":
            print("  [WARNING] プライマリエンジンがgoogle_visionではありません")
            print()

        if not credentials_path:
            print("  [ERROR] credentials_pathが設定されていません")
            return False

    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

    # 2. 認証情報ファイルの確認
    print("[ステップ2] 認証情報ファイルの確認")
    credentials_file = Path(credentials_path)

    if not credentials_file.exists():
        print(f"  [ERROR] 認証情報ファイルが見つかりません: {credentials_file}")
        print(f"  [HINT] JSONキーファイルを {credentials_file} に配置してください")
        return False
    else:
        print(f"  [OK] 認証情報ファイル確認: {credentials_file}")
        print()

    # 3. Google Vision Engineの初期化
    print("[ステップ3] Google Vision Engineの初期化")
    try:
        engine = GoogleVisionEngine(google_vision_config)

        if not engine.is_available():
            print("  [ERROR] Google Vision APIが利用できません")
            print("  [HINT] google-cloud-visionパッケージがインストールされているか確認してください")
            return False

        print("  [OK] エンジンが利用可能です")

        if not engine.initialize():
            print("  [ERROR] エンジンの初期化に失敗しました")
            return False

        print("  [OK] エンジンの初期化が完了しました")
        print()

    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. テスト画像でOCRを実行
    print("[ステップ4] テスト画像でOCR実行")
    try:
        # テスト画像を作成
        test_image = create_test_image()
        print("  [OK] テスト画像を作成しました")

        # OCRを実行
        print("  [PROCESSING] OCR処理を実行中...")
        result = engine.extract_text(test_image)

        if not result.success:
            print(f"  [ERROR] OCR処理が失敗しました: {result.error_message}")
            return False

        print("  [OK] OCR処理が完了しました")
        print()

        # 結果を表示
        print("[OCR結果]")
        print("-" * 70)
        print(result.text)
        print("-" * 70)
        print()
        print(f"  信頼度: {result.confidence:.2%}")
        print(f"  処理時間: {result.processing_time:.2f}秒")
        print(f"  エンジン: {result.engine_name}")
        print()

        # 期待されるキーワードが含まれているか確認
        expected_keywords = ["大規模言語モデル", "LLM", "Transformer", "自然言語処理", "NLP"]
        found_keywords = [kw for kw in expected_keywords if kw in result.text]

        if found_keywords:
            print(f"  [OK] 検出されたキーワード: {', '.join(found_keywords)}")
        else:
            print("  [WARNING] 期待されるキーワードが検出されませんでした")

    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

    # 5. 成功
    print()
    print("=" * 70)
    print("[SUCCESS] すべての検証が完了しました!")
    print("=" * 70)
    print()
    print("次のステップ:")
    print("  1. 実際のKindleスクリーンショットでOCRを実行してください")
    print("  2. yomitokuとの精度比較を行ってください")
    print("  3. NotebookLMでの利用を試してください")
    print()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
