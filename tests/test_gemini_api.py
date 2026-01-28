"""
Gemini API接続テストスクリプト

このスクリプトは、Gemini APIキーが正しく設定されているか、
APIに接続できるかをテストします。
"""

import os
import sys
from pathlib import Path

# Windows環境での文字エンコーディング問題を回避
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ocr import GeminiEngine
from PIL import Image


def main():
    print("=" * 60)
    print("Gemini API 接続テスト")
    print("=" * 60)
    print()

    # ステップ1: APIキーの確認
    print("[1] APIキーの確認...")
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("❌ GEMINI_API_KEYが環境変数に設定されていません")
        print()
        print("設定方法:")
        print("  PowerShell:")
        print('    $env:GEMINI_API_KEY="your-api-key-here"')
        print()
        print("  または、永続的に設定:")
        print('    [System.Environment]::SetEnvironmentVariable(\'GEMINI_API_KEY\', \'your-api-key\', \'User\')')
        return 1

    # APIキーの一部を表示（セキュリティのため）
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
    print(f"✓ APIキーが設定されています: {masked_key}")
    print()

    # ステップ2: エンジンの初期化
    print("[2] Gemini Engineの初期化...")
    try:
        engine = GeminiEngine()

        if engine.initialize():
            print(f"✓ Gemini APIの初期化に成功しました")
            print(f"  モデル: {engine.model_name}")
            print(f"  温度: {engine.temperature}")
            print(f"  最大出力トークン: {engine.max_output_tokens}")

            # 利用可能なモデルをリスト
            print("\n  利用可能なモデルを確認中...")
            try:
                import google.generativeai as genai
                models = genai.list_models()
                print("  利用可能なモデル:")
                for model in models:
                    if 'generateContent' in model.supported_generation_methods:
                        print(f"    - {model.name}")
            except Exception as list_error:
                print(f"  モデルリスト取得エラー: {list_error}")
        else:
            print("❌ 初期化に失敗しました")
            return 1
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()

    # ステップ3: テスト画像の作成
    print("[3] テスト画像の作成...")
    try:
        # 簡単なテスト画像を作成（白地に黒文字）
        from PIL import ImageDraw, ImageFont

        # 200x100の白い画像を作成
        test_image = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(test_image)

        # テキストを描画（フォントが利用できない場合はデフォルトフォント）
        text = "こんにちは、世界！\nHello, World!"
        try:
            # Windowsの標準フォントを試す
            font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 32)
        except:
            # フォントが見つからない場合はデフォルト
            font = None

        draw.text((20, 50), text, fill='black', font=font)

        print("✓ テスト画像を作成しました")
        print(f"  サイズ: {test_image.size}")
        print(f"  テキスト: {text.replace(chr(10), ' ')}")
    except Exception as e:
        print(f"❌ 画像作成エラー: {e}")
        return 1
    print()

    # ステップ4: OCR実行
    print("[4] OCR処理の実行...")
    try:
        result = engine.extract_text(test_image)

        if result.success:
            print("✓ テキスト抽出に成功しました")
            print(f"  信頼度: {result.confidence:.2f}")
            print(f"  処理時間: {result.processing_time:.2f}秒")
            print()
            print("抽出されたテキスト:")
            print("-" * 60)
            print(result.text)
            print("-" * 60)
        else:
            print(f"❌ テキスト抽出に失敗しました: {result.error_message}")
            return 1
    except Exception as e:
        print(f"❌ OCR実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()

    # ステップ5: クリーンアップ
    print("[5] リソースの解放...")
    try:
        engine.close()
        print("✓ エンジンをクローズしました")
    except Exception as e:
        print(f"⚠ クローズ時の警告: {e}")
    print()

    # 完了
    print("=" * 60)
    print("✓ すべてのテストが成功しました！")
    print("Gemini OCRエンジンは正常に動作しています。")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
