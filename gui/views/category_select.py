"""Category selection view with performance-optimized tree."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    InfoBar,
    InfoBarPosition,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
)

from src.handlers.base import create_default_registry

from ..widgets.modpack_tree import ModpackTreeWidget
from ..widgets.stats_card import StatsCard

if TYPE_CHECKING:
    from src.models import LanguageFilePair

    from ..app import MainWindow

logger = logging.getLogger(__name__)


class CategorySelectionView(QWidget):
    """View for selecting which files to translate."""

    filesSelected = Signal(list)  # Emitted when files are selected

    def __init__(self, main_window: MainWindow) -> None:
        """Initialize category selection view.

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

        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 30, 50, 30)

        # Left side: Tree view
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)

        # Title and controls
        title = SubtitleLabel(t.t("category_select.title"))
        left_layout.addWidget(title)

        # Filter and action buttons
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        filter_label = BodyLabel(t.t("common.filter") + ":")
        control_layout.addWidget(filter_label)

        self.handler_filter = ComboBox()
        
        # Dynamically load handler names
        registry = create_default_registry()
        handler_names = [t.t("common.all")] + sorted(
            [h.name for h in registry.handlers]
        )
        
        self.handler_filter.addItems(handler_names)
        self.handler_filter.setFixedWidth(150)
        control_layout.addWidget(self.handler_filter)

        control_layout.addStretch()

        self.select_all_btn = PushButton(t.t("common.select_all"))
        self.deselect_all_btn = PushButton(t.t("common.deselect_all"))
        self.select_handler_btn = PushButton(t.t("common.select_handler"))
        self.deselect_handler_btn = PushButton(t.t("common.deselect_handler"))

        control_layout.addWidget(self.select_handler_btn)
        control_layout.addWidget(self.deselect_handler_btn)
        control_layout.addWidget(self.select_all_btn)
        control_layout.addWidget(self.deselect_all_btn)

        left_layout.addLayout(control_layout)

        # Tree widget
        self.tree_widget = ModpackTreeWidget()
        left_layout.addWidget(self.tree_widget)

        # Pagination controls
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(10)

        self.prev_page_btn = PushButton(t.t("common.back"))
        self.prev_page_btn.setFixedWidth(80)
        self.prev_page_btn.clicked.connect(self.tree_widget.previous_page)
        pagination_layout.addWidget(self.prev_page_btn)

        self.page_label = BodyLabel("1 / 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pagination_layout.addWidget(self.page_label, stretch=1)

        self.next_page_btn = PushButton(t.t("common.next"))
        self.next_page_btn.setFixedWidth(80)
        self.next_page_btn.clicked.connect(self.tree_widget.next_page)
        pagination_layout.addWidget(self.next_page_btn)

        left_layout.addLayout(pagination_layout)

        layout.addLayout(left_layout, stretch=3)

        # Right side: Summary and buttons
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)

        summary_title = SubtitleLabel(t.t("category_select.summary_title"))
        right_layout.addWidget(summary_title)

        # Selection stats card
        self.stats_card = StatsCard(t.t("category_select.summary_title"))
        self.stats_card.add_stat("selected", t.t("category_select.stats.selected"), 0)
        self.stats_card.add_stat("total", t.t("category_select.stats.total"), 0)
        self.stats_card.setFixedWidth(300)
        right_layout.addWidget(self.stats_card)

        right_layout.addStretch()

        # Navigation buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)

        self.back_button = PushButton(t.t("common.back"))
        self.next_button = PrimaryPushButton(t.t("category_select.start_translation"))

        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.next_button)

        right_layout.addLayout(button_layout)

        layout.addLayout(right_layout, stretch=1)

        # Connect signals
        self.handler_filter.currentTextChanged.connect(self._on_filter_changed)
        self.select_all_btn.clicked.connect(self._on_select_all)
        self.deselect_all_btn.clicked.connect(self._on_deselect_all)
        self.select_handler_btn.clicked.connect(self._on_select_handler)
        self.deselect_handler_btn.clicked.connect(self._on_deselect_handler)
        self.tree_widget.selectionChanged.connect(self._update_stats)
        self.tree_widget.pageChanged.connect(self._on_page_changed)
        self.back_button.clicked.connect(self._on_back_clicked)
        self.next_button.clicked.connect(self._on_next_clicked)

    def load_files(self, file_pairs: list[LanguageFilePair]) -> None:
        """Load file pairs into tree with loading dialog.

        Args:
            file_pairs: List of language file pairs
        """
        from PySide6.QtCore import QTimer

        from ..i18n import get_translator
        from ..widgets.loading_dialog import LoadingDialog

        t = get_translator()

        # Show loading dialog
        loading_dialog = LoadingDialog(
            title=t.t("loading.title"), message=t.t("loading.preparing"), parent=self
        )
        loading_dialog.show()

        # Process events to show dialog
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

        # Load files (this may take time)
        def do_load() -> None:
            self.tree_widget.load_files(file_pairs)
            self._update_stats()
            loading_dialog.close()
            logger.info("Loaded %d files for selection", len(file_pairs))

        # Defer loading to allow dialog to render
        QTimer.singleShot(100, do_load)

    def _update_stats(self) -> None:
        """Update selection statistics."""
        selected, total = self.tree_widget.get_selection_stats()
        self.stats_card.update_stat("selected", selected)
        self.stats_card.update_stat("total", total)

    def _on_page_changed(self, current_page: int, total_pages: int) -> None:
        """Handle page change event.

        Args:
            current_page: Current page number (1-indexed)
            total_pages: Total number of pages
        """
        self.page_label.setText(f"{current_page} / {total_pages}")
        self.prev_page_btn.setEnabled(current_page > 1)
        self.next_page_btn.setEnabled(current_page < total_pages)
        self._update_stats()

    def _on_filter_changed(self, handler: str) -> None:
        """Handle filter change.

        Args:
            handler: Selected handler name
        """
        from ..i18n import get_translator

        t = get_translator()

        if handler == t.t("common.all"):
            self.tree_widget.filter_by_handler(None)
        else:
            self.tree_widget.filter_by_handler(handler)

        self._update_stats()

    def _on_select_all(self) -> None:
        """Handle select all button click (all files across all pages)."""
        self.tree_widget.select_all_files()
        self._update_stats()

    def _on_deselect_all(self) -> None:
        """Handle deselect all button click (all files across all pages)."""
        self.tree_widget.deselect_all_files()
        self._update_stats()

    def _on_select_handler(self) -> None:
        """Handle select handler button click (current filter only)."""
        current_filter = self.handler_filter.currentText()
        from ..i18n import get_translator

        t = get_translator()

        if current_filter == t.t("common.all"):
            self.tree_widget.select_all_files()
        else:
            self.tree_widget.select_by_handler(current_filter)
        self._update_stats()

    def _on_deselect_handler(self) -> None:
        """Handle deselect handler button click (current filter only)."""
        current_filter = self.handler_filter.currentText()
        from ..i18n import get_translator

        t = get_translator()

        if current_filter == t.t("common.all"):
            self.tree_widget.deselect_all_files()
        else:
            self.tree_widget.deselect_by_handler(current_filter)
        self._update_stats()

    def _on_back_clicked(self) -> None:
        """Handle back button click."""
        self.main_window.previous_step()

    def _on_next_clicked(self) -> None:
        """Handle next button click."""
        from ..i18n import get_translator

        t = get_translator()

        selected_files = self.tree_widget.get_selected_files()

        if not selected_files:
            InfoBar.warning(
                t.t("category_select.no_selection"),
                t.t("category_select.no_selection_msg"),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )
            return

        # Update state
        self.main_window.update_state("selected_files", selected_files)

        # Emit signal
        self.filesSelected.emit(selected_files)

        logger.info("Selected %d files for translation", len(selected_files))
