"""Welcome screen with translation/download choice."""

from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    HyperlinkButton,
    PrimaryPushButton,
    SubtitleLabel,
)
from qfluentwidgets import FluentIcon as FIF

if TYPE_CHECKING:
    from ..app import MainWindow


class WelcomeCard(CardWidget):
    """Animated card widget for welcome screen options."""

    def __init__(
        self,
        icon: FIF,
        title: str,
        description: str,
        button_text: str,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize welcome card.

        Args:
            icon: Fluent icon
            title: Card title
            description: Card description
            button_text: Button text
            parent: Parent widget
        """
        super().__init__(parent)
        self._init_ui(icon, title, description, button_text)
        self._setup_animations()

    def _init_ui(
        self,
        icon: FIF,
        title: str,
        description: str,
        button_text: str,
    ) -> None:
        """Initialize UI components."""
        self.setFixedSize(400, 300)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 40, 30, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setPixmap(icon.icon(color=Qt.GlobalColor.white).pixmap(64, 64))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        self.title_label = SubtitleLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Description
        self.desc_label = BodyLabel(description)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)

        # Button
        self.button = PrimaryPushButton(button_text)
        self.button.setFixedWidth(200)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.desc_label)
        layout.addStretch()
        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignCenter)

    def _setup_animations(self) -> None:
        """Setup hover animations."""
        self._default_size = self.size()
        self._hover_animation = QPropertyAnimation(self, b"geometry")
        self._hover_animation.setDuration(200)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event: object) -> None:
        """Handle mouse enter - scale up."""
        super().enterEvent(event)
        # Subtle scale effect
        current_geo = self.geometry()
        target_geo = current_geo.adjusted(-5, -5, 5, 5)
        self._hover_animation.setStartValue(current_geo)
        self._hover_animation.setEndValue(target_geo)
        self._hover_animation.start()

    def leaveEvent(self, event: object) -> None:
        """Handle mouse leave - scale down."""
        super().leaveEvent(event)
        current_geo = self.geometry()
        target_geo = current_geo.adjusted(5, 5, -5, -5)
        self._hover_animation.setStartValue(current_geo)
        self._hover_animation.setEndValue(target_geo)
        self._hover_animation.start()


class WelcomeView(QWidget):
    """Welcome screen with translation/download choice."""

    def __init__(self, main_window: MainWindow) -> None:
        """Initialize welcome view.

        Args:
            main_window: Main application window
        """
        super().__init__()
        self.main_window = main_window
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        from ..i18n import get_translator

        t = get_translator()

        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)

        # Title
        title = SubtitleLabel(t.t("welcome.title"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Description
        desc = BodyLabel(t.t("welcome.description"))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addStretch()

        # Cards container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(40)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Translate card
        self.translate_card = WelcomeCard(
            FIF.LANGUAGE,
            t.t("welcome.translate.title"),
            t.t("welcome.translate.description"),
            t.t("welcome.translate.button"),
        )

        # Download card
        self.download_card = WelcomeCard(
            FIF.DOWNLOAD,
            t.t("welcome.download.title"),
            t.t("welcome.download.description"),
            t.t("welcome.download.button"),
        )

        cards_layout.addWidget(self.translate_card)
        cards_layout.addWidget(self.download_card)

        layout.addLayout(cards_layout)
        layout.addStretch()

        # Discord link
        self.discord_link = HyperlinkButton(
            "https://discord.gg/UBkvjNgvYX",
            t.t("welcome.discord"),
            self,
        )
        layout.addWidget(self.discord_link, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        self.translate_card.button.clicked.connect(self._on_translate_clicked)
        self.download_card.button.clicked.connect(self._on_download_clicked)

    def _on_translate_clicked(self) -> None:
        """Handle translate button click."""
        # Navigate to modpack selection view
        # This will be implemented when ModpackSelectionView is ready
        pass

    def _on_download_clicked(self) -> None:
        """Handle download button click."""
        webbrowser.open("https://mcat.2odk.com/modpacks")
