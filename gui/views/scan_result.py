"""Scan result view with language and LLM settings."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    DoubleSpinBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    SpinBox,
    SubtitleLabel,
    SwitchButton,
)

from ..widgets.stats_card import ScanStatsCard

if TYPE_CHECKING:
    from src.scanner import ScanResult

    from ..app import MainWindow

logger = logging.getLogger(__name__)


class ScanResultView(QWidget):
    """View for displaying scan results and configuring translation settings."""

    settingsConfirmed = Signal(dict)  # Emitted when settings are confirmed

    def __init__(self, main_window: MainWindow) -> None:
        """Initialize scan result view.

        Args:
            main_window: Main application window
        """
        super().__init__()
        self.main_window = main_window
        self.scan_result: ScanResult | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        from ..i18n import get_translator

        t = get_translator()

        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 30, 50, 30)

        # Left side: Statistics
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)

        stats_title = SubtitleLabel(t.t("scan_result.title"))
        left_layout.addWidget(stats_title)

        self.stats_card = ScanStatsCard()
        self.stats_card.setFixedWidth(350)
        left_layout.addWidget(self.stats_card)

        left_layout.addStretch()

        layout.addLayout(left_layout)

        # Right side: Settings
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)

        settings_title = SubtitleLabel(t.t("scan_result.settings_title"))
        right_layout.addWidget(settings_title)

        # Settings card
        settings_card = CardWidget()
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setSpacing(20)
        settings_layout.setContentsMargins(25, 25, 25, 25)

        # Language settings
        lang_form = QFormLayout()
        lang_form.setSpacing(15)

        self.source_locale = ComboBox()
        self.source_locale.addItems(["en_us", "ja_jp", "zh_cn"])
        self.source_locale.setCurrentText("en_us")
        lang_form.addRow(t.t("scan_result.language.source"), self.source_locale)

        self.target_locale = ComboBox()
        self.target_locale.addItems(["ko_kr", "en_us", "ja_jp", "zh_cn"])
        self.target_locale.setCurrentText("ko_kr")
        lang_form.addRow(t.t("scan_result.language.target"), self.target_locale)

        settings_layout.addLayout(lang_form)

        # LLM settings
        llm_label = BodyLabel(t.t("scan_result.llm.title"))
        llm_label.setProperty("class", "section-title")
        settings_layout.addWidget(llm_label)

        llm_form = QFormLayout()
        llm_form.setSpacing(15)

        self.llm_provider = ComboBox()
        self.llm_provider.addItems(["ollama", "openai", "anthropic", "google"])
        self.llm_provider.setCurrentText("ollama")
        self.llm_provider.currentTextChanged.connect(self._on_provider_changed)
        llm_form.addRow(t.t("scan_result.llm.provider"), self.llm_provider)

        self.llm_base_url = LineEdit()
        self.llm_base_url.setText("http://localhost:11434")
        self.llm_base_url.setPlaceholderText("Base URL")
        llm_form.addRow("Base URL:", self.llm_base_url)

        self.llm_api_key = LineEdit()
        self.llm_api_key.setPlaceholderText("API Key (선택사항)")
        self.llm_api_key.setEchoMode(LineEdit.EchoMode.Password)
        llm_form.addRow("API Key:", self.llm_api_key)

        self.llm_model = LineEdit()
        self.llm_model.setText("qwen2.5:14b")
        self.llm_model.setPlaceholderText(t.t("scan_result.llm.model"))
        llm_form.addRow(t.t("scan_result.llm.model"), self.llm_model)

        self.temperature = DoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(0.1)
        llm_form.addRow(t.t("scan_result.llm.temperature"), self.temperature)

        self.batch_size = SpinBox()
        self.batch_size.setRange(1, 100)
        self.batch_size.setValue(30)
        llm_form.addRow(t.t("scan_result.llm.batch_size"), self.batch_size)

        self.max_concurrent = SpinBox()
        self.max_concurrent.setRange(1, 50)
        self.max_concurrent.setValue(15)
        llm_form.addRow(t.t("scan_result.llm.max_concurrent"), self.max_concurrent)

        self.requests_per_minute = SpinBox()
        self.requests_per_minute.setRange(0, 10000)
        self.requests_per_minute.setValue(0)
        self.requests_per_minute.setToolTip(
            "API 요청 속도 제한 (분당 요청 수)\n"
            "0 = 제한 없음\n"
            "클라우드 API 사용 시 rate limit 오류 방지용"
        )
        llm_form.addRow(t.t("scan_result.llm.rpm"), self.requests_per_minute)

        self.tokens_per_minute = SpinBox()
        self.tokens_per_minute.setRange(0, 100_000_000)
        self.tokens_per_minute.setValue(0)
        self.tokens_per_minute.setToolTip(
            "API 토큰 속도 제한 (분당 토큰 수)\n"
            "0 = 제한 없음\n"
            "예: 4000000 = 4M TPM\n"
            "클라우드 API 사용 시 rate limit 오류 방지용"
        )
        llm_form.addRow(t.t("scan_result.llm.tpm"), self.tokens_per_minute)

        settings_layout.addLayout(llm_form)

        # Pipeline options
        options_label = BodyLabel(t.t("scan_result.options.title"))
        options_label.setProperty("class", "section-title")
        settings_layout.addWidget(options_label)

        options_layout = QFormLayout()
        options_layout.setSpacing(12)

        self.skip_glossary = SwitchButton()
        self.skip_glossary.setChecked(False)
        options_layout.addRow(
            t.t("scan_result.options.skip_glossary"), self.skip_glossary
        )

        self.skip_review = SwitchButton()
        self.skip_review.setChecked(False)
        options_layout.addRow(t.t("scan_result.options.skip_review"), self.skip_review)

        self.save_glossary = SwitchButton()
        self.save_glossary.setChecked(True)
        self.save_glossary.setToolTip(
            "모드팩 전용 용어집을 저장합니다 (바닐라 용어집은 제외)\n"
            "나중에 용어집을 재사용하거나 수동으로 편집할 수 있습니다"
        )
        options_layout.addRow(
            t.t("scan_result.options.save_glossary"), self.save_glossary
        )

        settings_layout.addLayout(options_layout)

        right_layout.addWidget(settings_card)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.back_button = PushButton(t.t("common.back"))
        self.next_button = PrimaryPushButton(t.t("common.next"))

        button_layout.addWidget(self.back_button)
        button_layout.addStretch()
        button_layout.addWidget(self.next_button)

        right_layout.addLayout(button_layout)

        layout.addLayout(right_layout, stretch=1)

        # Connect signals
        self.back_button.clicked.connect(self._on_back_clicked)
        self.next_button.clicked.connect(self._on_next_clicked)

        # Set initial provider defaults
        self._on_provider_changed(self.llm_provider.currentText())

        # Load settings from config
        self._load_config()

    def set_scan_result(self, result: ScanResult) -> None:
        """Set scan result and update display.

        Args:
            result: Scan result from worker
        """
        self.scan_result = result

        # Update statistics
        self.stats_card.update_stat("total_files", len(result.translation_files))
        self.stats_card.update_stat("total_source", result.total_source_files)
        self.stats_card.update_stat("total_target", result.total_target_files)
        self.stats_card.update_stat("paired", result.total_paired)
        self.stats_card.update_stat("source_only", len(result.source_only_files))

        logger.info(
            "Scan result displayed: %d total files, %d translation pairs",
            len(result.translation_files),
            len(result.all_translation_pairs),
        )

    def _load_config(self) -> None:
        """Load settings from configuration."""
        config = self.main_window.config

        # Language settings
        self.source_locale.setCurrentText(
            config.get("translation.source_locale", "en_us")
        )
        self.target_locale.setCurrentText(
            config.get("translation.target_locale", "ko_kr")
        )

        # LLM settings
        self.llm_provider.setCurrentText(config.get("llm.provider", "ollama"))
        self.llm_base_url.setText(config.get("llm.base_url", "http://localhost:11434"))
        self.llm_api_key.setText(config.get("llm.api_key", ""))
        self.llm_model.setText(config.get("llm.model", "qwen2.5:14b"))
        self.temperature.setValue(config.get("llm.temperature", 0.1))
        self.batch_size.setValue(config.get("llm.batch_size", 30))
        self.max_concurrent.setValue(config.get("llm.max_concurrent", 15))
        self.requests_per_minute.setValue(config.get("llm.requests_per_minute", 0))
        self.tokens_per_minute.setValue(config.get("llm.tokens_per_minute", 0))

        # Pipeline options
        self.skip_glossary.setChecked(config.get("translation.skip_glossary", False))
        self.skip_review.setChecked(config.get("translation.skip_review", False))
        self.save_glossary.setChecked(config.get("translation.save_glossary", True))

    def _save_config(self) -> None:
        """Save settings to configuration."""
        config = self.main_window.config

        # Language settings
        config.set("translation.source_locale", self.source_locale.currentText())
        config.set("translation.target_locale", self.target_locale.currentText())

        # LLM settings
        config.set("llm.provider", self.llm_provider.currentText())
        config.set("llm.base_url", self.llm_base_url.text().strip())
        config.set("llm.api_key", self.llm_api_key.text().strip())
        config.set("llm.model", self.llm_model.text())
        config.set("llm.temperature", self.temperature.value())
        config.set("llm.batch_size", self.batch_size.value())
        config.set("llm.max_concurrent", self.max_concurrent.value())
        config.set("llm.requests_per_minute", self.requests_per_minute.value())
        config.set("llm.tokens_per_minute", self.tokens_per_minute.value())

        # Pipeline options
        config.set("translation.skip_glossary", self.skip_glossary.isChecked())
        config.set("translation.skip_review", self.skip_review.isChecked())
        config.set("translation.save_glossary", self.save_glossary.isChecked())

        config.save()

    def _on_provider_changed(self, provider: str) -> None:
        """Handle LLM provider change.

        Args:
            provider: Selected provider name
        """
        # Set default base URLs for each provider
        defaults = {
            "ollama": ("http://localhost:11434", "qwen2.5:14b"),
            "openai": ("https://api.openai.com/v1", "gpt-4-turbo-preview"),
            "anthropic": ("https://api.anthropic.com", "claude-3-5-sonnet-20241022"),
            "google": (
                "https://generativelanguage.googleapis.com/v1beta",
                "gemini-1.5-pro",
            ),
        }

        base_url, default_model = defaults.get(provider, ("", ""))
        self.llm_base_url.setText(base_url)

        # Update model placeholder if current model is empty
        if not self.llm_model.text():
            self.llm_model.setText(default_model)

    def get_settings(self) -> dict[str, object]:
        """Get current settings as dictionary.

        Returns:
            Settings dictionary
        """
        api_key = self.llm_api_key.text().strip()

        return {
            "source_locale": self.source_locale.currentText(),
            "target_locale": self.target_locale.currentText(),
            "llm_provider": self.llm_provider.currentText(),
            "llm_model": self.llm_model.text(),
            "llm_temperature": self.temperature.value(),
            "llm_base_url": self.llm_base_url.text().strip() or None,
            "llm_api_key": api_key if api_key else None,
            "max_concurrent": self.max_concurrent.value(),
            "batch_size": self.batch_size.value(),
            "requests_per_minute": self.requests_per_minute.value(),
            "tokens_per_minute": self.tokens_per_minute.value(),
            "skip_glossary": self.skip_glossary.isChecked(),
            "skip_review": self.skip_review.isChecked(),
            "save_glossary": self.save_glossary.isChecked(),
        }

    def _on_back_clicked(self) -> None:
        """Handle back button click."""
        self.main_window.previous_step()

    def _on_next_clicked(self) -> None:
        """Handle next button click."""
        # Save settings
        self._save_config()

        # Update main window state
        settings = self.get_settings()
        self.main_window.update_state("pipeline_config", settings)

        # Emit signal
        self.settingsConfirmed.emit(settings)

        logger.info("Settings confirmed: %s", settings)
