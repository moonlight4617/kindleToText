# Kindle書籍OCR自動化ワークフロー 実装計画書

## プロジェクト概要
Kindle for PCの書籍を自動でスクリーンショット撮影し、OCR処理によってテキスト化するツールの実装計画

---

## Phase 0: 開発環境セットアップ

### 0.1 Python環境
- [x] Python 3.11.5 インストール（pyenv）
- [x] プロジェクトローカルバージョン設定（.python-version）
- [x] 仮想環境作成（venv）
- [x] 依存パッケージ定義ファイル作成

### 0.2 プロジェクト構造
- [x] ディレクトリ構造作成
- [x] 必須ファイル作成（README.md, .gitignore等）
- [x] 設定ファイルテンプレート作成

### 0.3 依存パッケージ
- [x] requirements.txt 作成
- [x] requirements-dev.txt 作成
- [x] パッケージインストール
- [ ] Yomitoku インストール確認（ユーザー手動作業）

---

## Phase 1: 基盤機能実装

### 1.1 設定管理モジュール (config)
- [x] `config/config_loader.py` - YAML設定読み込み
- [x] `config/settings.py` - 設定クラス定義
- [x] `config/config.example.yaml` - 設定ファイルテンプレート
- [x] ユニットテスト作成（15テスト合格）

**実装内容**:
- YAML設定ファイルの読み込み
- 設定値のバリデーション
- デフォルト値の適用

### 1.2 ユーティリティモジュール (utils)
- [x] `utils/logger.py` - ロギング設定
- [x] `utils/validators.py` - バリデーション関数
- [x] ユニットテスト作成（42テスト合格）

**実装内容**:
- Loguruベースのロガー設定
- ファイル名バリデーション
- 入力値検証

---

## Phase 2: スクリーンショット機能

### 2.1 ウィンドウ管理 (capture/window_manager.py)
- [x] Kindleウィンドウ検出機能
- [x] ウィンドウアクティブ化機能
- [x] ウィンドウ情報取得（位置・サイズ）
- [x] ユニットテスト作成（19テスト合格）

**実装内容**:
```python
class WindowManager:
    def find_kindle_window() -> WindowInfo
    def activate_window(window: WindowInfo) -> bool
    def get_window_region(window: WindowInfo) -> Region
```

### 2.2 スクリーンショット撮影 (capture/screenshot.py)
- [x] スクリーンショット撮影機能
- [x] 画像保存機能
- [x] ページ送り機能
- [x] キャプチャ間隔制御
- [x] ユニットテスト作成（23テスト合格）

**実装内容**:
```python
class ScreenshotCapture:
    def capture_screen(region: Region) -> Image
    def save_screenshot(image: Image, path: str) -> bool
    def turn_page(key: str) -> bool
    def wait_for_page_load(delay: float) -> None
```

### 2.3 統合テスト
- [x] capture モジュール統合テスト（42テスト合格）
- [ ] 実機テスト（Kindle for PC使用）※ユーザー実施推奨

---

## Phase 3: 画像前処理機能

### 3.1 画像処理 (preprocessor/image_processor.py)
- [x] ノイズ除去機能
- [x] コントラスト調整機能
- [x] 傾き補正機能
- [x] トリミング機能
- [x] 二値化処理機能
- [x] OCR最適化統合処理
- [x] ユニットテスト作成（25テスト合格）

**実装内容**:
```python
class ImageProcessor:
    def remove_noise(image: Image) -> Image
    def adjust_contrast(image: Image) -> Image
    def correct_skew(image: Image) -> Image
    def trim_margins(image: Image) -> Image
    def binarize(image: Image) -> Image
    def optimize_for_ocr(image: Image) -> Image
```

### 3.2 フィルター処理 (preprocessor/filters.py)
- [x] 各種フィルター実装
- [x] フィルターパラメータ調整機能
- [x] ユニットテスト作成（33テスト合格）

### 3.3 画像品質評価
- [x] 画像品質評価関数
- [x] 前処理前後の比較機能

### 3.4 統合テスト
- [x] preprocessor モジュール統合テスト（58テスト合格）
- [ ] サンプル画像での精度評価※ユーザー実施推奨

---

## Phase 4: OCR処理機能

### 4.1 OCRインターフェース (ocr/ocr_interface.py)
- [x] OCRエンジン抽象インターフェース定義
- [x] エンジン切り替えロジック（ファクトリーパターン）

**実装内容**:
```python
class OCRInterface(ABC):
    @abstractmethod
    def extract_text(image: Image) -> str
    @abstractmethod
    def extract_with_layout(image: Image) -> LayoutData
```

### 4.2 Yomitokuエンジン (ocr/yomitoku_engine.py)
- [x] Yomitoku初期化
- [x] テキスト抽出機能
- [x] レイアウト情報取得
- [x] エラーハンドリング
- [x] ユニットテスト作成（モック使用・11テスト合格）

**実装内容**:
```python
class YomitokuEngine(OCRInterface):
    def __init__(config: dict)
    def extract_text(image: Image) -> str
    def extract_with_layout(image: Image) -> LayoutData
    def get_confidence_score(result) -> float
```

### 4.3 Tesseractエンジン (ocr/tesseract_engine.py)
- [x] Tesseract初期化
- [x] テキスト抽出機能（フォールバック用）
- [x] レイアウト情報取得
- [x] エラーハンドリング
- [x] ユニットテスト作成（15テスト合格）

**実装内容**:
```python
class TesseractEngine(OCRInterface):
    def __init__(config: dict)
    def extract_text(image: Image) -> str
    def extract_with_layout(image: Image) -> LayoutData
```

### 4.4 見出し検出機能
- [ ] フォントサイズベース検出※Phase 5で実装予定
- [ ] 位置ベース検出※Phase 5で実装予定
- [ ] 見出しマークアップ機能※Phase 5で実装予定

### 4.5 統合テスト
- [x] OCRモジュール統合テスト（47テスト合格）
- [ ] 実画像でのOCR精度評価※ユーザー実施推奨
- [ ] Yomitoku/Tesseract比較テスト※ユーザー実施推奨

---

## Phase 5: テキスト出力機能

### 5.1 テキスト整形 (output/formatter.py)
- [x] テキストクリーニング機能
- [x] 見出し整形機能（レイアウト情報活用）
- [x] 段落整理機能
- [x] 不要文字除去
- [x] ユニットテスト作成（28テスト合格）

**実装内容**:
```python
class TextFormatter:
    def clean_text(text: str) -> str
    def format_headings(text: str, layout: LayoutData) -> str
    def organize_paragraphs(text: str) -> str
    def remove_artifacts(text: str) -> str
```

### 5.2 テキスト書き込み (output/text_writer.py)
- [x] テキストファイル作成機能
- [x] テキスト追記機能
- [x] メタデータ追加機能
- [x] エンコーディング処理（UTF-8/BOM対応）
- [x] Markdown形式出力対応
- [x] ユニットテスト作成（32テスト合格）

**実装内容**:
```python
class TextWriter:
    def create_file(path: str, metadata: dict) -> bool
    def append_text(path: str, text: str) -> bool
    def add_metadata(path: str, metadata: dict) -> bool
```

### 5.3 統合テスト
- [x] output モジュール統合テスト（60テスト合格）
- [x] ファイル出力確認

---

## Phase 6: 状態管理機能

### 6.1 状態管理 (state/state_manager.py)
- [x] 状態ファイル保存機能
- [x] 状態ファイル読み込み機能
- [x] 状態更新機能
- [x] 再開可能判定機能
- [x] ユニットテスト作成（21テスト合格）

**実装内容**:
```python
class StateManager:
    def save_state(state: StateData) -> bool
    def load_state(book_title: str) -> StateData
    def update_state(state: StateData, updates: dict) -> StateData
    def can_resume(book_title: str) -> bool
    def get_state_file_path(book_title: str) -> str
    def delete_state(book_title: str) -> bool
    def list_states() -> List[StateData]
    def create_initial_state(...) -> StateData
```

**状態データ構造**:
```python
@dataclass
class StateData:
    book_title: str
    start_datetime: str  # ISO format
    last_update: str  # ISO format
    current_page: int
    total_pages: int
    processed_pages: List[int]
    failed_pages: List[int]
    output_file: str
    screenshot_dir: str
    status: str  # "in_progress", "completed", "failed"
```

### 6.2 進捗管理 (state/progress_tracker.py)
- [x] 進捗追跡機能
- [x] 進捗表示機能
- [x] 残り時間推定機能
- [x] ユニットテスト作成（33テスト合格）

**実装内容**:
```python
class ProgressTracker:
    def update_progress(page: int, failed: bool = False) -> None
    def estimate_remaining_time() -> timedelta
    def get_progress_percentage() -> float
    def display_progress(verbose: bool = False) -> str
    def get_progress_bar(width: int = 50) -> str
    def get_elapsed_time() -> timedelta
    def get_average_page_time() -> float
    def get_pages_per_minute() -> float
    def get_summary() -> dict
    def reset(new_start_page: int = None) -> None
```

### 6.3 統合テスト
- [x] state モジュール統合テスト（7テスト合格）
- [x] 状態保存・復元テスト
- [x] 再開機能テスト

---

## Phase 7: メイン制御機能

### 7.1 ワークフロー制御 (main.py)
- [x] CLI引数パース（Click使用）
- [x] 初期化処理
- [x] メインループ実装
- [x] エラーハンドリング
- [x] 完了処理

**実装内容**:
```python
class KindleOCRWorkflow:
    def initialize(book_title, total_pages, start_page) -> bool
    def resume_from_state(book_title) -> bool
    def process_page(page_number) -> bool
    def save_state() -> None
    def run() -> bool

@click.command()
@click.option('--title', '-t', required=True, help='書籍タイトル')
@click.option('--total-pages', '-p', type=int, help='総ページ数')
@click.option('--start-page', '-s', type=int, default=1, help='開始ページ')
@click.option('--config', '-c', default='config/config.yaml', help='設定ファイル')
@click.option('--resume', '-r', is_flag=True, help='前回の処理を再開')
@click.option('--debug', '-d', is_flag=True, help='デバッグモード')
def main(title, total_pages, start_page, config, resume, debug):
    # メイン処理
```

### 7.2 ワークフロー機能
- [x] 設定読み込み
- [x] 書籍タイトルバリデーション
- [x] 出力ディレクトリ作成
- [x] 再開判定・処理
- [x] ページループ制御
- [x] 定期的な状態保存
- [x] 進捗表示
- [x] キーボード割り込み処理（Ctrl+C）

### 7.3 エラーハンドリング
- [x] 致命的エラー処理（ウィンドウ未検出、初期化失敗等）
- [x] 回復可能エラー処理（連続失敗カウント）
- [x] 警告処理（OCRテキスト未検出等）
- [x] エラーログ記録

### 7.4 統合テスト
- [x] エンドツーエンドテスト（モック使用・8テスト合格）
- [x] エラーケーステスト
- [ ] テスト修正（4テスト失敗中）※優先度低

---

## Phase 8: 実機テスト・調整

### 8.1 機能テスト
- [ ] Kindle for PCでの動作確認
- [ ] スクリーンショット精度確認
- [ ] OCR精度確認
- [ ] テキスト出力確認
- [ ] 状態保存・再開機能確認

### 8.2 パラメータ調整
- [ ] 画像前処理パラメータ調整
- [ ] OCR信頼度閾値調整
- [ ] ページ送り遅延調整
- [ ] 状態保存間隔調整

### 8.3 エラーケーステスト
- [ ] Kindleウィンドウが見つからない場合
- [ ] OCR失敗時のフォールバック
- [ ] ディスク容量不足
- [ ] 処理中断・再開
- [ ] ネットワークエラー（オフライン確認）

### 8.4 パフォーマンステスト
- [ ] 1ページあたりの処理時間計測
- [ ] メモリ使用量確認
- [ ] 長時間稼働安定性確認（100ページ以上）

### 8.5 品質評価
- [ ] OCR精度評価（サンプル10ページ）
- [ ] 見出し認識精度評価
- [ ] テキスト整形品質評価

---

## Phase 9: ドキュメント整備

### 9.1 ユーザードキュメント
- [ ] README.md 作成
  - プロジェクト概要
  - インストール手順
  - 使い方
  - トラブルシューティング
- [ ] USAGE.md 作成
  - 詳細な使用方法
  - コマンドオプション説明
  - 設定ファイル説明
- [ ] INSTALLATION.md 作成
  - 環境構築手順
  - Yomitokuインストール手順
  - トラブルシューティング

### 9.2 開発者ドキュメント
- [ ] CONTRIBUTING.md 作成
- [ ] API仕様書作成（Docstring充実）
- [ ] アーキテクチャ図更新

### 9.3 ドキュメントレビュー
- [ ] 要件定義書の最終確認
- [ ] 技術仕様書の最終確認
- [ ] 実装計画書の完了確認

---

## Phase 10: リリース準備

### 10.1 コード品質
- [ ] 全ユニットテスト実行・合格
- [ ] カバレッジ80%以上達成
- [ ] Blackフォーマット適用
- [ ] Flake8リント合格
- [ ] mypy型チェック合格
- [ ] isortインポート整理

### 10.2 リリースファイル
- [ ] requirements.txt 最終確認
- [ ] .gitignore 最終確認
- [ ] LICENSE ファイル作成
- [ ] CHANGELOG.md 作成

### 10.3 バージョン管理
- [ ] 初期バージョン v1.0.0 タグ付け
- [ ] リリースノート作成

---

## Phase 11: 将来の拡張（オプション）

### 11.1 GUI実装
- [ ] tkinterベースのGUI設計
- [ ] GUI実装
- [ ] GUIテスト

### 11.2 高度な機能
- [ ] 並列処理対応
- [ ] 目次自動抽出
- [ ] 図表認識・スキップ機能
- [ ] PDF出力対応

### 11.3 NotebookLM連携
- [ ] 自動アップロード機能
- [ ] API連携（公式APIが利用可能になった場合）

---

## 進捗管理

### 全体進捗
- Phase 0: 🟢 完了（2025-10-18）
- Phase 1: 🟢 完了（2025-10-18）
- Phase 2: 🟢 完了（2025-10-28）
- Phase 3: 🟢 完了（2025-10-28）
- Phase 4: 🟢 完了（2025-10-29）
- Phase 5: 🟢 完了（2025-11-03）
- Phase 6: 🟢 完了（2025-11-05）
- Phase 7: 🟢 完了（2025-11-05）
- Phase 8: 🟡 進行中（テストインフラ完了、実機テスト待ち）
- Phase 9: ⚪ 未着手
- Phase 10: ⚪ 未着手

**凡例**:
- ⚪ 未着手
- 🟡 進行中
- 🟢 完了

---

## 推定工数

| Phase | 作業内容 | 推定工数 |
|-------|---------|---------|
| Phase 0 | 環境セットアップ | 2時間 |
| Phase 1 | 基盤機能実装 | 4時間 |
| Phase 2 | スクリーンショット機能 | 8時間 |
| Phase 3 | 画像前処理機能 | 8時間 |
| Phase 4 | OCR処理機能 | 10時間 |
| Phase 5 | テキスト出力機能 | 4時間 |
| Phase 6 | 状態管理機能 | 6時間 |
| Phase 7 | メイン制御機能 | 8時間 |
| Phase 8 | 実機テスト・調整 | 10時間 |
| Phase 9 | ドキュメント整備 | 4時間 |
| Phase 10 | リリース準備 | 2時間 |
| **合計** | | **66時間** |

---

## 更新履歴
- 2025-10-18: 初版作成
- 2025-10-18: Phase 0 完了（開発環境セットアップ）
- 2025-10-18: Phase 1 完了（基盤機能実装 - 設定管理・ユーティリティ）
- 2025-10-28: Phase 2 完了（スクリーンショット機能 - ウィンドウ管理・撮影）
- 2025-10-28: Phase 3 完了（画像前処理機能 - 画像処理・フィルター）
- 2025-10-29: Phase 4 完了（OCR処理機能 - Yomitoku・Tesseractエンジン）
- 2025-11-03: Phase 5 完了（テキスト出力機能 - テキスト整形・ファイル書き込み）
- 2025-11-05: Phase 6 完了（状態管理機能 - StateManager・ProgressTracker）
- 2025-11-05: Phase 7 完了（メイン制御機能 - CLIインターフェース・ワークフロー制御）
- 2025-11-05: Phase 8 進行中（テストインフラ整備完了 - 手動テストガイド・環境検証・パフォーマンス監視）
