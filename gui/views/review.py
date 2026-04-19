"""Review view for LLM-based translation review."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import (
    SubtitleLabel,
    BodyLabel,
    PrimaryPushButton,
    PushButton,
    ProgressBar,
)

if TYPE_CHECKING:
    from ..app import MainWindow

logger = logging.getLogger(__name__)


class ReviewView(QWidget):
    """View for reviewing translations with LLM."""
    
    startReviewRequested = Signal()  # Emitted when user wants to review
    skipReviewRequested = Signal()  # Emitted when user wants to skip
    
    def __init__(self, main_window: MainWindow) -> None:
        """Initialize review view.
        
        Args:
            main_window: Main application window
        """
        super().__init__()
        self.main_window = main_window
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI components."""
        from ..i18n import get_translator
        t = get_translator()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = SubtitleLabel(t.t("review.title"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Description
        desc = BodyLabel(t.t("review.description"))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(30)

        # Progress bar (hidden initially)
        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = BodyLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        layout.addSpacing(30)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.skip_button = PushButton(t.t("review.skip_review"))
        self.start_button = PrimaryPushButton(t.t("review.start_review"))
        
        button_layout.addWidget(self.skip_button)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.start_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.skip_button.clicked.connect(self.skipReviewRequested.emit)
        self.start_button.clicked.connect(self._on_start_clicked)
    
    def _on_start_clicked(self) -> None:
        """Handle start button click."""
        from ..i18n import get_translator
        t = get_translator()
        
        self.start_button.setEnabled(False)
        self.skip_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText(t.t("review.reviewing"))

        self.startReviewRequested.emit()

    def update_progress(self, current: int, total: int) -> None:
        """Update review progress.

        Args:
            current: Current progress
            total: Total items
        """
        from ..i18n import get_translator
        t = get_translator()
        
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
        self.status_label.setText(f"{t.t('review.reviewing')} ({current}/{total})")
