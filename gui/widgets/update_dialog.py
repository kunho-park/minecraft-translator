"""Update notification dialog."""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QTextBrowser
from qfluentwidgets import MessageBoxBase, SubtitleLabel, BodyLabel

from ..i18n import get_translator


class UpdateDialog(MessageBoxBase):
    """Dialog showing update information with Markdown support."""

    def __init__(self, version: str, release_notes: str, download_url: str, parent=None):
        super().__init__(parent)
        self.translator = get_translator()
        self.download_url = download_url
        
        # Title
        self.titleLabel = SubtitleLabel(self.translator.t("update.title"), self)
        
        # Version info
        self.versionLabel = BodyLabel(
            self.translator.t("update.available", version=version), 
            self
        )
        # Use semi-transparent color for better adaptability in light/dark modes
        self.versionLabel.setStyleSheet("color: palette(text); font-size: 14px; margin-bottom: 5px; opacity: 0.8;")

        # Release notes viewer (Markdown)
        self.textBrowser = QTextBrowser(self)
        self.textBrowser.setOpenExternalLinks(True)
        self.textBrowser.setMarkdown(release_notes)
        
        # Style for QTextBrowser to look good in both themes
        # Using rgba for background allows it to adapt slightly to the underlying theme color
        self.textBrowser.setStyleSheet("""
            QTextBrowser {
                background-color: rgba(127, 127, 127, 0.05);
                border: 1px solid rgba(127, 127, 127, 0.2);
                border-radius: 6px;
                padding: 10px;
                font-family: 'Segoe UI', 'Microsoft Sans Serif', sans-serif;
                font-size: 13px;
            }
        """)
        self.textBrowser.setMinimumHeight(300)
        
        # Layout setup
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.versionLabel)
        self.viewLayout.addWidget(self.textBrowser)

        # Buttons
        self.yesButton.setText(self.translator.t("update.download"))
        self.cancelButton.setText(self.translator.t("update.later"))
        
        # Resize logic - make it wider and taller
        self.widget.setMinimumWidth(600)
        
        # Connect signals
        self.yesButton.clicked.connect(self._on_download)
        self.cancelButton.clicked.connect(self.reject)

    def _on_download(self) -> None:
        """Handle download button click."""
        QDesktopServices.openUrl(QUrl(self.download_url))
        self.accept()
