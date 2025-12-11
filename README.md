# Kindle to Text Converter

Kindle for PCで表示される書籍を自動的にスクリーンショット撮影し、OCR解析によってテキスト化するツール。

## 概要

このツールは、Kindle for PCで開いた書籍を自動的にキャプチャし、高精度なOCR処理によってテキストファイルに変換します。生成されたテキストファイルは、NotebookLMなどのツールにインポートして、書籍の要約やQAに活用できます。

## 主な機能

- **自動スクリーンショット撮影**: Kindle for PCのウィンドウを自動検出し、ページを順次キャプチャ
- **高精度画像前処理**: ノイズ除去、コントラスト調整、傾き補正など（精度優先）
- **多言語OCR対応**: Yomitoku（日本語特化）とTesseract（フォールバック）
- **中断・再開機能**: 長時間処理中でも安心。状態保存により途中から再開可能
- **進捗表示**: リアルタイムの処理状況と推定残り時間を表示
- **見出し認識**: フォントサイズと位置情報から見出しを自動検出

## 必要環境

- **OS**: Windows 10/11
- **Python**: 3.11.5 以上
- **Kindle**: Kindle for PC（最新版推奨）
- **OCR**: Yomitoku または Tesseract

## インストール

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd kindleToText_v2/project
```

### 2. Pythonバージョン確認

このプロジェクトはPython 3.11.5を使用します。pyenvでバージョンを管理しています。

```bash
python --version
# Python 3.11.5 が表示されることを確認
```

### 3. 仮想環境のアクティベート

```bash
# Windows
venv\Scripts\activate
```

### 4. 依存パッケージのインストール

依存パッケージは既にインストール済みです。新しい環境でセットアップする場合：

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 5. Yomitokuのインストール

Yomitoku（日本語OCRエンジン）を公式ドキュメントに従ってインストールします。

参照: https://kotaro-kinoshita.github.io/yomitoku/installation/

```bash
pip install yomitoku
```

### 6. Tesseractのインストール（オプション）

フォールバック用のTesseract OCRをインストールします。

1. [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki)からインストーラーをダウンロード
2. インストール時に「Japanese」言語パックを選択
3. インストールパスを確認（デフォルト: `C:\Program Files\Tesseract-OCR\tesseract.exe`）

### 7. 設定ファイルの作成

```bash
copy config\config.example.yaml config\config.yaml
```

必要に応じて`config\config.yaml`を編集してください。

## 使い方

### 基本的な使い方

```bash
python src/main.py --title "書籍タイトル"
```

### オプション

```bash
python src/main.py --help
```

利用可能なオプション：
- `--title TEXT`: 書籍タイトル（必須）
- `--start-page INTEGER`: 開始ページ（デフォルト: 1）
- `--end-page INTEGER`: 終了ページ（デフォルト: 自動検出）
- `--config PATH`: 設定ファイルパス（デフォルト: config/config.yaml）
- `--resume`: 前回の処理を再開
- `--debug`: デバッグモード

### 使用例

#### 新規処理

```bash
python src/main.py --title "深層学習入門"
```

#### 特定ページ範囲を指定

```bash
python src/main.py --title "深層学習入門" --start-page 10 --end-page 100
```

#### 前回の続きから再開

```bash
python src/main.py --title "深層学習入門" --resume
```

### 実行前の準備

1. Kindle for PCを起動し、変換したい書籍を開く
2. 全画面表示にするか、ウィンドウサイズを固定
3. 開始ページに移動
4. ツールを実行

## 出力ファイル

処理が完了すると、以下のファイルが生成されます：

```
output/
└── {書籍タイトル}/
    ├── screenshots/              # スクリーンショット画像
    │   ├── {書籍タイトル}_page_001.png
    │   ├── {書籍タイトル}_page_002.png
    │   └── ...
    ├── {書籍タイトル}_{日付}.txt    # 抽出されたテキスト
    ├── log_{書籍タイトル}_{日付}.log # 処理ログ
    └── state_{書籍タイトル}.json    # 処理状態（再開用）
```

## NotebookLMへのインポート

1. `output/{書籍タイトル}/{書籍タイトル}_{日付}.txt` を開く
2. NotebookLM (https://notebooklm.google.com/) にアクセス
3. 「Sources」から「Upload」を選択
4. テキストファイルをアップロード
5. 要約やQAを実施

## AI自動コードレビュー

このプロジェクトでは、GitHub Actions + Google Gemini APIを使用した自動コードレビュー機能を提供しています。

### セットアップ

#### 1. GitHub Secretsの設定

リポジトリの設定で以下のSecretを追加してください：

1. GitHub リポジトリページで `Settings` > `Secrets and variables` > `Actions` に移動
2. `New repository secret` をクリック
3. 以下のSecretを追加：
   - **Name**: `GEMINI_API_KEY`
   - **Value**: あなたのGoogle Gemini APIキー（[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)で取得）

注: `GITHUB_TOKEN`は自動的に提供されるため、設定不要です。

#### 2. 動作確認

1. Pull Requestを作成
2. GitHub Actionsが自動的にトリガーされます
3. 数分後、PRにAIによるレビューコメントが投稿されます

### レビュー観点

AIレビューでは以下の観点で自動チェックされます：

1. **バグの可能性**: ロジックエラー、エッジケース、null/undefined参照など
2. **セキュリティ脆弱性**: インジェクション、認証・認可の問題、機密情報の露出など
3. **パフォーマンス問題**: 非効率なアルゴリズム、不要な計算、メモリリークなど
4. **コードの可読性・保守性**: 命名規則、複雑さ、重複コードなど
5. **ベストプラクティス**: 言語固有の慣習、設計パターン、エラーハンドリングなど

### 対象ファイル

以下の拡張子のファイルがレビュー対象です：
- Python: `.py`
- JavaScript/TypeScript: `.js`, `.ts`, `.jsx`, `.tsx`
- その他: `.java`, `.go`, `.rs`, `.cpp`, `.c`, `.h`

### 注意事項

- APIキーは必ずGitHub Secretsで管理してください（コミットしないこと）
- 大規模なPRの場合、レビューに時間がかかる場合があります
- Gemini APIは無料枠があります（月間リクエスト制限あり）
- 機密情報を含むファイル（.env等）はレビュー対象外です
- 使用モデル: `gemini-2.0-flash-exp`（高速・高品質）

詳細は [docs/dev_diary/2025-12-09_自動ソースレビュー環境の構築.md](docs/dev_diary/2025-12-09_自動ソースレビュー環境の構築.md) を参照してください。

## 開発

### プロジェクト構造

```
project/
├── src/                  # ソースコード
│   ├── capture/         # スクリーンショット撮影
│   ├── preprocessor/    # 画像前処理
│   ├── ocr/            # OCR処理
│   ├── output/         # テキスト出力
│   ├── state/          # 状態管理
│   └── utils/          # ユーティリティ
├── tests/               # テストコード
├── config/              # 設定ファイル
├── output/              # 出力先
└── logs/                # ログ出力先
```

### テスト実行

```bash
# 全テスト実行
pytest

# カバレッジ付き実行
pytest --cov=src --cov-report=html

# 特定テスト実行
pytest tests/test_ocr.py
```

### コード品質チェック

```bash
# フォーマット
black src/

# インポート整理
isort src/

# リント
flake8 src/

# 型チェック
mypy src/
```

## ドキュメント

- [requirements.md](requirements.md) - 要件定義書
- [technical_specification.md](technical_specification.md) - 技術仕様書
- [implementation_plan.md](implementation_plan.md) - 実装計画書

## トラブルシューティング

### Kindleウィンドウが検出できない

`config.yaml`の`kindle.window_title`を確認してください。ウィンドウタイトルが"Kindle"と一致しない場合は、実際のタイトルに変更します。

```yaml
kindle:
  window_title: "Kindle"  # 実際のウィンドウタイトルに合わせる
```

### OCRが失敗する

1. Yomitokuが正しくインストールされているか確認
2. 画像前処理設定を調整（`config.yaml`の`preprocessing`セクション）
3. フォールバックのTesseractが動作するか確認

### メモリ不足エラー

`config.yaml`の`performance.max_image_size`を小さくしてください。

```yaml
performance:
  max_image_size: [2000, 2000]  # より小さいサイズに変更
```

## 注意事項

### 著作権について

本ツールは、個人が購入した書籍を個人的に利用する目的でのみ使用してください。
- 第三者への配布や共有は禁止
- 商用利用は禁止
- 著作権法を遵守してください

### 精度について

- OCRの精度は書籍のフォント、レイアウト、画質に依存します
- 図表、数式、特殊文字は正しく認識されない場合があります
- 生成されたテキストは必ず内容を確認してください

## ライセンス

MIT License（予定）

## 貢献

バグ報告や機能要望は、Issueでお願いします。

## 更新履歴

- 2025-10-18: プロジェクト開始、Phase 0 完了（開発環境セットアップ）
