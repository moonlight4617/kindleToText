"""
Kindle書籍OCR自動化ワークフロー - メインスクリプト

Kindle for PCの書籍を自動でスクリーンショット撮影し、
OCR処理によってテキスト化するツール。
"""

import sys
from pathlib import Path
import ctypes

# Windows DPI Aware を設定（高DPI環境での座標ズレを防ぐ）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Windows 8.1 以前のフォールバック
    except Exception:
        pass  # DPI Aware 設定に失敗しても続行

import click
from loguru import logger

from src.capture.screenshot import ScreenshotCapture
from src.capture.window_manager import WindowManager
from src.config.config_loader import ConfigLoader
from src.ocr.ocr_interface import OCREngineFactory
from src.output.text_writer import TextWriter
from src.preprocessor.image_processor import ImageProcessor
from src.state.progress_tracker import ProgressTracker
from src.state.state_manager import StateManager


class KindleOCRWorkflow:
    """Kindle OCR ワークフロー制御クラス"""

    def __init__(self, config: dict):
        """
        初期化

        Args:
            config: 設定辞書
        """
        self.config = config
        self.state_manager = StateManager(
            state_dir=config["state"].get("state_dir", "output/state")
        )
        self.window_manager = None
        self.screenshot_capture = None
        self.image_processor = None
        self.ocr_engine = None
        self.text_writer = None
        self.progress_tracker = None
        self.state = None

    def initialize(self, book_title: str, total_pages: int, start_page: int = 1):
        """
        ワークフローを初期化

        Args:
            book_title: 書籍タイトル
            total_pages: 総ページ数
            start_page: 開始ページ

        Returns:
            初期化成功の場合 True
        """
        try:
            logger.info(f"Initializing workflow for: {book_title}")

            # 出力ディレクトリ作成
            output_dir = Path(self.config["output"]["base_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)

            # スクリーンショット保存ディレクトリ
            screenshot_dir = output_dir / f"{book_title}_screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            # 出力ファイルパス
            output_file = output_dir / f"{book_title}.txt"

            # 各モジュールを初期化
            self.window_manager = WindowManager(
                self.config["kindle"]["window_title"]
            )
            self.screenshot_capture = ScreenshotCapture(
                page_turn_key=self.config["kindle"]["page_turn_key"],
                page_load_delay=self.config["kindle"]["page_turn_delay"],
                screenshot_delay=self.config["kindle"].get("window_activation_delay", 0.5)
            )
            self.image_processor = ImageProcessor(self.config["preprocessing"])
            self.ocr_engine = OCREngineFactory.create_engine(
                self.config["ocr"]["primary_engine"], self.config["ocr"]
            )
            if self.ocr_engine is None:
                logger.error(f"Failed to create OCR engine: {self.config['ocr']['primary_engine']}")
                return False

            if not self.ocr_engine.initialize():
                logger.error("Failed to initialize OCR engine")
                return False

            self.text_writer = TextWriter(
                encoding=self.config["output"]["encoding"]
            )
            self.output_file = output_file

            # 進捗トラッカー初期化
            self.progress_tracker = ProgressTracker(
                total_pages=total_pages, start_page=start_page
            )

            # 初期状態作成
            self.state = self.state_manager.create_initial_state(
                book_title=book_title,
                total_pages=total_pages,
                output_file=str(output_file),
                screenshot_dir=str(screenshot_dir),
                start_page=start_page,
            )

            logger.info("Workflow initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize workflow: {e}")
            return False

    def resume_from_state(self, book_title: str) -> bool:
        """
        保存された状態から再開

        Args:
            book_title: 書籍タイトル

        Returns:
            再開成功の場合 True
        """
        try:
            logger.info(f"Attempting to resume: {book_title}")

            # 状態を読み込み
            self.state = self.state_manager.load_state(book_title)
            if self.state is None:
                logger.error("No saved state found")
                return False

            # 再開可能か確認
            if not self.state_manager.can_resume(book_title):
                logger.error("Cannot resume: processing already completed or invalid state")
                return False

            # 各モジュールを初期化
            self.window_manager = WindowManager(
                self.config["kindle"]["window_title"]
            )
            self.screenshot_capture = ScreenshotCapture(
                page_turn_key=self.config["kindle"]["page_turn_key"],
                page_load_delay=self.config["kindle"]["page_turn_delay"],
                screenshot_delay=self.config["kindle"].get("window_activation_delay", 0.5)
            )
            self.image_processor = ImageProcessor(self.config["preprocessing"])
            self.ocr_engine = OCREngineFactory.create_engine(
                self.config["ocr"]["primary_engine"], self.config["ocr"]
            )
            if self.ocr_engine is None:
                logger.error(f"Failed to create OCR engine: {self.config['ocr']['primary_engine']}")
                return False

            if not self.ocr_engine.initialize():
                logger.error("Failed to initialize OCR engine")
                return False

            self.text_writer = TextWriter(
                self.state.output_file,
                encoding=self.config["output"]["encoding"],
                append=True,
            )

            # 進捗トラッカーを復元
            self.progress_tracker = ProgressTracker(
                total_pages=self.state.total_pages, start_page=self.state.current_page
            )
            # 既に処理済みのページ情報を設定
            self.progress_tracker.current_page = self.state.current_page

            logger.info(
                f"Resuming from page {self.state.current_page}/{self.state.total_pages}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to resume from state: {e}")
            return False

    def process_page(self, page_number: int) -> bool:
        """
        1ページを処理

        Args:
            page_number: ページ番号

        Returns:
            処理成功の場合 True
        """
        try:
            logger.info(f"Processing page {page_number}/{self.state.total_pages}")

            # Kindleウィンドウを検出・アクティブ化
            window = self.window_manager.find_kindle_window()
            if not window:
                logger.error("Kindle window not found")
                return False

            if not self.window_manager.activate_window(window):
                logger.error("Failed to activate Kindle window")
                return False

            # スクリーンショット撮影
            region = self.window_manager.get_window_region(window)
            image = self.screenshot_capture.capture_screen(region)

            if image is None:
                logger.error(f"Failed to capture screenshot for page {page_number}")
                return False

            # スクリーンショット保存
            screenshot_path = (
                Path(self.state.screenshot_dir) / f"page_{page_number:04d}.png"
            )
            self.screenshot_capture.save_screenshot(image, str(screenshot_path))

            # 画像前処理
            processed_image = self.image_processor.optimize_for_ocr(image)

            # OCR処理
            ocr_result = self.ocr_engine.extract_text(processed_image)

            if not ocr_result.success or not ocr_result.text or ocr_result.text.strip() == "":
                logger.warning(f"No text extracted from page {page_number}")
                # 空ページとして扱う（エラーではない）
                text = f"\n[Page {page_number} - No text detected]\n\n"
            else:
                text = ocr_result.text

            # テキスト保存
            self.text_writer.append_text(self.output_file, text)
            self.text_writer.append_text(self.output_file, "\n" + "=" * 80 + "\n\n")

            # 次のページへ
            if page_number < self.state.total_pages:
                # ページ送り前にウィンドウを再アクティブ化
                if not self.window_manager.activate_window(window):
                    logger.warning("Failed to reactivate Kindle window before page turn")
                    # ページ送りは試みる（既にアクティブな可能性もあるため）
                self.screenshot_capture.turn_page("forward")
                self.screenshot_capture.wait_for_page_load(
                    self.config["kindle"]["page_turn_delay"]
                )

            logger.info(f"Page {page_number} processed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to process page {page_number}: {e}")
            return False

    def save_state(self):
        """現在の状態を保存"""
        try:
            self.state_manager.save_state(self.state)
            logger.debug("State saved successfully")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def run(self) -> bool:
        """
        メイン処理ループを実行

        Returns:
            処理成功の場合 True
        """
        try:
            consecutive_failures = 0
            max_consecutive_failures = self.config["error_handling"][
                "max_consecutive_failures"
            ]
            save_interval = self.config["state"]["save_interval"]

            # 開始ページを決定
            start_page = self.state.current_page + 1
            if start_page <= 0:
                start_page = 1

            # メインループ
            for page in range(start_page, self.state.total_pages + 1):
                # ページ処理
                success = self.process_page(page)

                if success:
                    # 成功時
                    consecutive_failures = 0
                    self.progress_tracker.update_progress(page, failed=False)
                    self.state.processed_pages.append(page)
                    self.state.current_page = page
                else:
                    # 失敗時
                    consecutive_failures += 1
                    self.progress_tracker.update_progress(page, failed=True)
                    self.state.failed_pages.append(page)

                    if consecutive_failures >= max_consecutive_failures:
                        logger.error(
                            f"Too many consecutive failures ({consecutive_failures}). Aborting."
                        )
                        self.state.status = "failed"
                        self.save_state()
                        return False

                # 状態を更新
                updates = {
                    "current_page": page,
                    "processed_pages": self.state.processed_pages.copy(),
                    "failed_pages": self.state.failed_pages.copy(),
                }
                self.state = self.state_manager.update_state(self.state, updates)

                # 定期的に状態を保存
                if page % save_interval == 0:
                    self.save_state()

                # 進捗表示
                if self.config["progress"]["show_progress_bar"]:
                    progress_bar = self.progress_tracker.get_progress_bar()
                    progress_info = self.progress_tracker.display_progress()
                    logger.info(f"\n{progress_bar}\n{progress_info}")

            # 処理完了
            self.state.status = "completed"
            self.state = self.state_manager.update_state(
                self.state, {"status": "completed"}
            )
            self.save_state()

            # サマリー表示
            logger.info("=" * 80)
            logger.info("Processing completed!")
            logger.info(f"Total pages: {self.state.total_pages}")
            logger.info(f"Processed pages: {len(self.state.processed_pages)}")
            logger.info(f"Failed pages: {len(self.state.failed_pages)}")
            if self.state.failed_pages:
                logger.warning(f"Failed page numbers: {self.state.failed_pages}")
            logger.info(f"Output file: {self.state.output_file}")
            logger.info("=" * 80)

            # 完了後、状態ファイルを削除（設定に応じて）
            if self.config["state"]["cleanup_on_completion"]:
                self.state_manager.delete_state(self.state.book_title)

            return True

        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}")
            self.state.status = "failed"
            self.save_state()
            return False


@click.command()
@click.option(
    "--title",
    "-t",
    required=True,
    help="書籍タイトル（出力ファイル名に使用されます）",
)
@click.option(
    "--total-pages",
    "-p",
    type=int,
    required=False,
    help="総ページ数（--resumeを指定しない場合は必須）",
)
@click.option(
    "--start-page",
    "-s",
    type=int,
    default=1,
    help="開始ページ番号（デフォルト: 1）",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    default="config/config.yaml",
    help="設定ファイルのパス（デフォルト: config/config.yaml）",
)
@click.option(
    "--resume",
    "-r",
    is_flag=True,
    help="前回の処理を再開する",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="デバッグモードで実行",
)
def main(title, total_pages, start_page, config, resume, debug):
    """
    Kindle書籍OCR自動化ツール

    Kindle for PCで開いた書籍を自動でスクリーンショット撮影し、
    OCR処理によってテキストファイルに変換します。

    例:
      python main.py --title "サンプル書籍" --total-pages 100

      python main.py --title "サンプル書籍" --resume
    """
    try:
        # 設定ファイル読み込み
        config_loader = ConfigLoader(config)
        cfg = config_loader.load()

        # デバッグモードの設定
        if debug:
            cfg["advanced"]["debug_mode"] = True
            cfg["logging"]["level"] = "DEBUG"

        # ログレベル設定
        logger.remove()
        logger.add(
            sys.stderr,
            level=cfg["logging"]["level"],
            format=cfg["logging"]["format"],
        )

        # ログファイル設定
        if cfg["logging"]["file"]:
            log_path = Path(
                cfg["logging"]["file_path"]
                .replace("{book_title}", title)
                .replace("{date}", Path(__file__).stem)
            )
            log_path.parent.mkdir(parents=True, exist_ok=True)
            logger.add(
                str(log_path),
                level=cfg["logging"]["level"],
                rotation=cfg["logging"]["rotation"],
                retention=cfg["logging"]["retention"],
            )

        logger.info("=" * 80)
        logger.info("Kindle OCR Automation Tool")
        logger.info("=" * 80)
        logger.info(f"Book Title: {title}")
        logger.info(f"Config File: {config}")
        logger.info(f"Resume Mode: {resume}")
        logger.info(f"Debug Mode: {debug}")
        logger.info("=" * 80)

        # ワークフロー初期化
        workflow = KindleOCRWorkflow(cfg)

        if resume:
            # 再開モード
            if not workflow.resume_from_state(title):
                logger.error("Failed to resume workflow")
                sys.exit(1)
        else:
            # 新規実行モード
            if total_pages is None:
                logger.error("--total-pages is required when not resuming")
                click.echo("Error: --total-pages is required when not resuming")
                sys.exit(1)

            if not workflow.initialize(title, total_pages, start_page):
                logger.error("Failed to initialize workflow")
                sys.exit(1)

        # メイン処理実行
        success = workflow.run()

        if success:
            logger.info("Processing completed successfully!")
            sys.exit(0)
        else:
            logger.error("Processing failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        logger.info("State has been saved. Use --resume to continue.")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
