"""Progress card widget for displaying translation progress."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import CardWidget, SubtitleLabel, BodyLabel, ProgressBar


class ProgressCard(CardWidget):
    """Card widget for displaying progress with label and bar."""
    
    def __init__(self, title: str, parent: object = None) -> None:
        """Initialize progress card.
        
        Args:
            title: Card title
            parent: Parent widget
        """
        super().__init__(parent)
        self.title = title
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = SubtitleLabel(self.title)
        layout.addWidget(title_label)
        
        # Progress bar
        self.progress_bar = ProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = BodyLabel("준비 중...")
        layout.addWidget(self.status_label)
    
    def update_progress(self, current: int, total: int, message: str = "") -> None:
        """Update progress.
        
        Args:
            current: Current progress
            total: Total items
            message: Status message
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
        
        if message:
            self.status_label.setText(f"{message} ({current}/{total})")
        else:
            self.status_label.setText(f"{current}/{total}")
    
    def set_indeterminate(self, enabled: bool = True) -> None:
        """Set indeterminate progress mode.
        
        Args:
            enabled: Whether to enable indeterminate mode
        """
        if enabled:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
