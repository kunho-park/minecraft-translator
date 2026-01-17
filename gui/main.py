"""Application entry point."""

from __future__ import annotations

import faulthandler
import logging
import sys
import traceback
from pathlib import Path

import colorlog
from PySide6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme

from .app import MainWindow
from .config import get_config
from .i18n import get_translator


def setup_logging() -> None:
    """Configure logging with colorlog."""
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        fmt="%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    handler.setFormatter(formatter)

    logger = colorlog.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Disable AFC logging from google_genai.models
    logging.getLogger("google_genai.models").setLevel(logging.WARNING)


def load_stylesheet(app: QApplication) -> None:
    """Load custom QSS stylesheet.

    Args:
        app: QApplication instance
    """
    qss_file = Path(__file__).parent / "styles" / "app.qss"
    if qss_file.exists():
        with open(qss_file, encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    setup_logging()
    # Enable faulthandler to catch segmentation faults
    faulthandler.enable()

    logger = logging.getLogger(__name__)
    logger.info("Starting Modpack Translator GUI")

    # Set up exception hook to log unhandled exceptions
    def exception_hook(exctype, value, tb):
        logger.critical("Unhandled exception:", exc_info=(exctype, value, tb))
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = exception_hook

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Modpack Translator")
    app.setOrganizationName("MCAT")

    # Load configuration
    config = get_config()

    # Load translator
    translator = get_translator()
    language = config.get("language", "ko")
    translator.load_language(language)
    logger.info("Language set to: %s", language)

    # Set theme
    theme_name = config.get("theme", "auto")
    if theme_name == "dark":
        setTheme(Theme.DARK)
    elif theme_name == "light":
        setTheme(Theme.LIGHT)
    else:
        setTheme(Theme.AUTO)

    # Load custom stylesheet
    load_stylesheet(app)

    # Create main window
    window = MainWindow()
    window.show()

    logger.info("GUI initialized successfully")

    # Run application
    exit_code = app.exec()

    # Save configuration on exit
    config.save()
    logger.info("Application exiting with code %d", exit_code)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
