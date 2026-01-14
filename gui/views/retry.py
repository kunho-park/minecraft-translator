"""Retry view for failed translations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QListWidget, QListWidgetItem
from qfluentwidgets import (
    SubtitleLabel,
    BodyLabel,
    PrimaryPushButton,
    PushButton,
    CardWidget,
)

if TYPE_CHECKING:
    from ..app import MainWindow
    from src.pipeline import PipelineResult

logger = logging.getLogger(__name__)


class RetryView(QWidget):
    """View for retrying failed translations."""
    
    retryRequested = Signal()  # Emitted when user wants to retry
    skipRequested = Signal()  # Emitted when user wants to skip
    
    def __init__(self, main_window: MainWindow) -> None:
        """Initialize retry view.
        
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

        # Title
        title = SubtitleLabel(t.t("retry.title"))
        layout.addWidget(title)

        # Description
        desc = BodyLabel(t.t("retry.description"))
        layout.addWidget(desc)

        # Failed files list
        card = CardWidget()
        card_layout = QVBoxLayout(card)

        list_label = BodyLabel(t.t("retry.failed_files") + ":")
        card_layout.addWidget(list_label)

        self.failed_list = QListWidget()
        self.failed_list.setMinimumHeight(300)
        card_layout.addWidget(self.failed_list)

        layout.addWidget(card)

        # Buttons
        button_layout = QHBoxLayout()
        self.skip_button = PushButton(t.t("retry.skip_button"))
        self.retry_button = PrimaryPushButton(t.t("retry.retry_button"))
        
        button_layout.addWidget(self.skip_button)
        button_layout.addStretch()
        button_layout.addWidget(self.retry_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.skip_button.clicked.connect(self.skipRequested.emit)
        self.retry_button.clicked.connect(self.retryRequested.emit)
    
    def set_failed_summary(self, result: PipelineResult) -> None:
        """Set failed files summary.
        
        Args:
            result: Pipeline result with failures
        """
        self.failed_list.clear()
        
        failed_summary = result.get_failed_summary()
        for file_path, count in failed_summary.items():
            item = QListWidgetItem(f"{file_path}: {count}개 실패")
            self.failed_list.addItem(item)
