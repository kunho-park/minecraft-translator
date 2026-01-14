"""Performance-optimized tree widget for modpack files."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator

from src.handlers.base import create_default_registry

if TYPE_CHECKING:
    from src.models import LanguageFilePair

logger = logging.getLogger(__name__)

# Pagination constants
ITEMS_PER_PAGE = 1000  # Number of items per page


class ModpackTreeItem(QTreeWidgetItem):
    """Tree item representing a mod or file."""

    def __init__(self, parent: QTreeWidget | QTreeWidgetItem | None = None) -> None:
        """Initialize tree item."""
        super().__init__(parent)
        self.file_pair: LanguageFilePair | None = None
        self.is_mod_group = False
        self.mod_id: str | None = None
        # Don't set default check state here - will be set when loading

    def set_as_mod_group(self, mod_id: str, file_count: int) -> None:
        """Configure this item as a mod group.

        Args:
            mod_id: Mod identifier
            file_count: Number of files in this mod
        """
        self.is_mod_group = True
        self.mod_id = mod_id
        self.setText(0, f"{mod_id} ({file_count}개 파일)")
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsAutoTristate)

    def set_as_file(self, file_pair: LanguageFilePair) -> None:
        """Configure this item as a file.

        Args:
            file_pair: Language file pair
        """
        self.is_mod_group = False
        self.file_pair = file_pair
        self.setText(0, file_pair.source_path.name)
        self.setToolTip(0, str(file_pair.source_path))


class ModpackTreeWidget(QTreeWidget):
    """Performance-optimized tree widget for modpack files.

    Features:
    - Lazy loading of tree items
    - Checkboxes for file selection
    - Mod grouping with file counts
    - Filtering by handler type
    - Pagination for large file lists
    """

    selectionChanged = Signal()  # Emitted when selection changes
    pageChanged = Signal(int, int)  # Emitted when page changes (current, total)

    def __init__(self, parent: object = None) -> None:
        """Initialize tree widget."""
        super().__init__(parent)
        self._all_file_pairs: list[LanguageFilePair] = []  # All files (unfiltered)
        self._file_pairs: list[LanguageFilePair] = []  # Filtered files
        self._all_mod_groups: dict[str, list[LanguageFilePair]] = {}
        self._current_page = 0
        self._total_pages = 0
        self._items_per_page = ITEMS_PER_PAGE
        self._selected_file_paths: set[str] = set()  # Track selected files across pages
        self._current_filter: str | None = None  # Current handler filter
        self._handler_registry = create_default_registry()
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        from ..i18n import get_translator

        t = get_translator()

        self.setHeaderLabels(
            [t.t("modpack_tree.headers.file"), t.t("modpack_tree.headers.handler")]
        )
        self.setColumnWidth(0, 400)
        self.setAlternatingRowColors(True)
        self.setAnimated(True)

        # Connect signals
        self.itemChanged.connect(self._on_item_changed)

    def load_files(self, file_pairs: list[LanguageFilePair]) -> None:
        """Load file pairs into tree with pagination.

        Args:
            file_pairs: List of language file pairs
        """
        self._all_file_pairs = file_pairs
        self._file_pairs = file_pairs
        self._current_filter = None
        self._all_mod_groups = self._group_by_mod(file_pairs)

        # Initialize all files as selected by default
        self._selected_file_paths = {str(fp.source_path) for fp in file_pairs}

        # Calculate total pages
        self._update_pagination()
        self._current_page = 0

        # Load first page
        self._load_page(0)

        logger.info(
            "Loaded %d files into tree (%d mods, %d pages)",
            len(file_pairs),
            len(self._all_mod_groups),
            self._total_pages,
        )

    def _update_pagination(self) -> None:
        """Update pagination based on current file list."""
        total_files = len(self._file_pairs)
        self._total_pages = max(
            1, (total_files + self._items_per_page - 1) // self._items_per_page
        )

    def _load_page(self, page: int) -> None:
        """Load a specific page of files.

        Args:
            page: Page number (0-indexed)
        """
        if page < 0 or page >= self._total_pages:
            return

        self._current_page = page

        # Disconnect signal temporarily for performance
        self.itemChanged.disconnect(self._on_item_changed)

        self.clear()

        # Calculate file range for this page
        start_idx = page * self._items_per_page
        end_idx = min(start_idx + self._items_per_page, len(self._file_pairs))
        page_files = self._file_pairs[start_idx:end_idx]

        # Group page files by mod
        page_mod_groups = self._group_by_mod(page_files)

        # Build tree for this page
        for mod_id in sorted(page_mod_groups.keys()):
            files = page_mod_groups[mod_id]

            # Create mod group item
            mod_item = ModpackTreeItem(self)
            total_mod_files = len(self._all_mod_groups[mod_id])
            page_mod_files = len(files)

            # Show page info if mod has files on multiple pages
            if total_mod_files > page_mod_files:
                mod_item.setText(0, f"{mod_id} ({page_mod_files}/{total_mod_files})")
            else:
                mod_item.set_as_mod_group(mod_id, len(files))

            mod_item.is_mod_group = True
            mod_item.mod_id = mod_id
            mod_item.setFlags(mod_item.flags() | Qt.ItemFlag.ItemIsAutoTristate)
            # Mod group state will be auto-calculated from children (tristate)

            # Add file items
            for file_pair in sorted(files, key=lambda f: f.source_path.name):
                file_item = ModpackTreeItem(mod_item)
                file_item.set_as_file(file_pair)

                # Restore selection state from previous pages
                file_path = str(file_pair.source_path)
                if file_path in self._selected_file_paths:
                    file_item.setCheckState(0, Qt.CheckState.Checked)
                else:
                    file_item.setCheckState(0, Qt.CheckState.Unchecked)

                # Get handler name
                handler_name = self._get_handler_name(file_pair)
                file_item.setText(1, handler_name)

        self.expandAll()

        # Reconnect signal after loading
        self.itemChanged.connect(self._on_item_changed)
        self.pageChanged.emit(self._current_page + 1, self._total_pages)

        logger.debug(
            "Loaded page %d/%d (%d-%d of %d files)",
            page + 1,
            self._total_pages,
            start_idx + 1,
            end_idx,
            len(self._file_pairs),
        )

    def next_page(self) -> None:
        """Load next page."""
        if self._current_page < self._total_pages - 1:
            self._load_page(self._current_page + 1)

    def previous_page(self) -> None:
        """Load previous page."""
        if self._current_page > 0:
            self._load_page(self._current_page - 1)

    def get_current_page_info(self) -> tuple[int, int]:
        """Get current page information.

        Returns:
            Tuple of (current_page, total_pages) (1-indexed)
        """
        return (self._current_page + 1, self._total_pages)

    def _group_by_mod(
        self, file_pairs: list[LanguageFilePair]
    ) -> dict[str, list[LanguageFilePair]]:
        """Group file pairs by mod ID.

        Args:
            file_pairs: List of file pairs

        Returns:
            Dictionary mapping mod IDs to file lists
        """
        groups: dict[str, list[LanguageFilePair]] = defaultdict(list)

        for pair in file_pairs:
            mod_id = pair.mod_id or "unknown"
            groups[mod_id].append(pair)

        return dict(groups)

    def _get_handler_name(self, file_pair: LanguageFilePair) -> str:
        """Get handler name for a file.

        Args:
            file_pair: Language file pair

        Returns:
            Handler name
        """
        handler = self._handler_registry.get_handler(file_pair.source_path)
        if handler:
            return handler.name
        return "Unknown"

    def get_selected_files(self) -> list[LanguageFilePair]:
        """Get list of selected (checked) file pairs across all pages.

        Returns:
            List of selected file pairs
        """
        # When using pagination, return files from _selected_file_paths
        if self._total_pages > 1:
            selected: list[LanguageFilePair] = []
            for file_pair in self._file_pairs:
                if str(file_pair.source_path) in self._selected_file_paths:
                    selected.append(file_pair)
            return selected

        # For single page, use the standard iterator approach
        selected: list[LanguageFilePair] = []
        iterator = QTreeWidgetItemIterator(
            self, QTreeWidgetItemIterator.IteratorFlag.Checked
        )

        while iterator.value():
            item: ModpackTreeItem = iterator.value()  # type: ignore[assignment]
            if not item.is_mod_group and item.file_pair:
                selected.append(item.file_pair)
            iterator += 1

        return selected

    def get_selection_stats(self) -> tuple[int, int]:
        """Get selection statistics.

        Returns:
            Tuple of (selected_count, total_count) based on current filter
        """
        # Count selected files in current filter
        selected_in_filter = sum(
            1
            for fp in self._file_pairs
            if str(fp.source_path) in self._selected_file_paths
        )
        return selected_in_filter, len(self._file_pairs)

    def select_all_files(self) -> None:
        """Select all items across all pages (respects current filter)."""
        # Select all files in current filtered view
        self._selected_file_paths.update(
            {str(fp.source_path) for fp in self._file_pairs}
        )
        # Update current page display
        self._set_all_check_state(Qt.CheckState.Checked)
        self.selectionChanged.emit()

    def deselect_all_files(self) -> None:
        """Deselect all items across all pages (respects current filter)."""
        # Deselect all files in current filtered view
        files_to_remove = {str(fp.source_path) for fp in self._file_pairs}
        self._selected_file_paths -= files_to_remove
        # Update current page display
        self._set_all_check_state(Qt.CheckState.Unchecked)
        self.selectionChanged.emit()

    def select_by_handler(self, handler_name: str) -> None:
        """Select all files with a specific handler across all pages.

        Args:
            handler_name: Handler name to select (e.g., "JSON", "SNBT", "KubeJS")
        """
        # Add files matching handler to selection
        for fp in self._file_pairs:
            if self._get_handler_name(fp) == handler_name:
                self._selected_file_paths.add(str(fp.source_path))

        # Update current page display
        self._update_current_page_checkboxes()
        self.selectionChanged.emit()

    def deselect_by_handler(self, handler_name: str) -> None:
        """Deselect all files with a specific handler across all pages.

        Args:
            handler_name: Handler name to deselect (e.g., "JSON", "SNBT", "KubeJS")
        """
        # Remove files matching handler from selection
        files_to_remove = {
            str(fp.source_path)
            for fp in self._file_pairs
            if self._get_handler_name(fp) == handler_name
        }
        self._selected_file_paths -= files_to_remove

        # Update current page display
        self._update_current_page_checkboxes()
        self.selectionChanged.emit()

    def _update_current_page_checkboxes(self) -> None:
        """Update checkboxes for current page based on _selected_file_paths."""
        # Disconnect signal temporarily for performance
        self.itemChanged.disconnect(self._on_item_changed)

        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            if isinstance(item, ModpackTreeItem) and item.file_pair:
                file_path = str(item.file_pair.source_path)
                if file_path in self._selected_file_paths:
                    item.setCheckState(0, Qt.CheckState.Checked)
                else:
                    item.setCheckState(0, Qt.CheckState.Unchecked)
            iterator += 1

        # Reconnect signal
        self.itemChanged.connect(self._on_item_changed)

    def _set_all_check_state(self, state: Qt.CheckState) -> None:
        """Set check state for all top-level items.

        Args:
            state: Check state to set
        """
        # Disconnect signal temporarily for performance
        self.itemChanged.disconnect(self._on_item_changed)

        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item:
                item.setCheckState(0, state)

        # Reconnect signal
        self.itemChanged.connect(self._on_item_changed)

    def filter_by_handler(self, handler_name: str | None) -> None:
        """Filter items by handler type and reload pagination.

        Args:
            handler_name: Handler name to filter by, or None for all
        """
        from ..i18n import get_translator

        t = get_translator()

        # Store current filter
        self._current_filter = handler_name

        # Filter file pairs
        if handler_name is None or handler_name == t.t("common.all"):
            # Show all files
            self._file_pairs = self._all_file_pairs
        else:
            # Filter by handler
            self._file_pairs = [
                fp
                for fp in self._all_file_pairs
                if self._get_handler_name(fp) == handler_name
            ]

        logger.info(
            "Filtered to %d files (handler: %s)",
            len(self._file_pairs),
            handler_name or "all",
        )

        # Update pagination for filtered list
        self._update_pagination()

        # Reset to first page
        self._current_page = 0
        self._load_page(0)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item check state change.

        Args:
            item: Changed item
            column: Changed column
        """
        if column == 0:
            # Update selected file paths
            tree_item = item  # type: ignore[assignment]
            if isinstance(tree_item, ModpackTreeItem) and tree_item.file_pair:
                file_path = str(tree_item.file_pair.source_path)
                if tree_item.checkState(0) == Qt.CheckState.Checked:
                    self._selected_file_paths.add(file_path)
                else:
                    self._selected_file_paths.discard(file_path)

            self.selectionChanged.emit()
