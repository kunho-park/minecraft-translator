"""Translation progress view with real-time updates."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QTextEdit, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    InfoBar,
    InfoBarPosition,
    ProgressBar,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
)

if TYPE_CHECKING:
    from ..app import MainWindow

logger = logging.getLogger(__name__)


class TranslationProgressView(QWidget):
    """View for showing translation progress in real-time."""

    stopRequested = Signal()

    def __init__(self, main_window: MainWindow) -> None:
        """Initialize translation progress view.

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
        layout.setSpacing(25)
        layout.setContentsMargins(50, 30, 50, 30)

        # Title and status
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)

        title = SubtitleLabel(t.t("translation_progress.title"))
        header_layout.addWidget(title)

        self.status_label = BodyLabel("준비 중...")
        self.status_label.setStyleSheet("color: #888888;")
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        # Progress card
        progress_card = CardWidget()
        progress_card_layout = QVBoxLayout(progress_card)
        progress_card_layout.setSpacing(15)
        progress_card_layout.setContentsMargins(25, 25, 25, 25)

        # Progress percentage label
        self.progress_label = StrongBodyLabel("0%")
        self.progress_label.setStyleSheet("font-size: 24px;")
        progress_card_layout.addWidget(
            self.progress_label, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Progress bar
        self.progress_bar = ProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        progress_card_layout.addWidget(self.progress_bar)

        # Current/Total label
        self.count_label = BodyLabel("0 / 0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet("color: #888888;")
        progress_card_layout.addWidget(self.count_label)

        layout.addWidget(progress_card)

        # Stats grid
        stats_container = CardWidget()
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setSpacing(15)
        stats_layout.setContentsMargins(25, 25, 25, 25)

        stats_title = StrongBodyLabel("번역 통계")
        stats_layout.addWidget(stats_title)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)
        stats_grid.setColumnStretch(1, 1)
        stats_grid.setColumnStretch(3, 1)

        # Total
        self.total_label = BodyLabel("전체 항목:")
        self.total_value = StrongBodyLabel("0")
        stats_grid.addWidget(self.total_label, 0, 0)
        stats_grid.addWidget(self.total_value, 0, 1)

        # Completed
        self.completed_label = BodyLabel("완료:")
        self.completed_value = StrongBodyLabel("0")
        self.completed_value.setStyleSheet("color: #00B578;")  # Green
        stats_grid.addWidget(self.completed_label, 0, 2)
        stats_grid.addWidget(self.completed_value, 0, 3)

        # Failed
        self.failed_label = BodyLabel("실패:")
        self.failed_value = StrongBodyLabel("0")
        self.failed_value.setStyleSheet("color: #FF4D4F;")  # Red
        stats_grid.addWidget(self.failed_label, 1, 0)
        stats_grid.addWidget(self.failed_value, 1, 1)

        # Success rate
        self.rate_label = BodyLabel("성공률:")
        self.rate_value = StrongBodyLabel("0%")
        self.rate_value.setStyleSheet("color: #1890FF;")  # Blue
        stats_grid.addWidget(self.rate_label, 1, 2)
        stats_grid.addWidget(self.rate_value, 1, 3)

        # Token usage - Input tokens
        self.input_token_label = BodyLabel("🪙 입력 토큰:")
        self.input_token_value = StrongBodyLabel("0")
        self.input_token_value.setStyleSheet("color: #FFA940;")  # Orange
        stats_grid.addWidget(self.input_token_label, 2, 0)
        stats_grid.addWidget(self.input_token_value, 2, 1)

        # Token usage - Output tokens
        self.output_token_label = BodyLabel("🪙 출력 토큰:")
        self.output_token_value = StrongBodyLabel("0")
        self.output_token_value.setStyleSheet("color: #FFA940;")  # Orange
        stats_grid.addWidget(self.output_token_label, 2, 2)
        stats_grid.addWidget(self.output_token_value, 2, 3)

        # Token usage - Total tokens
        self.total_token_label = BodyLabel("🪙 총 토큰:")
        self.total_token_value = StrongBodyLabel("0")
        self.total_token_value.setStyleSheet("color: #FFA940;")  # Orange
        stats_grid.addWidget(self.total_token_label, 3, 0)
        stats_grid.addWidget(self.total_token_value, 3, 1)

        stats_layout.addLayout(stats_grid)
        layout.addWidget(stats_container)

        # Log card
        log_card = CardWidget()
        log_card_layout = QVBoxLayout(log_card)
        log_card_layout.setSpacing(10)
        log_card_layout.setContentsMargins(25, 25, 25, 25)

        log_title = StrongBodyLabel(t.t("translation_progress.log_title"))
        log_card_layout.addWidget(log_title)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #1E1E1E;
                color: #CCCCCC;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
            """
        )
        log_card_layout.addWidget(self.log_text)

        layout.addWidget(log_card)

        layout.addStretch()

        # Stop button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.stop_button = PushButton(t.t("translation_progress.stop"))
        self.stop_button.setFixedWidth(120)
        self.stop_button.clicked.connect(self.stopRequested.emit)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)

    def update_progress(
        self,
        message: str,
        current: int,
        total: int,
        stats: dict[str, object] | None = None,
    ) -> None:
        """Update progress display.

        Args:
            message: Progress message
            current: Current progress
            total: Total items
            stats: Additional statistics
        """
        # Update progress bar and percentage
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_label.setText(f"{percentage}%")
            self.count_label.setText(f"{current:,} / {total:,}")

        # Update status
        self.status_label.setText(message)

        # Update stats
        if stats:
            if "total" in stats:
                self.total_value.setText(f"{stats['total']:,}")
            if "completed" in stats:
                self.completed_value.setText(f"{stats['completed']:,}")
            if "failed" in stats:
                failed = stats["failed"]
                self.failed_value.setText(f"{failed:,}")
                # Change color based on failure count
                if failed > 0:
                    self.failed_value.setStyleSheet(
                        "color: #FF4D4F; font-weight: bold;"
                    )
                else:
                    self.failed_value.setStyleSheet("color: #888888;")
            if "success_rate" in stats:
                rate_str = str(stats["success_rate"])
                self.rate_value.setText(rate_str)
                # Parse percentage for color
                try:
                    rate = float(rate_str.rstrip("%"))
                    if rate >= 95:
                        self.rate_value.setStyleSheet(
                            "color: #00B578; font-weight: bold;"
                        )
                    elif rate >= 80:
                        self.rate_value.setStyleSheet(
                            "color: #1890FF; font-weight: bold;"
                        )
                    else:
                        self.rate_value.setStyleSheet(
                            "color: #FF9800; font-weight: bold;"
                        )
                except ValueError:
                    pass

            # Update token usage
            if "input_tokens" in stats:
                self.input_token_value.setText(f"{stats['input_tokens']:,}")
            if "output_tokens" in stats:
                self.output_token_value.setText(f"{stats['output_tokens']:,}")
            if "total_tokens" in stats:
                self.total_token_value.setText(f"{stats['total_tokens']:,}")

        # Add to log with timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

        # Auto-scroll
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def complete(self) -> None:
        """Mark translation as complete."""
        from ..i18n import get_translator

        t = get_translator()

        self.progress_bar.setValue(100)
        self.status_label.setText(t.t("completion.description"))
        self.stop_button.setText(t.t("common.next"))

        InfoBar.success(
            t.t("completion.title"),
            t.t("completion.description"),
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000,
        )
