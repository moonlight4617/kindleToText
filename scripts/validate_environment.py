"""
環境検証スクリプト

実機テストの前に、実行環境が正しくセットアップされているかを確認します。
"""

import sys
import io
from pathlib import Path

# Windows コンソールの文字エンコーディング問題を修正
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from src.config.config_loader import ConfigLoader


def check_python_version():
    """Pythonバージョンの確認"""
    logger.info("Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        logger.success(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        logger.error(
            f"✗ Python 3.11+ required, found {version.major}.{version.minor}.{version.micro}"
        )
        return False


def check_dependencies():
    """必須パッケージの確認"""
    logger.info("Checking required packages...")
    # パッケージ名とインポート名のマッピング
    required_packages = {
        "click": "click",
        "loguru": "loguru",
        "Pillow": "PIL",
        "numpy": "numpy",
        "opencv-python": "cv2",
        "pytesseract": "pytesseract",
        "pyyaml": "yaml",
        "pywin32": "win32api",
    }

    all_ok = True
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            logger.success(f"✓ {package_name}")
        except ImportError:
            logger.error(f"✗ {package_name} not installed")
            all_ok = False

    return all_ok


def check_tesseract():
    """Tesseractのインストール確認"""
    logger.info("Checking Tesseract OCR...")
    try:
        import pytesseract

        try:
            version = pytesseract.get_tesseract_version()
            logger.success(f"✓ Tesseract {version}")

            # 日本語データの確認
            try:
                langs = pytesseract.get_languages()
                if "jpn" in langs:
                    logger.success("✓ Japanese language data (jpn)")
                else:
                    logger.warning("△ Japanese language data (jpn) not found")
                    logger.warning(
                        "  Download from: https://github.com/tesseract-ocr/tessdata"
                    )

                if "eng" in langs:
                    logger.success("✓ English language data (eng)")
                else:
                    logger.warning("△ English language data (eng) not found")

            except Exception as e:
                logger.warning(f"△ Could not check language data: {e}")

            return True

        except Exception as e:
            logger.error(f"✗ Tesseract not found or not in PATH: {e}")
            logger.info("  Download from: https://github.com/UB-Mannheim/tesseract/wiki")
            return False

    except ImportError:
        logger.error("✗ pytesseract package not installed")
        return False


def check_config_file():
    """設定ファイルの確認"""
    logger.info("Checking configuration file...")
    config_path = project_root / "config" / "config.yaml"

    if not config_path.exists():
        logger.error(f"✗ Configuration file not found: {config_path}")
        logger.info("  Copy config.example.yaml to config.yaml and edit it")
        return False

    try:
        config_loader = ConfigLoader(str(config_path))
        config = config_loader.load()
        logger.success(f"✓ Configuration file loaded: {config_path}")

        # 重要な設定項目の確認
        if "kindle" in config:
            logger.success("✓ Kindle settings found")
        else:
            logger.warning("△ Kindle settings not found")

        if "ocr" in config:
            logger.success("✓ OCR settings found")
            if "primary_engine" in config["ocr"]:
                engine = config["ocr"]["primary_engine"]
                logger.info(f"  Primary OCR engine: {engine}")
        else:
            logger.warning("△ OCR settings not found")

        return True

    except Exception as e:
        logger.error(f"✗ Failed to load configuration: {e}")
        return False


def check_output_directory():
    """出力ディレクトリの確認"""
    logger.info("Checking output directory...")
    output_dir = project_root / "output"

    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.success(f"✓ Output directory created: {output_dir}")
        except Exception as e:
            logger.error(f"✗ Failed to create output directory: {e}")
            return False
    else:
        logger.success(f"✓ Output directory exists: {output_dir}")

    # 書き込み権限の確認
    test_file = output_dir / "test_write.tmp"
    try:
        test_file.write_text("test")
        test_file.unlink()
        logger.success("✓ Output directory is writable")
        return True
    except Exception as e:
        logger.error(f"✗ Output directory is not writable: {e}")
        return False


def check_kindle_installation():
    """Kindle for PCのインストール確認（簡易）"""
    logger.info("Checking Kindle for PC...")

    # Windowsの一般的なインストールパスを確認
    possible_paths = [
        Path(r"C:\Program Files\Amazon\Kindle\Kindle.exe"),
        Path(r"C:\Program Files (x86)\Amazon\Kindle\Kindle.exe"),
        Path.home() / "AppData" / "Local" / "Amazon" / "Kindle" / "application" / "Kindle.exe",
    ]

    for path in possible_paths:
        if path.exists():
            logger.success(f"✓ Kindle for PC found: {path}")
            return True

    logger.warning("△ Kindle for PC not found in standard locations")
    logger.info("  Please ensure Kindle for PC is installed")
    logger.info("  Download from: https://www.amazon.co.jp/kindle-dbs/fd/kcp")
    return False


def main():
    """メイン検証処理"""
    logger.remove()
    logger.add(sys.stderr, format="<level>{message}</level>", level="INFO")

    print("=" * 80)
    print("Environment Validation for Kindle OCR Tool")
    print("=" * 80)
    print()

    results = {
        "Python Version": check_python_version(),
        "Required Packages": check_dependencies(),
        "Tesseract OCR": check_tesseract(),
        "Configuration File": check_config_file(),
        "Output Directory": check_output_directory(),
        "Kindle for PC": check_kindle_installation(),
    }

    print()
    print("=" * 80)
    print("Validation Summary")
    print("=" * 80)

    all_passed = True
    for check_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check_name:<25} {status}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print()
        logger.success("All checks passed! You are ready to run the tool.")
        print()
        print("Next steps:")
        print("1. Open Kindle for PC and select a book")
        print("2. Run: python main.py --title \"Book Title\" --total-pages 10 --debug")
        print()
        return 0
    else:
        print()
        logger.error("Some checks failed. Please fix the issues above.")
        print()
        print("Common issues:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Install Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki")
        print("- Copy config.example.yaml to config.yaml and edit it")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
