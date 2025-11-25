# 手動テストガイド - Phase 8: 実機テスト・調整

このドキュメントは、Kindle for PCを使用した実機テストの手順をまとめたものです。

## 前提条件

### 必須ソフトウェア
- [x] Python 3.11.5 がインストール済み
- [x] 仮想環境（venv）が作成済み
- [x] すべての依存パッケージがインストール済み
- [x] **Kindle for PC がインストール済み** ※ユーザーが手動でインストール
- [ ] **Tesseract OCR がインストール済み** ※ユーザーが手動でインストール
  - Windows: https://github.com/UB-Mannheim/tesseract/wiki
  - インストール後、PATHに追加
  - 日本語データ（jpn.traineddata）のインストール確認
- [ ] **(オプション) Yomitoku がインストール済み** ※高精度OCR用

### テスト用書籍の準備
- Kindle for PCで任意の書籍を開く
- テスト用に10～20ページ程度の書籍を推奨
- 日本語と英語が混在したページがあると良い

---

## テスト1: 基本動作確認

### 目的
ツールが正常に起動し、基本的なOCR処理が実行できることを確認する。

### 手順

1. **設定ファイルの作成**
```bash
cd project
cp config/config.example.yaml config/config.yaml
```

2. **設定ファイルの編集** (`config/config.yaml`)
   - Tesseractのパスを確認・設定（必要に応じて）
   ```yaml
   ocr:
     tesseract:
       tesseract_cmd: null  # null の場合は自動検出
   ```

3. **Kindle for PCを起動**
   - テスト用書籍を開く
   - 開始ページを表示しておく
   - ウィンドウを最大化または適切なサイズに調整

4. **ツールの実行**（10ページをテスト）
```bash
./venv/Scripts/activate
python main.py --title "テスト書籍" --total-pages 10 --debug
```

5. **確認ポイント**
   - [x] Kindleウィンドウが自動検出されるか
   - [x] スクリーンショットが正常に撮影されるか（`output/テスト書籍_screenshots/` に保存される）
   - [x] ページが自動的に送られるか
   - [x] OCRが実行され、テキストが抽出されるか
   - [x] 進捗バーが表示されるか
   - [x] 処理完了後、テキストファイルが生成されるか（`output/テスト書籍.txt`）

6. **出力確認**
   - `output/テスト書籍.txt` を開く
   - テキストが正しく抽出されているか確認
   - 文字化けや誤認識がないか確認

---

## テスト2: 中断・再開機能の確認

### 目的
処理を中断しても、再開できることを確認する。

### 手順

1. **処理の開始**（20ページで実行）
```bash
python main.py --title "再開テスト" --total-pages 20 --debug
```

2. **途中で中断**
   - 5～10ページ処理したところで `Ctrl+C` を押す
   - 「State has been saved. Use --resume to continue.」というメッセージが表示されることを確認

3. **状態ファイルの確認**
```bash
ls output/state/
# 再開テスト_state.json が存在することを確認
```

4. **処理の再開**
```bash
python main.py --title "再開テスト" --resume --debug
```

5. **確認ポイント**
   - [ ] 前回中断したページから処理が再開されるか
   - [ ] 既に処理済みのページがスキップされるか
   - [ ] テキストが追記モードで保存されるか
   - [ ] 進捗が正しく表示されるか

---

## テスト3: エラーハンドリングの確認

### 3.1 Kindleウィンドウが見つからない場合

**手順**:
1. Kindle for PCを**起動せずに**ツールを実行
```bash
python main.py --title "エラーテスト1" --total-pages 5
```

**期待結果**:
- [ ] 「Kindle window not found」というエラーメッセージが表示される
- [ ] ツールが適切に終了する（クラッシュしない）

### 3.2 OCRエンジンが利用できない場合

**手順**:
1. `config/config.yaml` で存在しないOCRエンジンを指定
```yaml
ocr:
  primary_engine: "invalid_engine"
```
2. ツールを実行
```bash
python main.py --title "エラーテスト2" --total-pages 5
```

**期待結果**:
- [ ] OCRエンジンの初期化エラーが表示される
- [ ] ツールが適切に終了する

### 3.3 ディスク容量不足（シミュレーション）

**注意**: 実際のディスク容量不足は危険なため、小さいディスクやテスト用パーティションで実施することを推奨。

---

## テスト4: パラメータ調整

### 4.1 ページ送り遅延の調整

**目的**: ページ送り後の待機時間が適切か確認する。

**手順**:
1. `config/config.yaml` で遅延時間を変更
```yaml
kindle:
  page_turn_delay: 0.5  # 短くしてテスト
```

2. 実行して確認
   - [ ] ページが完全に読み込まれる前にスクリーンショットが撮られないか
   - [ ] 遅延が短すぎる場合は、値を増やす（1.0～2.0秒を推奨）

### 4.2 画像前処理パラメータの調整

**目的**: OCR精度を向上させるための前処理パラメータを調整する。

**手順**:
1. まず前処理なしで実行
```yaml
preprocessing:
  noise_reduction:
    enabled: false
  contrast:
    enabled: false
  skew_correction:
    enabled: false
  margin_trim:
    enabled: false
  binarization:
    enabled: false
```

2. 結果を確認し、必要に応じて各処理を有効化
```yaml
preprocessing:
  noise_reduction:
    enabled: true
    method: "gaussian"
    kernel_size: 3
  contrast:
    enabled: true
    method: "clahe"
    clip_limit: 2.0
  # ... 他のパラメータ
```

3. 前処理の効果を比較
   - [ ] `output/テスト書籍_screenshots/` のスクリーンショットを目視確認
   - [ ] OCR結果のテキスト品質を比較

### 4.3 OCR信頼度閾値の調整

**手順**:
1. `config/config.yaml` で閾値を調整
```yaml
ocr:
  tesseract:
    confidence_threshold: 0.7  # デフォルトより高く設定
```

2. 低品質な画像でテスト
   - [ ] 閾値を超えないテキストが警告として記録されるか

---

## テスト5: パフォーマンス測定

### 目的
処理速度とリソース使用量を測定する。

### 手順

1. **100ページの処理時間を計測**
```bash
time python main.py --title "パフォーマンステスト" --total-pages 100
```

**記録項目**:
- [ ] 総処理時間: _______ 分
- [ ] 1ページあたりの平均時間: _______ 秒
- [ ] スクリーンショット撮影時間: _______ 秒/ページ
- [ ] OCR処理時間: _______ 秒/ページ

2. **メモリ使用量の確認**
   - タスクマネージャー（Windows）またはリソースモニタで確認
   - [ ] ピークメモリ使用量: _______ MB
   - [ ] メモリリークの有無

3. **CPU使用率の確認**
   - [ ] 平均CPU使用率: _______ %
   - [ ] 他のアプリケーションへの影響

---

## テスト6: OCR精度評価

### 目的
OCR精度を定量的に評価する。

### 手順

1. **サンプルページの選定**
   - 10ページ程度の異なる種類のページを選ぶ
     - 通常のテキストページ
     - 図表を含むページ
     - 小さいフォントのページ
     - 英語と日本語が混在するページ

2. **手動でテキストを確認**
   - 各ページのOCR結果を目視確認
   - 正解データ（正しいテキスト）を記録

3. **精度の計算**
   - 文字認識率 = (正しく認識された文字数) / (総文字数) × 100
   - [ ] 日本語認識率: _______ %
   - [ ] 英語認識率: _______ %
   - [ ] 全体認識率: _______ %

4. **誤認識パターンの記録**
   - よくある誤認識（例: 「力」→「カ」、「O」→「0」等）
   - 認識できない文字パターン

---

## テスト7: 長時間稼働の安定性

### 目的
長時間の処理でメモリリークやクラッシュが発生しないことを確認する。

### 手順

1. **200ページ以上の書籍で実行**
```bash
python main.py --title "長時間テスト" --total-pages 200
```

2. **確認ポイント**
   - [ ] 処理が最後まで完了するか
   - [ ] メモリ使用量が徐々に増加しないか（メモリリーク）
   - [ ] エラーが発生せずに完了するか
   - [ ] 状態ファイルが定期的に保存されているか

---

## トラブルシューティング

### よくある問題と解決策

#### 1. 「Kindle window not found」エラー

**原因**: Kindleウィンドウが検出できない

**解決策**:
- Kindle for PCが起動しているか確認
- `config/config.yaml` の `window_title` を調整
```yaml
kindle:
  window_title: "Kindle"  # または "Amazon Kindle" 等
```

#### 2. OCR結果が空または精度が低い

**原因**: 画像品質が低い、またはOCRエンジンの設定が不適切

**解決策**:
- スクリーンショットを確認し、画質を確認
- 前処理パラメータを調整
- Kindleウィンドウのサイズを大きくする
- より高精度なOCRエンジン（Yomitoku）を試す

#### 3. ページ送りが速すぎる/遅すぎる

**原因**: `page_turn_delay` の設定が不適切

**解決策**:
- 遅延時間を調整（1.0～2.0秒を推奨）
```yaml
kindle:
  page_turn_delay: 1.5
```

#### 4. メモリ不足エラー

**原因**: 大量の画像を処理してメモリが不足

**解決策**:
- 画像サイズを制限
```yaml
performance:
  max_image_size: [2000, 2000]  # 幅・高さの最大値
```
- 処理を複数回に分けて実行

#### 5. Tesseract not found エラー

**原因**: Tesseractがインストールされていない、またはPATHが通っていない

**解決策**:
- Tesseractをインストール
- `config/config.yaml` でパスを明示的に指定
```yaml
ocr:
  tesseract:
    tesseract_cmd: "C:/Program Files/Tesseract-OCR/tesseract.exe"
```

---

## テスト結果の記録

以下のテンプレートを使用して、テスト結果を記録してください。

```markdown
## テスト実行記録

**日付**: YYYY-MM-DD
**環境**:
- OS: Windows 11
- Python: 3.11.5
- Tesseract: バージョン
- Kindle for PC: バージョン

### テスト1: 基本動作確認
- 結果: ✓ 成功 / ✗ 失敗
- 備考:

### テスト2: 中断・再開機能
- 結果: ✓ 成功 / ✗ 失敗
- 備考:

### テスト3: エラーハンドリング
- 結果: ✓ 成功 / ✗ 失敗
- 備考:

### テスト4: パラメータ調整
- 最適なpage_turn_delay: _____ 秒
- 前処理の有効/無効:
- 備考:

### テスト5: パフォーマンス
- 1ページあたりの平均時間: _____ 秒
- メモリ使用量: _____ MB
- 備考:

### テスト6: OCR精度
- 日本語認識率: _____ %
- 英語認識率: _____ %
- 備考:

### テスト7: 長時間稼働
- 結果: ✓ 成功 / ✗ 失敗
- 処理ページ数: _____
- 備考:

### 総合評価
- 実用性: ✓ 実用可能 / △ 要改善 / ✗ 実用困難
- 改善が必要な点:
- その他の気づき:
```

---

## 次のステップ

すべてのテストが完了したら:
1. テスト結果を `docs/dev_diary/` に記録
2. 発見された問題を Issue として記録
3. Phase 9（ドキュメント整備）に進む

---

## 参考情報

- [Tesseract OCR Documentation](https://github.com/tesseract-ocr/tesseract)
- [Kindle for PC ダウンロード](https://www.amazon.co.jp/kindle-dbs/fd/kcp)
- [実装計画書](../implementation_plan.md)
