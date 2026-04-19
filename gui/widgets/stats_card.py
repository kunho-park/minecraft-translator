"""Statistics card widgets."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import CardWidget, SubtitleLabel, BodyLabel, CaptionLabel


class StatItem(QLabel):
    """Single statistic item display."""
    
    def __init__(self, label: str, value: str | int, parent: object = None) -> None:
        """Initialize stat item.
        
        Args:
            label: Stat label
            value: Stat value
            parent: Parent widget
        """
        super().__init__(parent)
        self.label_text = label
        self.value_text = str(value)
        self._update_text()
    
    def _update_text(self) -> None:
        """Update display text."""
        self.setText(f"{self.label_text}: <b>{self.value_text}</b>")
    
    def set_value(self, value: str | int) -> None:
        """Update value.
        
        Args:
            value: New value
        """
        self.value_text = str(value)
        self._update_text()


class StatsCard(CardWidget):
    """Card widget for displaying statistics."""
    
    def __init__(self, title: str, parent: object = None) -> None:
        """Initialize stats card.
        
        Args:
            title: Card title
            parent: Parent widget
        """
        super().__init__(parent)
        self.title = title
        self.stats: dict[str, StatItem] = {}
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = SubtitleLabel(self.title)
        layout.addWidget(title_label)
        
        # Stats container
        self.stats_layout = QVBoxLayout()
        self.stats_layout.setSpacing(8)
        layout.addLayout(self.stats_layout)
    
    def add_stat(self, key: str, label: str, value: str | int) -> None:
        """Add a statistic item.
        
        Args:
            key: Unique key for this stat
            label: Display label
            value: Initial value
        """
        stat_item = StatItem(label, value)
        self.stats[key] = stat_item
        self.stats_layout.addWidget(stat_item)
    
    def update_stat(self, key: str, value: str | int) -> None:
        """Update a statistic value.
        
        Args:
            key: Stat key
            value: New value
        """
        if key in self.stats:
            self.stats[key].set_value(value)
    
    def clear_stats(self) -> None:
        """Clear all statistics."""
        for stat in self.stats.values():
            stat.deleteLater()
        self.stats.clear()


class ScanStatsCard(StatsCard):
    """Specialized card for scan statistics."""
    
    def __init__(self, parent: object = None) -> None:
        """Initialize scan stats card.
        
        Args:
            parent: Parent widget
        """
        super().__init__("스캔 통계", parent)
        self._init_stats()
    
    def _init_stats(self) -> None:
        """Initialize default stats."""
        from ..i18n import get_translator
        t = get_translator()
        self.add_stat("total_files", t.t("scan_result.stats.total_files", "총 파일 수"), 0)
        self.add_stat("total_source", t.t("scan_result.stats.source_files"), 0)
        self.add_stat("total_target", t.t("scan_result.stats.target_files"), 0)
        self.add_stat("paired", t.t("scan_result.stats.paired"), 0)
        self.add_stat("source_only", t.t("scan_result.stats.source_only"), 0)


class TranslationStatsCard(StatsCard):
    """Specialized card for translation statistics."""
    
    def __init__(self, parent: object = None) -> None:
        """Initialize translation stats card.
        
        Args:
            parent: Parent widget
        """
        super().__init__("번역 통계", parent)
        self._init_stats()
    
    def _init_stats(self) -> None:
        """Initialize default stats."""
        from ..i18n import get_translator
        t = get_translator()
        self.add_stat("total", t.t("translation_progress.stats.total"), 0)
        self.add_stat("completed", t.t("translation_progress.stats.completed"), 0)
        self.add_stat("failed", t.t("translation_progress.stats.failed"), 0)
        self.add_stat("success_rate", t.t("translation_progress.stats.success_rate"), "0%")
