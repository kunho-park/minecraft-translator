"""Loading dialog widget."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout
from qfluentwidgets import BodyLabel, IndeterminateProgressBar, SubtitleLabel


class LoadingDialog(QDialog):
    """Simple loading dialog with progress bar."""

    def __init__(
        self, title: str = "", message: str = "", parent: object = None
    ) -> None:
        """Initialize loading dialog.

        Args:
            title: Dialog title
            message: Initial message
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Import translator
        from ..i18n import get_translator
        t = get_translator()
        
        # Use default title if not provided
        if not title:
            title = t.t("loading.title")
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        self.title_label = SubtitleLabel(title)
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Progress bar
        self.progress_bar = IndeterminateProgressBar()
        self.progress_bar.setFixedHeight(4)
        layout.addWidget(self.progress_bar)

        # Message
        self.message_label = BodyLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.message_label)

        layout.addStretch()

    def set_message(self, message: str) -> None:
        """Update message text.

        Args:
            message: New message
        """
        self.message_label.setText(message)

    def showEvent(self, event: object) -> None:
        """Handle show event."""
        super().showEvent(event)
        self.progress_bar.start()

    def closeEvent(self, event: object) -> None:
        """Handle close event."""
        self.progress_bar.stop()
        super().closeEvent(event)
