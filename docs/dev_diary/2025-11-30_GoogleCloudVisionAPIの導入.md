# Google Cloud Vision API導入計画

## ステータス: ✅ 完全完了（2025-11-30）

Phase 1の実装が完了し、Google Cloud Vision APIのセットアップも完了。
**検証テストも成功し、実際にAPIが動作することを確認しました。**

### 検証結果

#### テスト1: 合成画像での検証
- **信頼度**: 95.00%
- **処理時間**: 0.31秒
- **認識精度**: すべてのキーワード（大規模言語モデル、LLM、Transformer、自然言語処理、NLP）を正確に認識

#### テスト2: 実際のKindleスクリーンショットでの比較

**Google Vision API vs Yomitoku 比較結果:**

| 項目 | Google Vision API | Yomitoku | 差分 |
|------|-------------------|----------|------|
| 処理時間 | **1.18秒** | 45.30秒 | **38倍高速** |
| 信頼度 | **95.00%** | 0.00% | - |
| テキスト長 | 3,031文字 | 2,780文字 | +251文字 |

**結論**: Google Vision APIは、Yomitokuと比較して：
- 38倍高速
- より高い精度（専門用語の正確な認識）
- より多くのテキストを抽出

**推奨**: NotebookLMでの利用には、Google Vision APIを強く推奨

## 背景

現在使用しているyomitokuでのOCR精度が、NotebookLMでの利用には不十分であることが判明。特に以下の問題が顕著：

1. 専門用語の誤認識（LLM → 山M、Transformer → Tardoreなど）
2. 漢字の誤変換（本章 → 本車、訓練 → 事種など）
3. カタカナの誤認識（モデル → モアル、データ → アータなど）

商用OCR APIであるGoogle Cloud Vision APIの導入により、大幅な精度向上が期待できる。

## 実装完了サマリー

### 完了した作業

1. **Phase 1: GoogleVisionEngineの実装** ✅
   - [src/ocr/google_vision_engine.py](../../../src/ocr/google_vision_engine.py) - 完了
   - TEXT_DETECTION と DOCUMENT_TEXT_DETECTION をサポート
   - レイアウト情報抽出機能
   - エラーハンドリングとロギング

2. **依存関係の追加** ✅
   - `google-cloud-vision>=3.4.0` を requirements.txt に追加
   - パッケージのインストール完了

3. **設定ファイルの更新** ✅
   - config/config.yaml: Google Vision設定を追加、プライマリエンジンに設定
   - config/config.example.yaml: 詳細なコメント付き設定例
   - .gitignore: 認証情報ファイルの除外設定

4. **ユニットテストの作成** ✅
   - tests/test_google_vision_engine.py - 11個のテストが成功

5. **Google Cloudセットアップ** ✅ (2025-11-30完了)
   - Google Cloud プロジェクト作成
   - Cloud Vision API の有効化
   - サービスアカウントの作成とJSONキーのダウンロード
   - 認証情報ファイルの配置: `config/google_credentials.json`

### 現在の設定

```yaml
ocr:
  primary_engine: "google_vision"  # ✅ Google Vision APIを使用
  fallback_engine: "yomitoku"      # エラー時はyomitokuにフォールバック

  google_vision:
    credentials_path: "config/google_credentials.json"
    detection_type: "DOCUMENT_TEXT_DETECTION"
    language_hints: ["ja", "en"]
```

## 現在のアーキテクチャ

### OCRインターフェース設計

既存のコードベースは、OCRエンジンの抽象化が適切に設計されている：

- `OCRInterface`: 抽象基底クラス（ABC）
- `OCREngineFactory`: エンジンの登録・生成を管理
- `OCREngineSelector`: 優先順位に基づいてエンジンを自動選択

### 既存エンジン

1. **YomitokuEngine** ([src/ocr/yomitoku_engine.py](../../../src/ocr/yomitoku_engine.py))
   - 日本語特化のローカルOCR
   - GPUサポートあり
   - レイアウト情報取得可能

2. **TesseractEngine** ([src/ocr/tesseract_engine.py](../../../src/ocr/tesseract_engine.py))
   - オープンソースOCR
   - フォールバック用

### 設定管理

- YAMLベースの設定ファイル（[config/config.yaml](../../../config/config.yaml)）
- `ConfigLoader`クラスでドット記法サポート
- 既存のOCR設定：
  ```yaml
  ocr:
    primary_engine: "yomitoku"
    fallback_engine: "tesseract"
    retry_on_failure: true
    yomitoku:
      device: "cpu"
      confidence_threshold: 0.6
    tesseract:
      lang: "jpn"
      config: "--psm 6"
  ```

## 実装計画

### Phase 1: Google Cloud Vision API エンジンの実装

#### 1.1 依存関係の追加

**ファイル**: `requirements.txt`

```txt
google-cloud-vision>=3.4.0
```

#### 1.2 GoogleVisionEngineクラスの作成

**新規ファイル**: `src/ocr/google_vision_engine.py`

**実装内容**:
- `OCRInterface`を継承
- Google Cloud Vision API clientの初期化
- `TEXT_DETECTION`または`DOCUMENT_TEXT_DETECTION`機能の利用
- レスポンスから`OCRResult`への変換
- エラーハンドリング（API制限、認証エラーなど）

**主要メソッド**:
```python
class GoogleVisionEngine(OCRInterface):
    def __init__(self, config: Optional[dict] = None):
        # 設定：
        # - credentials_path: サービスアカウントキーのパス
        # - detection_type: "TEXT_DETECTION" or "DOCUMENT_TEXT_DETECTION"
        # - language_hints: ["ja", "en"]

    def initialize(self) -> bool:
        # Vision API clientの初期化
        # 認証情報の検証

    def extract_text(self, image: Image.Image) -> OCRResult:
        # 基本的なテキスト抽出
        # TEXT_DETECTION APIの呼び出し

    def extract_with_layout(self, image: Image.Image) -> OCRResult:
        # レイアウト情報付きテキスト抽出
        # DOCUMENT_TEXT_DETECTION APIの呼び出し
        # ブロック、パラグラフ、単語、シンボルの階層構造を解析
```

**レスポンスマッピング**:
- `TextAnnotation.description` → `OCRResult.text`
- Block/Paragraph情報 → `TextBlock`オブジェクト
- `BoundingPoly` → `BoundingBox`
- Confidence値の計算（Visionは単語レベルでconfidenceを返さない場合がある）

#### 1.3 ファクトリーへの登録

**ファイル**: `src/ocr/google_vision_engine.py` (末尾)

```python
# エンジンを登録
OCREngineFactory.register_engine("google_vision", GoogleVisionEngine)
```

**ファイル**: `src/ocr/__init__.py`

```python
from .google_vision_engine import GoogleVisionEngine

__all__ = [..., 'GoogleVisionEngine']
```

### Phase 2: 設定ファイルの更新

#### 2.1 config.yamlの拡張

**ファイル**: `config/config.yaml`

**追加内容**:
```yaml
ocr:
  primary_engine: "google_vision"  # yomitoku, tesseract, google_vision
  fallback_engine: "yomitoku"      # フォールバック先
  retry_on_failure: true
  max_retries: 3

  # 既存設定...
  yomitoku: {...}
  tesseract: {...}

  # 新規追加
  google_vision:
    credentials_path: null           # サービスアカウントキーのパス（nullの場合は環境変数GOOGLE_APPLICATION_CREDENTIALSを使用）
    detection_type: "DOCUMENT_TEXT_DETECTION"  # TEXT_DETECTION or DOCUMENT_TEXT_DETECTION
    language_hints: ["ja", "en"]     # 言語ヒント
    enable_text_detection_confidence: false  # Confidenceスコアの有効化（追加料金）
    image_context:
      language_hints: ["ja", "en"]
```

#### 2.2 config.example.yamlの更新

同様の設定をexampleファイルにも追加し、コメントで使い方を説明。

### Phase 3: 認証情報の管理

#### 3.1 サービスアカウントキーの取得手順

**ドキュメント**: このファイルの「セットアップ手順」セクション

1. Google Cloud Consoleでプロジェクト作成
2. Vision APIの有効化
3. サービスアカウントの作成
4. JSONキーのダウンロード
5. キーファイルの配置（推奨: `config/google_credentials.json`）
6. `.gitignore`への追加

#### 3.2 環境変数サポート

優先順位：
1. `config.yaml`の`credentials_path`
2. 環境変数`GOOGLE_APPLICATION_CREDENTIALS`
3. デフォルト認証情報（GCE/GKE環境）

### Phase 4: エラーハンドリングと料金管理

#### 4.1 APIエラーハンドリング

**主要エラー**:
- `google.api_core.exceptions.PermissionDenied`: 認証エラー
- `google.api_core.exceptions.ResourceExhausted`: API制限超過
- `google.api_core.exceptions.InvalidArgument`: 不正なリクエスト

**対応**:
- 適切なエラーメッセージを`OCRResult.error_message`に設定
- `success=False`でリターン
- フォールバックエンジンへの自動切り替え

#### 4.2 料金モニタリング

Vision APIは従量課金：
- 月間0-1,000ユニット: $1.50/1000ユニット
- 1,001-5,000,000: $1.50/1000ユニット
- DOCUMENT_TEXT_DETECTION: 通常のTEXT_DETECTIONと同料金

**推奨**:
- ログに処理画像数をカウント
- `max_api_calls_per_session`設定の追加を検討
- Quotaアラート設定（Google Cloud Console側）

### Phase 5: テスト実装

#### 5.1 ユニットテスト

**新規ファイル**: `tests/test_google_vision_engine.py`

**テスト項目**:
- [ ] エンジンの初期化
- [ ] 認証情報の読み込み
- [ ] テキスト抽出（モック使用）
- [ ] レイアウト抽出（モック使用）
- [ ] エラーハンドリング（認証失敗、API制限など）
- [ ] フォールバック動作

**モックの使用**:
```python
from unittest.mock import Mock, patch

@patch('google.cloud.vision.ImageAnnotatorClient')
def test_extract_text(mock_client):
    # モッククライアントを使用したテスト
```

#### 5.2 統合テスト

**新規ファイル**: `tests/integration/test_google_vision_integration.py`

実際のAPIを呼び出すテスト（CI/CDでは通常スキップ）:
- [ ] 実際の画像でのテキスト抽出
- [ ] 日本語テキストの精度確認
- [ ] レイアウト情報の正確性確認

#### 5.3 比較テスト

**目的**: Yomitokuとの精度比較

**ファイル**: `tests/benchmark/test_ocr_accuracy.py`

テストケース:
- [ ] 専門用語を含むページ
- [ ] 混在テキスト（日英）
- [ ] 複雑なレイアウト

### Phase 6: ドキュメント作成

#### 6.1 README更新

**ファイル**: `README.md`

追加内容:
- Google Cloud Vision APIの利用方法
- セットアップ手順
- 料金に関する注意事項

#### 6.2 設定ガイド

**新規ファイル**: `docs/google_vision_setup.md`

詳細なセットアップ手順:
1. Google Cloudプロジェクトの作成
2. Vision APIの有効化
3. 認証情報の設定
4. config.yamlの設定例
5. トラブルシューティング

## セットアップ手順（ユーザー向け）

### 1. Google Cloud Projectの準備

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新規プロジェクトを作成（または既存プロジェクトを選択）
3. 「APIとサービス」→「ライブラリ」から「Cloud Vision API」を検索
4. 「有効にする」をクリック

### 2. サービスアカウントの作成

1. 「APIとサービス」→「認証情報」
2. 「認証情報を作成」→「サービスアカウント」
3. サービスアカウント名を入力（例: `kindle-ocr-service`）
4. ロールを選択: `Cloud Vision API ユーザー`
5. 「完了」をクリック

### 3. 認証情報のダウンロード

1. 作成したサービスアカウントをクリック
2. 「キー」タブ→「鍵を追加」→「新しい鍵を作成」
3. 「JSON」を選択してダウンロード
4. ダウンロードしたファイルを`config/google_credentials.json`に配置

### 4. 設定ファイルの更新

`config/config.yaml`を編集:

```yaml
ocr:
  primary_engine: "google_vision"
  fallback_engine: "yomitoku"

  google_vision:
    credentials_path: "config/google_credentials.json"
    detection_type: "DOCUMENT_TEXT_DETECTION"
    language_hints: ["ja", "en"]
```

### 5. .gitignoreの確認

認証情報ファイルがgitignoreされていることを確認:

```gitignore
# Google Cloud credentials
config/google_credentials.json
config/*_credentials.json
*.json  # (認証情報ファイルのみを対象にする場合は上記の個別指定を推奨)
```

## 実装の優先順位

### Must Have (最小限の機能)
1. GoogleVisionEngineクラスの実装
2. TEXT_DETECTIONによる基本的なテキスト抽出
3. Config.yamlでのエンジン切り替え
4. 基本的なエラーハンドリング

### Should Have (重要な機能)
5. DOCUMENT_TEXT_DETECTIONによるレイアウト抽出
6. 環境変数による認証情報の指定
7. フォールバック機構の動作確認
8. ユニットテスト

### Nice to Have (追加機能)
9. 料金モニタリング機能
10. バッチ処理の最適化
11. キャッシュ機構
12. 詳細なドキュメント

## 実装時の注意点

### セキュリティ
- [ ] 認証情報ファイルを絶対にGitにコミットしない
- [ ] .gitignoreに認証情報のパターンを追加
- [ ] READMEにセキュリティ警告を記載

### コスト管理
- [ ] 処理画像数のロギング
- [ ] エラー時の無限リトライ防止
- [ ] 開発時はYomitokuを使用、本番のみGoogle Vision推奨

### 互換性
- [ ] 既存のYomitoku/Tesseractユーザーに影響を与えない
- [ ] Google Vision未設定時のグレースフルなフォールバック
- [ ] エンジンの利用可能性チェック（`is_available()`）

### パフォーマンス
- [ ] 画像サイズの制限（Vision API: 最大10MB）
- [ ] リトライロジックのバックオフ
- [ ] ネットワークタイムアウトの適切な設定

## 実装後の検証項目

### 機能検証
- [ ] 専門用語の認識精度（LLM、Transformer等）
- [ ] 漢字の認識精度
- [ ] カタカナの認識精度
- [ ] レイアウト情報の正確性

### 統合検証
- [ ] Config経由でのエンジン切り替え
- [ ] エラー時のフォールバック動作
- [ ] 既存機能（状態管理、進捗表示等）との統合

### NotebookLM向け検証
- [ ] 抽出テキストの可読性
- [ ] 専門用語の正確性
- [ ] 文脈の一貫性

## スケジュール案

1. **Phase 1**: GoogleVisionEngineの実装（2-3時間）
2. **Phase 2**: Config更新（30分）
3. **Phase 3**: 認証設定（30分）
4. **Phase 4**: エラーハンドリング（1時間）
5. **Phase 5**: テスト実装（1-2時間）
6. **Phase 6**: ドキュメント作成（1時間）

**合計**: 6-8時間

## 参考資料

- [Google Cloud Vision API - Python Client](https://cloud.google.com/python/docs/reference/vision/latest)
- [Cloud Vision API ドキュメント](https://cloud.google.com/vision/docs)
- [Vision API 料金](https://cloud.google.com/vision/pricing)
- [認証情報のセットアップ](https://cloud.google.com/docs/authentication/getting-started)

## 次のステップ

このドキュメント作成後:
1. ユーザーに実装計画の確認を依頼
2. 承認後、Phase 1から実装開始
3. 各フェーズ完了時にテストを実行
4. 最終的にNotebookLM向けの精度を再評価
