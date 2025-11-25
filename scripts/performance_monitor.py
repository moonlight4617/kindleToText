"""
パフォーマンス監視スクリプト

OCR処理のパフォーマンス（処理時間、メモリ使用量等）を測定します。
"""

import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List

import psutil
from loguru import logger


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""

    timestamp: str
    page_number: int
    screenshot_time: float  # スクリーンショット撮影時間（秒）
    preprocessing_time: float  # 画像前処理時間（秒）
    ocr_time: float  # OCR処理時間（秒）
    total_time: float  # 合計時間（秒）
    memory_usage_mb: float  # メモリ使用量（MB）
    cpu_percent: float  # CPU使用率（%）


class PerformanceMonitor:
    """パフォーマンス監視クラス"""

    def __init__(self, output_dir: str = "output/performance"):
        """
        初期化

        Args:
            output_dir: 測定結果の出力ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.metrics: List[PerformanceMetrics] = []
        self.process = psutil.Process()

        self.start_time = None
        self.screenshot_start = None
        self.preprocessing_start = None
        self.ocr_start = None

    def start_page(self):
        """ページ処理開始"""
        self.start_time = time.time()

    def start_screenshot(self):
        """スクリーンショット開始"""
        self.screenshot_start = time.time()

    def end_screenshot(self):
        """スクリーンショット終了"""
        return time.time() - self.screenshot_start if self.screenshot_start else 0

    def start_preprocessing(self):
        """前処理開始"""
        self.preprocessing_start = time.time()

    def end_preprocessing(self):
        """前処理終了"""
        return time.time() - self.preprocessing_start if self.preprocessing_start else 0

    def start_ocr(self):
        """OCR開始"""
        self.ocr_start = time.time()

    def end_ocr(self):
        """OCR終了"""
        return time.time() - self.ocr_start if self.ocr_start else 0

    def end_page(
        self, page_number: int, screenshot_time: float, preprocessing_time: float, ocr_time: float
    ):
        """
        ページ処理終了

        Args:
            page_number: ページ番号
            screenshot_time: スクリーンショット時間
            preprocessing_time: 前処理時間
            ocr_time: OCR時間
        """
        total_time = time.time() - self.start_time if self.start_time else 0

        # メモリ使用量取得
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024

        # CPU使用率取得
        cpu_percent = self.process.cpu_percent(interval=0.1)

        metric = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            page_number=page_number,
            screenshot_time=screenshot_time,
            preprocessing_time=preprocessing_time,
            ocr_time=ocr_time,
            total_time=total_time,
            memory_usage_mb=memory_mb,
            cpu_percent=cpu_percent,
        )

        self.metrics.append(metric)

        logger.debug(
            f"Page {page_number}: {total_time:.2f}s total "
            f"(screenshot: {screenshot_time:.2f}s, "
            f"preprocessing: {preprocessing_time:.2f}s, "
            f"ocr: {ocr_time:.2f}s), "
            f"Memory: {memory_mb:.1f}MB, "
            f"CPU: {cpu_percent:.1f}%"
        )

    def save_metrics(self, filename: str = None):
        """
        メトリクスをファイルに保存

        Args:
            filename: 出力ファイル名（Noneの場合は自動生成）
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_{timestamp}.json"

        filepath = self.output_dir / filename

        data = [asdict(m) for m in self.metrics]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Performance metrics saved to: {filepath}")

    def generate_report(self) -> dict:
        """
        パフォーマンスレポートを生成

        Returns:
            レポート辞書
        """
        if not self.metrics:
            return {}

        total_pages = len(self.metrics)

        # 各時間の統計
        screenshot_times = [m.screenshot_time for m in self.metrics]
        preprocessing_times = [m.preprocessing_time for m in self.metrics]
        ocr_times = [m.ocr_time for m in self.metrics]
        total_times = [m.total_time for m in self.metrics]

        # メモリ・CPUの統計
        memory_usages = [m.memory_usage_mb for m in self.metrics]
        cpu_percents = [m.cpu_percent for m in self.metrics]

        report = {
            "total_pages": total_pages,
            "total_time": sum(total_times),
            "average_time_per_page": sum(total_times) / total_pages,
            "screenshot": {
                "average": sum(screenshot_times) / total_pages,
                "min": min(screenshot_times),
                "max": max(screenshot_times),
            },
            "preprocessing": {
                "average": sum(preprocessing_times) / total_pages,
                "min": min(preprocessing_times),
                "max": max(preprocessing_times),
            },
            "ocr": {
                "average": sum(ocr_times) / total_pages,
                "min": min(ocr_times),
                "max": max(ocr_times),
            },
            "memory": {
                "average_mb": sum(memory_usages) / total_pages,
                "peak_mb": max(memory_usages),
                "min_mb": min(memory_usages),
            },
            "cpu": {
                "average_percent": sum(cpu_percents) / total_pages,
                "peak_percent": max(cpu_percents),
            },
        }

        return report

    def print_report(self):
        """レポートを標準出力に表示"""
        report = self.generate_report()

        if not report:
            logger.warning("No metrics to report")
            return

        print()
        print("=" * 80)
        print("Performance Report")
        print("=" * 80)
        print()
        print(f"Total Pages Processed: {report['total_pages']}")
        print(f"Total Time: {report['total_time']:.2f} seconds ({report['total_time']/60:.2f} minutes)")
        print(f"Average Time per Page: {report['average_time_per_page']:.2f} seconds")
        print()
        print("Breakdown by Stage:")
        print(f"  Screenshot:    {report['screenshot']['average']:.2f}s (avg) | "
              f"{report['screenshot']['min']:.2f}s (min) | "
              f"{report['screenshot']['max']:.2f}s (max)")
        print(f"  Preprocessing: {report['preprocessing']['average']:.2f}s (avg) | "
              f"{report['preprocessing']['min']:.2f}s (min) | "
              f"{report['preprocessing']['max']:.2f}s (max)")
        print(f"  OCR:           {report['ocr']['average']:.2f}s (avg) | "
              f"{report['ocr']['min']:.2f}s (min) | "
              f"{report['ocr']['max']:.2f}s (max)")
        print()
        print("Resource Usage:")
        print(f"  Memory: {report['memory']['average_mb']:.1f}MB (avg) | "
              f"{report['memory']['peak_mb']:.1f}MB (peak)")
        print(f"  CPU:    {report['cpu']['average_percent']:.1f}% (avg) | "
              f"{report['cpu']['peak_percent']:.1f}% (peak)")
        print()
        print("=" * 80)


def demo_usage():
    """使用例のデモ"""
    monitor = PerformanceMonitor()

    # シミュレーション: 10ページ処理
    for page in range(1, 11):
        monitor.start_page()

        # スクリーンショット
        monitor.start_screenshot()
        time.sleep(0.1)  # シミュレーション
        screenshot_time = monitor.end_screenshot()

        # 前処理
        monitor.start_preprocessing()
        time.sleep(0.2)  # シミュレーション
        preprocessing_time = monitor.end_preprocessing()

        # OCR
        monitor.start_ocr()
        time.sleep(0.5)  # シミュレーション
        ocr_time = monitor.end_ocr()

        monitor.end_page(page, screenshot_time, preprocessing_time, ocr_time)

    # レポート表示
    monitor.print_report()

    # メトリクス保存
    monitor.save_metrics("demo_metrics.json")


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    print("Performance Monitor Demo")
    print()
    demo_usage()
