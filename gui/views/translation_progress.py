"""Translation progress view with real-time updates."""

from __future__ import annotations

import logging
import time
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
        self._phase_start_time: float = 0.0
        self._phase_total: int = -1
        self._phase_start_current: int = 0
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

        # ETA label
        self.eta_label = BodyLabel("")
        self.eta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.eta_label.setStyleSheet("color: #1890FF; font-size: 13px;")
        progress_card_layout.addWidget(self.eta_label)

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

        # ETA calculation — reset timer when phase changes (total changes)
        self._update_eta(current, total)

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

    def _update_eta(self, current: int, total: int) -> None:
        """Calculate and display ETA based on current phase progress."""
        if total <= 0:
            self.eta_label.setText("")
            return

        now = time.monotonic()

        # Detect phase change when total changes
        if total != self._phase_total:
            self._phase_total = total
            self._phase_start_time = now
            self._phase_start_current = current
            self.eta_label.setText("⏱ 남은 시간 계산 중...")
            return

        done_in_phase = current - self._phase_start_current
        elapsed = now - self._phase_start_time

        if done_in_phase <= 0 or elapsed < 3.0:
            self.eta_label.setText("⏱ 남은 시간 계산 중...")
            return

        if current >= total:
            self.eta_label.setText("")
            return

        rate = done_in_phase / elapsed
        remaining_items = total - current
        eta_seconds = remaining_items / rate
        self.eta_label.setText(f"⏱ 남은 시간: {self._format_eta(eta_seconds)}")

    @staticmethod
    def _format_eta(seconds: float) -> str:
        """Format seconds into human-readable duration."""
        seconds = max(0, int(seconds))
        if seconds < 60:
            return f"{seconds}초"
        minutes = seconds // 60
        secs = seconds % 60
        if minutes < 60:
            return f"{minutes}분 {secs}초" if secs else f"{minutes}분"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}시간 {mins}분" if mins else f"{hours}시간"

    def reset_eta(self) -> None:
        """Reset ETA tracking state for a new run."""
        self._phase_start_time = 0.0
        self._phase_total = -1
        self._phase_start_current = 0
        self.eta_label.setText("")

    def complete(self) -> None:
        """Mark translation as complete."""
        from ..i18n import get_translator

        t = get_translator()

        self.progress_bar.setValue(100)
        self.status_label.setText(t.t("completion.description"))
        self.stop_button.setText(t.t("common.next"))
        self.eta_label.setText("")

        InfoBar.success(
            t.t("completion.title"),
            t.t("completion.description"),
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000,
        )
