"""Behavioral tests for the startup migration notice."""

from __future__ import annotations

import os
import unittest
from typing import ClassVar, cast
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow
from qfluentwidgets import MessageBox

from gui.app import MORU_DOWNLOAD_URL, MainWindow
from gui.i18n import get_translator


class MigrationNoticeTests(unittest.TestCase):
    """The startup notice directs users to moru without blocking legacy use."""

    app: ClassVar[QApplication]

    @classmethod
    def setUpClass(cls) -> None:
        instance = QApplication.instance()
        cls.app = instance if isinstance(instance, QApplication) else QApplication([])

    def setUp(self) -> None:
        self.window = cast(MainWindow, QMainWindow())
        self.window.translator = get_translator()

    def tearDown(self) -> None:
        self.window.translator.load_language("ko")
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_download_action_opens_latest_moru_release(self) -> None:
        self.window.translator.load_language("ko")
        rendered: dict[str, str] = {}

        def accept(dialog: MessageBox) -> int:
            rendered.update(
                title=dialog.titleLabel.text(),
                message=dialog.contentLabel.text(),
                download=dialog.yesButton.text(),
                continue_button=dialog.cancelButton.text(),
            )
            return 1

        with (
            patch.object(MessageBox, "exec", accept),
            patch("gui.app.QDesktopServices.openUrl", return_value=True) as open_url,
            patch("gui.app.QTimer.singleShot") as single_shot,
        ):
            MainWindow._show_moru_migration_notice(self.window)

        self.assertEqual(
            rendered,
            {
                "title": "새로운 앱 moru를 사용해 주세요",
                "message": (
                    "모드팩 번역기는 moru로 이전되었습니다.\n"
                    "더 나은 번역 품질과 최신 기능을 위해 moru를 사용해 주세요."
                ),
                "download": "moru 다운로드",
                "continue_button": "기존 앱 계속 사용",
            },
        )
        open_url.assert_called_once()
        self.assertEqual(open_url.call_args.args[0].toString(), MORU_DOWNLOAD_URL)
        self.assertEqual(single_shot.call_args.args[0], 1000)

    def test_continue_action_keeps_browser_closed(self) -> None:
        self.window.translator.load_language("en")
        rendered: dict[str, str] = {}

        def cancel(dialog: MessageBox) -> int:
            rendered.update(
                title=dialog.titleLabel.text(),
                message=dialog.contentLabel.text(),
                download=dialog.yesButton.text(),
                continue_button=dialog.cancelButton.text(),
            )
            return 0

        with (
            patch.object(MessageBox, "exec", cancel),
            patch("gui.app.QDesktopServices.openUrl") as open_url,
            patch("gui.app.QTimer.singleShot") as single_shot,
        ):
            MainWindow._show_moru_migration_notice(self.window)

        self.assertEqual(
            rendered,
            {
                "title": "Please switch to moru",
                "message": (
                    "Modpack Translator has moved to moru.\n"
                    "Use moru for the latest features and improved translation quality."
                ),
                "download": "Download moru",
                "continue_button": "Continue here",
            },
        )
        open_url.assert_not_called()
        self.assertEqual(single_shot.call_args.args[0], 1000)

    def test_window_startup_displays_notice_once(self) -> None:
        shown: list[tuple[str, str]] = []

        class StartupHarness(MainWindow):
            def __init__(self) -> None:
                QMainWindow.__init__(self)
                self.translator = get_translator()
                self.translator.load_language("ko")
                self._init_window()

        def close_notice(dialog: MessageBox) -> int:
            shown.append((dialog.titleLabel.text(), dialog.yesButton.text()))
            QTimer.singleShot(0, self.app.quit)
            return 0

        with (
            patch.object(MainWindow, "_create_menu_bar"),
            patch.object(MainWindow, "check_updates"),
            patch.object(MessageBox, "exec", close_notice),
        ):
            startup_window = StartupHarness()
            startup_window.show()
            QTimer.singleShot(1000, self.app.quit)
            self.app.exec()

        startup_window.close()
        startup_window.deleteLater()
        self.assertEqual(
            shown,
            [("새로운 앱 moru를 사용해 주세요", "moru 다운로드")],
        )



if __name__ == "__main__":
    unittest.main()
