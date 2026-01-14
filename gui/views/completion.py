"""Completion view showing final results."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
)
from qfluentwidgets import FluentIcon as FIF

if TYPE_CHECKING:
    from src.pipeline import PipelineResult

    from ..app import MainWindow

logger = logging.getLogger(__name__)


class CompletionView(QWidget):
    """View showing translation completion and final statistics."""

    def __init__(self, main_window: MainWindow) -> None:
        """Initialize completion view.

        Args:
            main_window: Main application window
        """
        super().__init__()
        self.main_window = main_window
        self.output_path: Path | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        from ..i18n import get_translator

        t = get_translator()

        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Title
        title = SubtitleLabel(t.t("completion.title"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Success message
        message = BodyLabel(t.t("completion.description"))
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)

        layout.addSpacing(20)

        # Stats card
        self.stats_card = CardWidget()
        stats_layout = QVBoxLayout(self.stats_card)
        stats_layout.setSpacing(12)
        stats_layout.setContentsMargins(25, 25, 25, 25)

        stats_title = BodyLabel("번역 통계")
        stats_title.setProperty("class", "subtitle")
        stats_layout.addWidget(stats_title)

        self.duration_label = BodyLabel(t.t("completion.stats.duration") + " -")
        self.total_label = BodyLabel(t.t("completion.stats.total_entries") + " -")
        self.translated_label = BodyLabel(t.t("completion.stats.translated") + " -")
        self.success_rate_label = BodyLabel(t.t("completion.stats.success_rate") + " -")
        self.token_usage_label = BodyLabel("🪙 토큰 사용량: -")

        stats_layout.addWidget(self.duration_label)
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.translated_label)
        stats_layout.addWidget(self.success_rate_label)
        stats_layout.addWidget(self.token_usage_label)

        layout.addWidget(self.stats_card)

        # Output files card
        self.output_card = CardWidget()
        output_layout = QVBoxLayout(self.output_card)
        output_layout.setSpacing(12)
        output_layout.setContentsMargins(25, 25, 25, 25)

        output_title = BodyLabel(t.t("completion.output.title"))
        output_title.setProperty("class", "subtitle")
        output_layout.addWidget(output_title)

        self.output_label = BodyLabel(t.t("completion.output.resource_pack") + " -")
        output_layout.addWidget(self.output_label)

        self.open_folder_button = PushButton(
            FIF.FOLDER, t.t("completion.output.open_folder")
        )
        self.open_folder_button.setFixedWidth(150)
        output_layout.addWidget(self.open_folder_button)

        layout.addWidget(self.output_card)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.new_translation_button = PrimaryPushButton(
            t.t("completion.new_translation")
        )
        button_layout.addWidget(self.new_translation_button)

        layout.addLayout(button_layout)

        # Connect signals
        self.open_folder_button.clicked.connect(self._open_output_folder)
        self.new_translation_button.clicked.connect(self._start_new_translation)

    def set_result(self, result: PipelineResult, output_path: Path) -> None:
        """Set translation result.

        Args:
            result: Pipeline result
            output_path: Output directory path
        """
        from ..i18n import get_translator

        t = get_translator()

        self.output_path = output_path

        # Update stats
        duration = result.duration_seconds if hasattr(result, 'duration_seconds') else 0.0
        self.duration_label.setText(
            f"소요 시간: {duration:.1f}초"
        )
        self.total_label.setText(
            f"전체 항목: {result.total_entries:,}"
        )
        self.translated_label.setText(
            f"번역 완료: {result.translated_entries:,}"
        )
        
        # Calculate success rate
        success_rate = (result.success_rate * 100) if result.total_entries > 0 else 0.0
        self.success_rate_label.setText(
            f"성공률: {success_rate:.1f}%"
        )

        # Update token usage
        total_tokens = getattr(result, 'total_tokens', 0)
        input_tokens = getattr(result, 'total_input_tokens', 0)
        output_tokens = getattr(result, 'total_output_tokens', 0)
        self.token_usage_label.setText(
            f"🪙 토큰 사용량: {total_tokens:,} (입력: {input_tokens:,}, 출력: {output_tokens:,})"
        )

        # Update output path
        self.output_label.setText(
            f"리소스팩: {output_path}"
        )

        logger.info(
            "Completion view updated: %d/%d translated (%.1f%%), %.1fs, %d tokens",
            result.translated_entries,
            result.total_entries,
            success_rate,
            duration,
            total_tokens,
        )

    def _open_output_folder(self) -> None:
        """Open output folder in file explorer."""
        if self.output_path and self.output_path.exists():
            os.startfile(str(self.output_path))

    def _request_review(self) -> None:
        """Request additional review of translations."""
        logger.info("Additional review requested")
        # TODO: Implement review functionality
        # For now, just show message
        from qfluentwidgets import InfoBar, InfoBarPosition

        InfoBar.info(
            title="리뷰 기능",
            content="리뷰는 번역 중 자동으로 실행됩니다. 설정에서 '리뷰 건너뛰기'를 비활성화하세요.",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def _go_to_upload(self) -> None:
        """Navigate to upload view."""
        self.main_window.go_to_step(6)  # Upload view

    def _start_new_translation(self) -> None:
        """Start a new translation."""
        # Navigate back to welcome screen
        self.main_window.go_to_step(0)
