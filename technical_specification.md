# Kindle書籍OCR自動化ワークフロー 技術仕様書

## 1. 開発環境

### 1.1 プログラミング言語
- **Python**: 3.11.5
- **バージョン管理**: pyenv-win
- **プロジェクトローカル設定**: `.python-version` ファイルで管理

### 1.2 仮想環境
- **ツール**: venv (Python標準)
- **仮想環境名**: `venv`
- **作成コマンド**:
  ```bash
  python -m venv venv
  ```
- **アクティベート**:
  ```bash
  # Windows
  venv\Scripts\activate
  ```

### 1.3 開発ツール
- **IDE**: Visual Studio Code
- **推奨VSCode拡張機能**:
  - Python (Microsoft)
  - Pylance
  - Python Test Explorer
  - YAML (Red Hat)

## 2. プロジェクト構成

### 2.1 ディレクトリ構造
```
kindleToText_v2/
├── project/
│   ├── src/                          # ソースコード
│   │   ├── __init__.py
│   │   ├── main.py                   # エントリーポイント
│   │   ├── config/                   # 設定関連
│   │   │   ├── __init__.py
│   │   │   ├── config_loader.py     # 設定読み込み
│   │   │   └── settings.py          # 設定クラス
│   │   ├── capture/                  # スクリーンショット撮影
│   │   │   ├── __init__.py
│   │   │   ├── screenshot.py        # 撮影処理
│   │   │   └── window_manager.py    # ウィンドウ操作
│   │   ├── preprocessor/             # 画像前処理
│   │   │   ├── __init__.py
│   │   │   ├── image_processor.py   # 画像処理
│   │   │   └── filters.py           # フィルター処理
│   │   ├── ocr/                      # OCR処理
│   │   │   ├── __init__.py
│   │   │   ├── yomitoku_engine.py   # Yomitoku処理
│   │   │   ├── tesseract_engine.py  # Tesseract処理
│   │   │   └── ocr_interface.py     # OCRインターフェース
│   │   ├── output/                   # テキスト出力
│   │   │   ├── __init__.py
│   │   │   ├── text_writer.py       # テキスト書き込み
│   │   │   └── formatter.py         # テキスト整形
│   │   ├── state/                    # 状態管理
│   │   │   ├── __init__.py
│   │   │   ├── state_manager.py     # 状態保存・読込
│   │   │   └── progress_tracker.py  # 進捗管理
│   │   └── utils/                    # ユーティリティ
│   │       ├── __init__.py
│   │       ├── logger.py            # ロギング
│   │       └── validators.py        # バリデーション
│   ├── tests/                        # テストコード
│   │   ├── __init__.py
│   │   ├── test_capture.py
│   │   ├── test_preprocessor.py
│   │   ├── test_ocr.py
│   │   ├── test_output.py
│   │   ├── test_state.py
│   │   └── fixtures/                # テスト用データ
│   ├── config/                       # 設定ファイル
│   │   ├── config.yaml              # メイン設定
│   │   └── config.example.yaml      # 設定サンプル
│   ├── output/                       # 出力先
│   │   └── .gitkeep
│   ├── logs/                         # ログ出力先
│   │   └── .gitkeep
│   ├── venv/                         # 仮想環境（Git管理外）
│   ├── requirements.txt              # 依存パッケージ
│   ├── requirements-dev.txt          # 開発用依存パッケージ
│   ├── .python-version               # Pythonバージョン指定
│   ├── .gitignore
│   ├── README.md
│   ├── requirements.md               # 要件定義書
│   └── technical_specification.md   # 本ドキュメント
```

### 2.2 設定ファイル構成
- **フォーマット**: YAML
- **配置**: `config/config.yaml`

## 3. 技術スタック

### 3.1 主要ライブラリ

#### 3.1.1 スクリーンショット・ウィンドウ操作
```
pyautogui==0.9.54          # スクリーンショット撮影
mss==9.0.1                 # 高速スクリーンショット
pygetwindow==0.0.9         # ウィンドウ情報取得
pywinauto==0.6.8           # Windows GUI自動化
```

#### 3.1.2 画像処理
```
Pillow==10.4.0             # 画像処理
opencv-python==4.10.0      # 高度な画像処理
numpy==1.26.4              # 数値計算
```

#### 3.1.3 OCR
```
yomitoku                   # 日本語OCR（メイン）
pytesseract==0.3.13        # Tesseract OCRラッパー（フォールバック）
```

#### 3.1.4 設定・データ管理
```
PyYAML==6.0.2              # YAML設定ファイル読み込み
python-dotenv==1.0.1       # 環境変数管理
```

#### 3.1.5 CLI・UI
```
click==8.1.7               # CLIフレームワーク
tqdm==4.66.5               # プログレスバー
colorama==0.4.6            # ターミナルカラー出力
```

#### 3.1.6 ユーティリティ
```
loguru==0.7.2              # ロギング
python-dateutil==2.9.0     # 日時処理
```

### 3.2 開発・テスト用ライブラリ
```
pytest==8.3.2              # テストフレームワーク
pytest-cov==5.0.0          # カバレッジ測定
pytest-mock==3.14.0        # モック機能
black==24.8.0              # コードフォーマッター
flake8==7.1.1              # リンター
mypy==1.11.2               # 型チェック
isort==5.13.2              # インポート文整理
```

## 4. アーキテクチャ設計

### 4.1 システムアーキテクチャ
```
┌─────────────────────────────────────────────────────────┐
│                    CLI Interface                        │
│                    (main.py)                            │
└────────────────┬────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────┐
│              Workflow Controller                        │
│         (メイン制御・進捗管理)                           │
└─┬──┬──┬──┬──┬─────────────────────────────────────────┘
  │  │  │  │  │
  │  │  │  │  └──> State Manager (状態管理)
  │  │  │  │
  │  │  │  └──────> Text Writer (テキスト出力)
  │  │  │
  │  │  └─────────> OCR Engine (OCR処理)
  │  │               ├─ Yomitoku (優先)
  │  │               └─ Tesseract (フォールバック)
  │  │
  │  └────────────> Image Preprocessor (画像前処理)
  │
  └───────────────> Screenshot Capture (撮影)
                     └─ Window Manager (ウィンドウ操作)
```

### 4.2 データフロー
```
1. 初期化
   ├─ 設定ファイル読み込み
   ├─ 書籍タイトル入力
   ├─ 状態ファイル確認（再開判定）
   └─ 出力ディレクトリ作成

2. メインループ (各ページ)
   ├─ Kindle for PCウィンドウをアクティブ化
   ├─ スクリーンショット撮影
   │   └─ screenshots/{書籍名}_page_{連番}.png
   ├─ 画像前処理
   │   ├─ トリミング
   │   ├─ ノイズ除去
   │   ├─ コントラスト調整
   │   ├─ 傾き補正
   │   └─ 二値化
   ├─ OCR処理
   │   ├─ Yomitoku実行 (第一選択)
   │   ├─ エラー時 → Tesseract実行
   │   └─ テキスト抽出
   ├─ テキスト整形
   │   ├─ 見出し認識
   │   ├─ 段落整理
   │   └─ 不要文字除去
   ├─ テキストファイルに追記
   ├─ 状態保存 (10ページごと)
   ├─ 進捗表示更新
   └─ 次ページへ遷移

3. 完了処理
   ├─ 最終状態保存
   ├─ ログファイル保存
   └─ 完了通知
```

### 4.3 モジュール設計

#### 4.3.1 main.py (エントリーポイント)
- CLI引数解析
- ワークフロー実行制御
- エラーハンドリング

#### 4.3.2 capture モジュール
**責務**: Kindle for PCのスクリーンショット撮影

**主要クラス**:
- `WindowManager`: ウィンドウ検出・アクティブ化
- `ScreenshotCapture`: スクリーンショット撮影・保存

**主要メソッド**:
- `find_kindle_window()`: Kindleウィンドウ検出
- `activate_window()`: ウィンドウアクティブ化
- `capture_screen(region)`: 画面キャプチャ
- `save_screenshot(image, path)`: 画像保存

#### 4.3.3 preprocessor モジュール
**責務**: 撮影画像の前処理（精度優先）

**主要クラス**:
- `ImageProcessor`: 画像処理メインクラス
- `ImageFilters`: 各種フィルター実装

**主要メソッド**:
- `remove_noise(image)`: ノイズ除去
- `adjust_contrast(image)`: コントラスト調整
- `correct_skew(image)`: 傾き補正
- `trim_margins(image)`: 余白除去
- `binarize(image)`: 二値化処理
- `optimize_for_ocr(image)`: OCR最適化（統合処理）

#### 4.3.4 ocr モジュール
**責務**: テキスト抽出

**主要クラス**:
- `OCRInterface`: OCRエンジン抽象インターフェース
- `YomitokuEngine`: Yomitoku実装
- `TesseractEngine`: Tesseract実装

**主要メソッド**:
- `extract_text(image)`: テキスト抽出
- `extract_with_layout(image)`: レイアウト情報付き抽出
- `detect_headings(layout_data)`: 見出し検出

#### 4.3.5 output モジュール
**責務**: テキストファイル出力

**主要クラス**:
- `TextWriter`: テキスト書き込み
- `TextFormatter`: テキスト整形

**主要メソッド**:
- `append_text(text, file_path)`: テキスト追記
- `format_headings(text)`: 見出し整形
- `clean_text(text)`: テキストクリーニング

#### 4.3.6 state モジュール
**責務**: 処理状態の保存・復元

**主要クラス**:
- `StateManager`: 状態管理
- `ProgressTracker`: 進捗追跡

**状態ファイル構造** (JSON):
```json
{
  "book_title": "書籍タイトル",
  "start_datetime": "2025-10-18T10:00:00",
  "last_update": "2025-10-18T11:30:00",
  "current_page": 150,
  "total_pages": 500,
  "processed_pages": [1, 2, 3, ..., 150],
  "failed_pages": [42, 87],
  "output_file": "output/書籍タイトル/書籍タイトル_20251018.txt",
  "screenshot_dir": "output/書籍タイトル/screenshots/",
  "status": "in_progress"
}
```

**主要メソッド**:
- `save_state(state_data)`: 状態保存
- `load_state(book_title)`: 状態読み込み
- `update_progress(page_num)`: 進捗更新
- `can_resume()`: 再開可能判定

#### 4.3.7 config モジュール
**責務**: 設定管理

**設定ファイル例** (`config/config.yaml`):
```yaml
# Kindle for PC設定
kindle:
  window_title: "Kindle"  # Kindleウィンドウのタイトル文字列
  page_turn_key: "Right"  # ページ送りキー
  page_turn_delay: 1.5    # ページ送り後の待機時間（秒）

# スクリーンショット設定
screenshot:
  format: "png"           # 保存形式
  quality: 95             # 画質（1-100）
  region:                 # キャプチャ領域（自動検出の場合null）
    x: null
    y: null
    width: null
    height: null

# 画像前処理設定（精度優先）
preprocessing:
  noise_reduction:
    enabled: true
    kernel_size: 3
  contrast:
    enabled: true
    clip_limit: 2.0
    tile_grid_size: [8, 8]
  skew_correction:
    enabled: true
    angle_threshold: 0.5
  margin_trim:
    enabled: true
    threshold: 240
  binarization:
    enabled: true
    method: "adaptive"    # "adaptive" or "otsu"
    block_size: 11
    c: 2

# OCR設定
ocr:
  primary_engine: "yomitoku"
  fallback_engine: "tesseract"
  yomitoku:
    model_path: null      # デフォルトモデル使用
    confidence_threshold: 0.6
  tesseract:
    lang: "jpn"
    config: "--psm 6"     # Page segmentation mode
    confidence_threshold: 0.5

# 出力設定
output:
  base_dir: "output"
  encoding: "utf-8"
  include_metadata: true  # メタデータ（処理日時等）をファイル先頭に含む

# 状態管理設定
state:
  save_interval: 10       # 状態保存間隔（ページ数）
  auto_save_on_error: true

# ログ設定
logging:
  level: "INFO"           # DEBUG, INFO, WARNING, ERROR
  console: true
  file: true
  file_path: "logs/{book_title}_{date}.log"
  rotation: "10 MB"
  retention: "30 days"

# 見出し認識設定
heading_detection:
  enabled: true
  font_size_threshold: 1.2  # 通常テキストの何倍で見出しと判定
  position_based: true       # 行位置で判定
```

#### 4.3.8 utils モジュール
**責務**: 共通ユーティリティ

**主要機能**:
- ロギング設定
- ファイル名バリデーション
- 日時フォーマット
- エラーハンドリング

## 5. CLI設計

### 5.1 コマンドライン引数
```bash
python src/main.py [OPTIONS]

Options:
  --title TEXT              書籍タイトル（必須）
  --start-page INTEGER      開始ページ（デフォルト: 1）
  --end-page INTEGER        終了ページ（デフォルト: 自動検出）
  --config PATH             設定ファイルパス（デフォルト: config/config.yaml）
  --resume                  前回の処理を再開
  --debug                   デバッグモード
  --help                    ヘルプ表示
```

### 5.2 実行例
```bash
# 新規処理開始
python src/main.py --title "マイブック"

# 特定ページ範囲を指定
python src/main.py --title "マイブック" --start-page 10 --end-page 100

# 前回の続きから再開
python src/main.py --title "マイブック" --resume

# カスタム設定ファイル使用
python src/main.py --title "マイブック" --config custom_config.yaml
```

### 5.3 プログレス表示
```
Kindle to Text Converter
========================
Book: マイブック
Output: output/マイブック/

[Processing] Page 150/500 (30%)
├─ Capturing screenshot... ✓
├─ Preprocessing image... ✓
├─ Running OCR (Yomitoku)... ✓
├─ Saving text... ✓
└─ Estimated time remaining: 25min 30sec

[State saved] Last checkpoint: Page 150
```

## 6. エラーハンドリング

### 6.1 エラー分類と対応

#### 6.1.1 致命的エラー（処理中断）
- Kindleウィンドウが見つからない
- 設定ファイル読み込み失敗
- 書籍タイトル未入力

**対応**: エラーメッセージ表示後、状態保存して終了

#### 6.1.2 回復可能エラー（リトライ）
- スクリーンショット失敗
- OCRエラー（フォールバックへ切替）
- 一時的なファイルI/Oエラー

**対応**: 3回までリトライ、失敗時はスキップ or 中断選択

#### 6.1.3 警告（処理継続）
- OCR信頼度低下
- 画像品質低下
- ページ送り遅延

**対応**: ログ記録、処理継続

### 6.2 エラーログ形式
```
[2025-10-18 11:30:45] ERROR - Page 42
  Type: OCRError
  Engine: Yomitoku
  Message: Failed to extract text with confidence > 0.6
  Action: Fallback to Tesseract
  Result: Success (Tesseract)
```

## 7. テスト戦略

### 7.1 テスト構成
```
tests/
├── test_capture.py          # スクリーンショット機能
├── test_preprocessor.py     # 画像前処理
├── test_ocr.py              # OCR処理
├── test_output.py           # テキスト出力
├── test_state.py            # 状態管理
└── fixtures/                # テスト用データ
    ├── sample_screenshots/
    └── sample_texts/
```

### 7.2 テスト種類

#### 7.2.1 ユニットテスト
- 各モジュールの個別機能テスト
- モック使用でOCR APIをシミュレート
- カバレッジ目標: 80%以上

#### 7.2.2 統合テスト
- モジュール間連携テスト
- サンプル画像を使用した全体フロー確認

#### 7.2.3 E2Eテスト（手動）
- 実際のKindleアプリでの動作確認
- 書籍1冊（少ページ）での完全フロー確認

### 7.3 テスト実行
```bash
# 全テスト実行
pytest

# カバレッジ付き実行
pytest --cov=src --cov-report=html

# 特定テスト実行
pytest tests/test_ocr.py

# デバッグモード
pytest -v -s
```

## 8. 開発ワークフロー

### 8.1 初期セットアップ
```bash
# 1. リポジトリ移動
cd c:\Users\ryoji.tanabe\自己研鑽\kindleToText_v2\project

# 2. Pythonバージョン確認（3.11.5が設定済み）
python --version

# 3. 仮想環境作成
python -m venv venv

# 4. 仮想環境アクティベート
venv\Scripts\activate

# 5. 依存パッケージインストール
pip install --upgrade pip
pip install -r requirements.txt

# 6. 開発用パッケージインストール
pip install -r requirements-dev.txt

# 7. 設定ファイル作成
copy config\config.example.yaml config\config.yaml
# 設定ファイルを編集

# 8. Yomitokuインストール（公式手順に従う）
# https://kotaro-kinoshita.github.io/yomitoku/installation/

# 9. テスト実行
pytest
```

### 8.2 コーディング規約
- **スタイル**: PEP 8準拠
- **フォーマッター**: Black (line-length: 100)
- **リンター**: Flake8
- **型ヒント**: 必須（mypy でチェック）
- **Docstring**: Google Style

### 8.3 コード品質チェック
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

### 8.4 Git管理
```.gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Output
output/
logs/
*.log

# State files
state_*.json

# Config (個人設定は除外)
config/config.yaml

# Cache
.pytest_cache/
.mypy_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
```

## 9. パフォーマンス最適化

### 9.1 精度優先の方針
- 処理速度よりもOCR精度を優先
- 画像前処理を丁寧に実施
- 必要に応じて複数エンジンの結果を比較

### 9.2 最適化ポイント
1. **画像処理**: OpenCVによる高速処理
2. **並列処理**: 将来的に複数ページの並列処理を検討
3. **メモリ管理**: 大量画像処理時のメモリリーク防止
4. **ファイルI/O**: バッファリングによる書き込み最適化

### 9.3 想定処理時間
- 1ページあたり: 5〜10秒（精度優先設定）
- 300ページの書籍: 25〜50分
- 500ページの書籍: 42〜83分

## 10. セキュリティとプライバシー

### 10.1 データ保護
- ローカル環境のみで処理（オフライン）
- 外部サーバーへのデータ送信なし
- 生成ファイルはユーザーのローカルディスクのみに保存

### 10.2 著作権遵守
- 個人利用に限定
- 第三者への配布禁止
- 商用利用禁止

## 11. 今後の拡張計画

### 11.1 Phase 1（初期実装）
- 基本機能実装
- Yomitoku + Tesseractの2エンジン対応
- CLI インターフェース
- 状態管理・再開機能

### 11.2 Phase 2（機能拡張）
- GUI追加（tkinter）
- 並列処理対応
- 目次の自動抽出
- 複数書籍のバッチ処理

### 11.3 Phase 3（高度化）
- 図表の認識とスキップ
- PDF出力対応
- クラウドストレージ連携
- NotebookLM自動アップロード

## 12. 依存関係管理

### 12.1 requirements.txt
```
# Core dependencies
pyautogui==0.9.54
mss==9.0.1
pygetwindow==0.0.9
pywinauto==0.6.8
Pillow==10.4.0
opencv-python==4.10.0
numpy==1.26.4
pytesseract==0.3.13
PyYAML==6.0.2
python-dotenv==1.0.1
click==8.1.7
tqdm==4.66.5
colorama==0.4.6
loguru==0.7.2
python-dateutil==2.9.0
```

### 12.2 requirements-dev.txt
```
# Development dependencies
pytest==8.3.2
pytest-cov==5.0.0
pytest-mock==3.14.0
black==24.8.0
flake8==7.1.1
mypy==1.11.2
isort==5.13.2
```

### 12.3 Yomitokuインストール
公式ドキュメントに従ってインストール:
https://kotaro-kinoshita.github.io/yomitoku/installation/

## 13. トラブルシューティング

### 13.1 よくある問題

#### Kindleウィンドウが検出できない
- ウィンドウタイトルが設定と一致しているか確認
- `config.yaml` の `kindle.window_title` を調整

#### OCRが失敗する
- 画像前処理設定を調整
- Yomitokuのモデルが正しくインストールされているか確認
- フォールバックのTesseractが動作するか確認

#### メモリ不足エラー
- 処理する画像サイズを小さくする
- バッチサイズを調整（将来実装時）

#### 文字化けが発生
- 出力ファイルのエンコーディングをUTF-8に設定
- テキストエディタ側のエンコーディング設定を確認

## 14. リファレンス

### 14.1 公式ドキュメント
- Python 3.11: https://docs.python.org/3.11/
- Yomitoku: https://kotaro-kinoshita.github.io/yomitoku/
- Tesseract: https://github.com/tesseract-ocr/tesseract
- OpenCV: https://docs.opencv.org/
- Click: https://click.palletsprojects.com/

### 14.2 関連ドキュメント
- [requirements.md](requirements.md) - 要件定義書
- [README.md](README.md) - プロジェクト概要（作成予定）
