# 2025-11-05

## 実施内容

Phase 8: 実機テスト・調整 - テストインフラ準備

- 手動テストガイドの作成
- 環境検証スクリプトの作成
- パフォーマンス監視スクリプトの作成
- テスト結果記録テンプレートの作成

### 目的・背景

Phase 7 までにすべてのコア機能が実装完了したため、Phase 8 では実際の Kindle for PC を使用した動作確認と調整を行う。本フェーズでは、実機テストを効率的に実施するためのインフラ（ガイド、検証スクリプト、監視ツール）を整備する。

### 所要時間／作業時間の見積もりと実績

- **見積もり**: 6時間
- **実績**: 約2時間
  - 手動テストガイド作成: 1時間
  - 環境検証スクリプト作成: 0.5時間
  - パフォーマンス監視スクリプト作成: 0.5時間
  - テスト結果テンプレート作成: 0.2時間

### 実装した機能

#### 1. 手動テストガイド ([docs/MANUAL_TESTING.md](../MANUAL_TESTING.md))

実機テストの手順を詳細に記載したドキュメント。

**テストシナリオ（全7種類）**:

1. **テスト1: 基本動作確認**
   - 目的: ツールが正常に起動し、基本的なOCR処理が実行できることを確認
   - 手順: 10ページの書籍でOCR処理を実行
   - 確認項目:
     - Kindleウィンドウの自動検出
     - スクリーンショットの撮影・保存
     - ページの自動送り
     - OCR実行とテキスト抽出
     - 進捗バーの表示
     - テキストファイルの生成

2. **テスト2: 中断・再開機能**
   - 目的: 処理を中断しても、再開できることを確認
   - 手順:
     1. 20ページで処理開始
     2. 5～10ページで Ctrl+C で中断
     3. --resume オプションで再開
   - 確認項目:
     - 状態ファイルの保存
     - 中断メッセージの表示
     - 前回の続きから再開
     - テキストの追記モード保存

3. **テスト3: エラーハンドリング**
   - 3-1: Kindle for PC未起動時のエラー処理
   - 3-2: 無効なOCRエンジン指定時のエラー処理
   - 3-3: ディスク容量不足のシミュレーション

4. **テスト4: パラメータ調整**
   - 4-1: ページ送り遅延の最適化（0.5～2.0秒）
   - 4-2: 画像前処理パラメータの最適化
   - 4-3: OCR信頼度閾値の調整

5. **テスト5: パフォーマンス測定**
   - 100ページの処理時間計測
   - メモリ使用量の確認
   - CPU使用率の確認
   - リソースモニタリング

6. **テスト6: OCR精度評価**
   - 10ページのサンプルでOCR精度を定量評価
   - 文字認識率の計算（日本語・英語・全体）
   - よくある誤認識パターンの記録

7. **テスト7: 長時間稼働の安定性**
   - 200ページ以上の処理で安定性を確認
   - メモリリークチェック
   - エラー発生頻度の記録

**トラブルシューティング**:
- Kindle window not found エラー
- OCR結果が空または精度が低い
- ページ送りが速すぎる/遅すぎる
- メモリ不足エラー
- Tesseract not found エラー

#### 2. 環境検証スクリプト ([scripts/validate_environment.py](../../scripts/validate_environment.py))

実機テストの前に、実行環境が正しくセットアップされているかを自動チェック。

**検証項目**:

```python
def main():
    results = {
        "Python Version": check_python_version(),        # Python 3.11+ 確認
        "Required Packages": check_dependencies(),       # 必須パッケージ確認
        "Tesseract OCR": check_tesseract(),             # Tesseract & 言語データ確認
        "Configuration File": check_config_file(),       # config.yaml の存在・読み込み
        "Output Directory": check_output_directory(),    # 出力ディレクトリの書き込み権限
        "Kindle for PC": check_kindle_installation(),   # Kindle for PC のインストール確認
    }
```

**主要機能**:

1. **Python バージョン確認**
   ```python
   def check_python_version():
       version = sys.version_info
       if version.major == 3 and version.minor >= 11:
           logger.success(f"✓ Python {version.major}.{version.minor}.{version.micro}")
           return True
       else:
           logger.error(f"✗ Python 3.11+ required")
           return False
   ```

2. **Tesseract 言語データ確認**
   ```python
   def check_tesseract():
       version = pytesseract.get_tesseract_version()
       langs = pytesseract.get_languages()
       if "jpn" in langs:
           logger.success("✓ Japanese language data (jpn)")
       if "eng" in langs:
           logger.success("✓ English language data (eng)")
   ```

3. **設定ファイルの検証**
   ```python
   def check_config_file():
       config_loader = ConfigLoader(str(config_path))
       config = config_loader.load()
       # 重要な設定項目の存在確認
       if "kindle" in config:
           logger.success("✓ Kindle settings found")
       if "ocr" in config:
           engine = config["ocr"]["primary_engine"]
           logger.info(f"  Primary OCR engine: {engine}")
   ```

**実行例**:
```bash
python scripts/validate_environment.py

================================================================================
Environment Validation for Kindle OCR Tool
================================================================================

✓ Python 3.11.5
✓ click
✓ loguru
✓ Pillow
✓ numpy
✓ opencv-python
✓ pytesseract
✓ pyyaml
✓ pywin32
✓ Tesseract 5.x.x
✓ Japanese language data (jpn)
✓ English language data (eng)
✓ Configuration file loaded: config/config.yaml
✓ Kindle settings found
✓ OCR settings found
  Primary OCR engine: tesseract
✓ Output directory exists: output
✓ Output directory is writable
△ Kindle for PC not found in standard locations

================================================================================
Validation Summary
================================================================================
Python Version            ✓ PASS
Required Packages         ✓ PASS
Tesseract OCR            ✓ PASS
Configuration File       ✓ PASS
Output Directory         ✓ PASS
Kindle for PC            ✗ FAIL
================================================================================
```

#### 3. パフォーマンス監視スクリプト ([scripts/performance_monitor.py](../../scripts/performance_monitor.py))

OCR処理のパフォーマンスを詳細に測定するためのユーティリティ。

**データ構造**:

```python
@dataclass
class PerformanceMetrics:
    timestamp: str
    page_number: int
    screenshot_time: float          # スクリーンショット撮影時間（秒）
    preprocessing_time: float       # 画像前処理時間（秒）
    ocr_time: float                # OCR処理時間（秒）
    total_time: float              # 合計時間（秒）
    memory_usage_mb: float         # メモリ使用量（MB）
    cpu_percent: float             # CPU使用率（%）
```

**主要機能**:

1. **段階別時間計測**
   ```python
   class PerformanceMonitor:
       def start_page(self):
           self.start_time = time.time()

       def start_screenshot(self):
           self.screenshot_start = time.time()

       def end_screenshot(self):
           return time.time() - self.screenshot_start

       # 同様に preprocessing, ocr の計測
   ```

2. **リソース使用量の取得**
   ```python
   def end_page(self, page_number, screenshot_time, preprocessing_time, ocr_time):
       # メモリ使用量取得
       memory_info = self.process.memory_info()
       memory_mb = memory_info.rss / 1024 / 1024

       # CPU使用率取得
       cpu_percent = self.process.cpu_percent(interval=0.1)
   ```

3. **レポート生成**
   ```python
   def generate_report(self) -> dict:
       return {
           "total_pages": total_pages,
           "total_time": sum(total_times),
           "average_time_per_page": sum(total_times) / total_pages,
           "screenshot": {
               "average": sum(screenshot_times) / total_pages,
               "min": min(screenshot_times),
               "max": max(screenshot_times),
           },
           # 同様に preprocessing, ocr, memory, cpu
       }
   ```

4. **レポート表示例**
   ```
   ================================================================================
   Performance Report
   ================================================================================

   Total Pages Processed: 100
   Total Time: 850.23 seconds (14.17 minutes)
   Average Time per Page: 8.50 seconds

   Breakdown by Stage:
     Screenshot:    0.15s (avg) | 0.12s (min) | 0.25s (max)
     Preprocessing: 1.20s (avg) | 0.95s (min) | 1.50s (max)
     OCR:           7.10s (avg) | 5.80s (min) | 9.20s (max)

   Resource Usage:
     Memory: 245.3MB (avg) | 312.8MB (peak)
     CPU:    65.2% (avg) | 95.1% (peak)

   ================================================================================
   ```

5. **メトリクスのJSON出力**
   ```python
   def save_metrics(self, filename: str = None):
       data = [asdict(m) for m in self.metrics]
       with open(filepath, "w", encoding="utf-8") as f:
           json.dump(data, f, ensure_ascii=False, indent=2)
   ```

**統合方法（main.py での使用例）**:
```python
from scripts.performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()

for page in range(start_page, total_pages + 1):
    monitor.start_page()

    monitor.start_screenshot()
    # スクリーンショット処理
    screenshot_time = monitor.end_screenshot()

    monitor.start_preprocessing()
    # 前処理
    preprocessing_time = monitor.end_preprocessing()

    monitor.start_ocr()
    # OCR処理
    ocr_time = monitor.end_ocr()

    monitor.end_page(page, screenshot_time, preprocessing_time, ocr_time)

monitor.print_report()
monitor.save_metrics("performance_results.json")
```

#### 4. テスト結果記録テンプレート ([docs/TEST_RESULTS_TEMPLATE.md](../TEST_RESULTS_TEMPLATE.md))

実機テストの結果を構造化して記録するためのテンプレート。

**構成**:
- 環境情報（ソフトウェア・ハードウェア）
- テスト1～7の結果記録欄（チェックボックス、データ記入欄）
- 総合評価
- 改善が必要な点
- 推奨設定
- 添付資料チェックリスト

**記録項目例（テスト5: パフォーマンス測定）**:
```markdown
### 測定結果

**処理時間**:
- 総処理時間: _____ 分 _____ 秒
- 1ページあたりの平均時間: _____ 秒
- 最速ページ: _____ 秒
- 最遅ページ: _____ 秒

**処理時間の内訳**（平均）:
- スクリーンショット: _____ 秒
- 画像前処理: _____ 秒
- OCR処理: _____ 秒
- ファイル書き込み: _____ 秒

**リソース使用量**:
- ピークメモリ使用量: _____ MB
- 平均メモリ使用量: _____ MB
- 平均CPU使用率: _____ %
- ピークCPU使用率: _____ %
```

### 課題・詰まった点と解決策

#### 1. 手動テストの範囲定義

**課題**: どこまで自動化し、どこまで手動で行うべきか判断が必要。

**解決策**:
- 環境検証は自動化（validate_environment.py）
- パフォーマンス測定は自動化（performance_monitor.py）
- OCR精度評価、エラーケース、実際の書籍での動作確認は手動
- 手動テストの手順を詳細に記載し、再現性を確保

#### 2. パフォーマンス監視の統合方法

**課題**: PerformanceMonitor を main.py に統合すると、コードが複雑になる。

**解決策**:
- PerformanceMonitor はオプショナル（必要時のみ使用）
- 独立したスクリプトとして提供
- デモ実装（demo_usage）を含めて使い方を明示
- 将来的に main.py に統合する場合は、--performance フラグで有効化

#### 3. Kindle for PC の検出

**課題**: Kindle for PC のインストールパスは環境によって異なる。

**解決策**:
- 一般的な3つのインストールパスをチェック
  - `C:\Program Files\Amazon\Kindle\Kindle.exe`
  - `C:\Program Files (x86)\Amazon\Kindle\Kindle.exe`
  - `%LOCALAPPDATA%\Amazon\Kindle\application\Kindle.exe`
- 見つからない場合も警告のみ（致命的エラーとしない）
- 実行時に実際のウィンドウ検出で最終判定

### テスト結果

Phase 8 では自動テストの代わりに、手動テストのインフラを整備。実際のテスト結果は、ユーザーが Kindle for PC で実行した後に記録される。

**作成したスクリプトの動作確認**:

```bash
# 環境検証スクリプトの動作確認
python scripts/validate_environment.py
# → すべての検証項目が正常に動作することを確認

# パフォーマンス監視のデモ実行
python scripts/performance_monitor.py
# → デモでシミュレーション実行し、レポート生成を確認
```

### 使用したツール・技術要素のメモ

- **psutil**: Pythonプロセス・システム情報取得ライブラリ
  - メモリ使用量取得: `process.memory_info().rss`
  - CPU使用率取得: `process.cpu_percent(interval=0.1)`

- **dataclasses**: パフォーマンスメトリクスのデータ構造定義
  - 型ヒント付きデータクラス
  - `asdict()` でJSONシリアライズ

- **pathlib**: パス操作
  - Kindle for PC インストールパスの存在確認
  - クロスプラットフォーム対応

- **pytesseract**: Tesseract検証
  - バージョン取得: `get_tesseract_version()`
  - 言語データ確認: `get_languages()`

### 学び／気づき

1. **テストインフラの重要性**: 実機テストを効率的に行うには、事前準備が重要。環境検証スクリプトにより、テスト実施前に問題を発見できる。

2. **パフォーマンス測定の自動化**: 手動でストップウォッチを使うのではなく、PerformanceMonitor により正確で詳細な測定が可能。複数回のテストで平均・最小・最大を自動計算できる。

3. **ドキュメントの詳細度**: 手動テストガイドは、実施者がドキュメントだけを見て迷わず実行できるレベルの詳細さが必要。コマンド例、期待結果、確認項目を明示。

4. **エラーハンドリングのテスト**: Phase 7 で実装したエラーハンドリングが、実際にどのように動作するかを確認するための具体的なシナリオを用意。

5. **テスト結果の構造化**: テンプレートを用意することで、テスト結果の記録漏れを防ぎ、後から分析しやすくなる。

6. **段階的な検証**: 基本動作 → エラーケース → パラメータ調整 → パフォーマンス → 精度 → 長時間稼働、という段階的な検証により、問題を早期発見できる。

7. **オプショナル機能の設計**: PerformanceMonitor は必須機能ではなく、必要時のみ使用するオプショナル機能として設計。これにより、通常使用時のシンプルさを保ちつつ、詳細分析も可能。

## 次に実施する予定のタスク

**Phase 8: 実機テスト実施（ユーザー作業）**

ユーザーが以下の手順で実機テストを実施:

1. **環境準備**
   - Kindle for PC のインストール
   - Tesseract OCR のインストール（日本語データ含む）
   - `python scripts/validate_environment.py` で環境確認

2. **実機テスト実施**
   - `docs/MANUAL_TESTING.md` に従ってテスト1～7を実施
   - 各テストの結果を `docs/TEST_RESULTS_TEMPLATE.md` に記録

3. **問題の修正・パラメータ調整**
   - 発見された問題の修正
   - OCR精度向上のためのパラメータ調整
   - パフォーマンス最適化

4. **Phase 8 の完了記録**
   - テスト結果を dev_diary に記録
   - implementation_plan.md を更新

**Phase 9: ドキュメント整備**

実機テスト完了後に以下のドキュメントを整備:
- README.md（プロジェクト概要、クイックスタート）
- INSTALLATION.md（インストール手順）
- USAGE.md（詳細な使用方法）
- CONFIGURATION.md（設定ファイルの詳細）
- TROUBLESHOOTING.md（トラブルシューティング）
- API_REFERENCE.md（開発者向けAPIドキュメント）

## その他メモ

- Phase 8 のインフラ整備により、実機テストの準備が完了
- 次のステップはユーザーによる手動テスト実施
- Phase 8 完了後、プロジェクトの実用性が評価される
- 全体進捗: 約73%完了（Phase 8 インフラ完了、Phase 8 実機テスト待ち）

### 実機テスト実施のためのコマンド例

```bash
# 1. 仮想環境の有効化
./venv/Scripts/activate

# 2. 環境検証
python scripts/validate_environment.py

# 3. Kindle for PC を起動し、テスト用書籍を開く

# 4. 基本動作テスト（10ページ）
python main.py --title "テスト書籍" --total-pages 10 --debug

# 5. パフォーマンス測定（100ページ）
python main.py --title "パフォーマンステスト" --total-pages 100

# 6. 中断・再開テスト
python main.py --title "再開テスト" --total-pages 20
# Ctrl+C で中断
python main.py --title "再開テスト" --resume

# 7. 長時間稼働テスト（200ページ）
python main.py --title "長時間テスト" --total-pages 200
```

### ファイル構成

```
project/
├── scripts/
│   ├── validate_environment.py    # 環境検証スクリプト
│   └── performance_monitor.py     # パフォーマンス監視スクリプト
├── docs/
│   ├── MANUAL_TESTING.md          # 手動テストガイド
│   ├── TEST_RESULTS_TEMPLATE.md   # テスト結果記録テンプレート
│   └── dev_diary/
│       └── 2025-11-05_phase8_testing_infrastructure.md  # 本ドキュメント
└── output/
    └── performance/               # パフォーマンスメトリクス出力先
```

Phase 8 のテストインフラ整備が完了しました。ユーザーによる実機テストの実施をお待ちしています。
