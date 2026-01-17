"""Modpack selection view with launcher scanning and thumbnails."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QByteArray, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    IndeterminateProgressBar,
    InfoBar,
    InfoBarPosition,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SubtitleLabel,
)
from qfluentwidgets import FluentIcon as FIF

if TYPE_CHECKING:
    from ..app import MainWindow

logger = logging.getLogger(__name__)


@dataclass
class ModpackInfo:
    """Modpack information with metadata."""

    name: str
    path: Path
    launcher: str = "Manual"
    thumbnail_url: str = ""
    author: str = ""
    version: str = ""
    website_url: str = ""
    curseforge_id: int | None = None

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} ({self.launcher})"


class ModpackCard(QFrame):
    """Card widget displaying modpack with thumbnail."""

    cardClicked = Signal(object)  # ModpackInfo
    cardDoubleClicked = Signal(object)  # ModpackInfo

    def __init__(
        self,
        modpack: ModpackInfo,
        network_manager: QNetworkAccessManager,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize modpack card."""
        super().__init__(parent)
        self.modpack = modpack
        self.network_manager = network_manager
        self._selected = False
        self._init_ui()
        self._load_thumbnail()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.setFixedSize(200, 240)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            """
            ModpackCard {
                background-color: #2d2d2d;
                border-radius: 8px;
                border: 1px solid #3d3d3d;
            }
            ModpackCard:hover {
                background-color: #353535;
                border: 1px solid #4d4d4d;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(180, 135)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet(
            "background-color: #252525; border-radius: 6px;"
        )
        self._set_default_thumbnail()
        layout.addWidget(self.thumbnail_label)

        # Name
        self.name_label = SubtitleLabel(self.modpack.name)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(40)
        layout.addWidget(self.name_label)

        # Info row
        info_text = self.modpack.launcher
        if self.modpack.author:
            info_text = f"{self.modpack.author} • {self.modpack.launcher}"
        if self.modpack.version:
            info_text += f" • {self.modpack.version}"

        self.info_label = CaptionLabel(info_text)
        self.info_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.info_label)

        layout.addStretch()

    def _set_default_thumbnail(self) -> None:
        """Set default thumbnail icon."""
        self.thumbnail_label.setText("🎮")
        self.thumbnail_label.setStyleSheet(
            """
            background-color: #252525;
            border-radius: 6px;
            font-size: 48px;
            color: #666666;
            """
        )

    def _load_thumbnail(self) -> None:
        """Load thumbnail from URL."""
        if not self.modpack.thumbnail_url:
            return

        if not self.modpack.thumbnail_url.startswith("http"):
            return

        try:
            logger.info("Starting thumbnail download: %s", self.modpack.thumbnail_url)
            url = QUrl(self.modpack.thumbnail_url)
            request = QNetworkRequest(url)
            reply = self.network_manager.get(request)
            logger.info("Network request initiated")
            reply.finished.connect(lambda: self._on_thumbnail_loaded(reply))
        except Exception as e:
            logger.error("Failed to start thumbnail load: %s", e, exc_info=True)

    def _on_thumbnail_loaded(self, reply: QNetworkReply) -> None:
        """Handle thumbnail download completion."""
        try:
            logger.info("Thumbnail download finished. Error: %s", reply.error())
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data: QByteArray = reply.readAll()
                logger.info("Thumbnail data size: %d bytes", data.size())
                pixmap = QPixmap()
                if pixmap.loadFromData(data):
                    logger.info(
                        "Thumbnail loaded successfully. Size: %dx%d",
                        pixmap.width(),
                        pixmap.height(),
                    )
                    scaled = pixmap.scaled(
                        180,
                        135,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    # Crop to center
                    if scaled.width() > 180 or scaled.height() > 135:
                        x = (scaled.width() - 180) // 2
                        y = (scaled.height() - 135) // 2
                        scaled = scaled.copy(x, y, 180, 135)
                    self.thumbnail_label.setPixmap(scaled)
                    self.thumbnail_label.setText("")
                    self.thumbnail_label.setStyleSheet(
                        "background-color: transparent; border-radius: 6px;"
                    )
        except Exception as e:
            logger.error("Failed to load thumbnail: %s", e, exc_info=True)
        finally:
            reply.deleteLater()

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        self._selected = selected
        if selected:
            self.setStyleSheet(
                """
                ModpackCard {
                    background-color: rgba(0, 120, 212, 0.15);
                    border-radius: 8px;
                    border: 2px solid #0078d4;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                ModpackCard {
                    background-color: #2d2d2d;
                    border-radius: 8px;
                    border: 1px solid #3d3d3d;
                }
                ModpackCard:hover {
                    background-color: #353535;
                    border: 1px solid #4d4d4d;
                }
                """
            )

    def mousePressEvent(self, event: object) -> None:
        """Handle mouse press."""
        super().mousePressEvent(event)
        self.cardClicked.emit(self.modpack)

    def mouseDoubleClickEvent(self, event: object) -> None:
        """Handle double click."""
        super().mouseDoubleClickEvent(event)
        self.cardDoubleClicked.emit(self.modpack)


class ScannerThread(QThread):
    """Background thread for scanning modpacks."""

    scanComplete = Signal(list)  # List of ModpackInfo
    scanProgress = Signal(str)  # Current status message

    def __init__(self, launcher_paths: list[tuple[str, Path]]) -> None:
        """Initialize scanner thread."""
        super().__init__()
        self.launcher_paths = launcher_paths

    def run(self) -> None:
        """Run the scanning operation."""
        modpacks: list[ModpackInfo] = []

        for launcher_name, launcher_path in self.launcher_paths:
            if not launcher_path.exists():
                continue

            self.scanProgress.emit(f"{launcher_name} 스캔 중...")
            logger.info("Scanning %s: %s", launcher_name, launcher_path)

            try:
                for item in launcher_path.iterdir():
                    if item.is_dir():
                        if self._is_valid_modpack(item):
                            modpack_info = self._get_modpack_info(item, launcher_name)
                            modpacks.append(modpack_info)
            except Exception as e:
                logger.error("Error scanning %s: %s", launcher_path, e)

        self.scanComplete.emit(modpacks)

    def _is_valid_modpack(self, path: Path) -> bool:
        """Check if directory is a valid modpack instance."""
        if (path / "mods").exists() or (path / "config").exists():
            return True

        for minecraft_name in ("minecraft", ".minecraft"):
            minecraft_dir = path / minecraft_name
            if minecraft_dir.exists():
                mods_dir = minecraft_dir / "mods"
                config_dir = minecraft_dir / "config"
                if mods_dir.exists() or config_dir.exists():
                    return True

        return False

    def _get_modpack_info(self, path: Path, launcher: str) -> ModpackInfo:
        """Get modpack information including thumbnail."""
        info = ModpackInfo(
            name=path.name,
            path=path,
            launcher=launcher,
        )

        # Try CurseForge manifest.json first
        manifest_path = path / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    data = json.load(f)
                    info.name = data.get("name", info.name)
                    info.author = data.get("author", "")
                    info.version = data.get("version", "")
            except Exception:
                pass

        # Try CurseForge minecraftinstance.json for thumbnail and ID
        instance_json_path = path / "minecraftinstance.json"
        if instance_json_path.exists():
            try:
                with open(instance_json_path, encoding="utf-8") as f:
                    data = json.load(f)
                    info.name = data.get("name", info.name)

                    # CurseForge ID는 여러 위치에 있을 수 있음
                    # 1. Root projectID (가장 정확)
                    if data.get("projectID"):
                        info.curseforge_id = data.get("projectID")

                    installed_modpack = data.get("installedModpack")
                    if installed_modpack:
                        info.thumbnail_url = installed_modpack.get("thumbnailUrl", "")
                        info.website_url = installed_modpack.get("webSiteURL", "")

                        # 2. installedModpack.addonID (대체)
                        if not info.curseforge_id and installed_modpack.get("addonID"):
                            info.curseforge_id = installed_modpack.get("addonID")

                        # 3. installedModpack.projectID (구버전)
                        if not info.curseforge_id and installed_modpack.get(
                            "projectID"
                        ):
                            info.curseforge_id = installed_modpack.get("projectID")

                        # Override version if available
                        if installed_modpack.get("version"):
                            info.version = installed_modpack.get("version", "")

                        if not info.author:
                            authors = installed_modpack.get("authors", [])
                            if authors:
                                info.author = authors[0].get("name", "")
            except Exception as e:
                logger.debug("Failed to read minecraftinstance.json: %s", e)

        # Prism/MultiMC instance.cfg
        if launcher in ("Prism Launcher", "MultiMC"):
            cfg_file = path / "instance.cfg"
            if cfg_file.exists():
                try:
                    with open(cfg_file, encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("name="):
                                info.name = line.split("=", 1)[1].strip()
                                break
                except Exception:
                    pass

        return info


class FlowLayout(QVBoxLayout):
    """A layout that flows cards and adjusts columns based on width."""

    pass


class ModpackSelectionView(QWidget):
    """Modpack selection view with automatic launcher detection."""

    modpackSelected = Signal(Path)  # Emitted when modpack is selected

    CARD_WIDTH = 200
    CARD_HEIGHT = 240
    CARD_SPACING = 15

    def __init__(self, main_window: MainWindow) -> None:
        """Initialize modpack selection view."""
        super().__init__()
        self.main_window = main_window
        self.modpacks: list[ModpackInfo] = []
        self.modpack_cards: list[ModpackCard] = []
        self.selected_modpack: ModpackInfo | None = None
        self.network_manager = QNetworkAccessManager(self)
        self.scanner_thread: ScannerThread | None = None
        self._init_ui()
        self._scan_launchers()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        from ..i18n import get_translator

        t = get_translator()

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 30, 50, 30)

        # Title
        title = SubtitleLabel(t.t("modpack_select.title"))
        layout.addWidget(title)

        # Description
        desc = BodyLabel(t.t("modpack_select.description"))
        layout.addWidget(desc)

        # Loading indicator
        self.loading_container = QWidget()
        loading_layout = QVBoxLayout(self.loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bar = IndeterminateProgressBar()
        self.progress_bar.setFixedHeight(4)
        loading_layout.addWidget(self.progress_bar)

        self.loading_label = CaptionLabel("모드팩 스캔 중...")
        self.loading_label.setStyleSheet("color: #888888;")
        loading_layout.addWidget(self.loading_label)

        self.loading_container.hide()
        layout.addWidget(self.loading_container)

        # Modpack grid in scroll area
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setMinimumHeight(400)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(self.CARD_SPACING)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.manual_button = PushButton(FIF.FOLDER, t.t("common.browse"))
        self.refresh_button = PushButton(FIF.SYNC, t.t("common.refresh"))
        self.next_button = PrimaryPushButton(t.t("common.next"))
        self.next_button.setEnabled(False)

        button_layout.addWidget(self.manual_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.next_button)

        layout.addLayout(button_layout)

        # Connect signals
        self.manual_button.clicked.connect(self._on_manual_select)
        self.refresh_button.clicked.connect(self._scan_launchers)
        self.next_button.clicked.connect(self._on_next_clicked)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize to reflow cards."""
        super().resizeEvent(event)
        self._reflow_cards()

    def showEvent(self, event: object) -> None:
        """Handle show event to ensure proper layout."""
        super().showEvent(event)
        # Delay reflow to ensure layout is fully initialized
        QTimer.singleShot(100, self._reflow_cards)

    def _calculate_columns(self) -> int:
        """Calculate number of columns based on available width."""
        # Use scroll area width, fallback to parent or default
        try:
            viewport = self.scroll_area.viewport()
            if viewport and viewport.width() > 0:
                available_width = viewport.width() - 20  # margins
            else:
                # Fallback to scroll area width
                available_width = self.scroll_area.width() - 20
        except Exception:
            # Ultimate fallback
            available_width = 1000

        if available_width <= 0:
            return 4

        cols = max(1, available_width // (self.CARD_WIDTH + self.CARD_SPACING))
        return cols

    def _reflow_cards(self) -> None:
        """Reflow cards based on current width."""
        if not self.modpack_cards:
            return

        cols = self._calculate_columns()

        # Remove all items from layout (without deleting widgets)
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        # Re-add cards with new column count
        for i, card in enumerate(self.modpack_cards):
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)

    def _clear_grid(self) -> None:
        """Clear all cards from grid."""
        for card in self.modpack_cards:
            card.deleteLater()
        self.modpack_cards.clear()

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _scan_launchers(self) -> None:
        """Scan common launcher paths for modpacks."""
        # Clear existing
        self.modpacks.clear()
        self._clear_grid()
        self.selected_modpack = None
        self.next_button.setEnabled(False)

        # Show loading
        self.loading_container.show()
        self.progress_bar.start()
        self.refresh_button.setEnabled(False)
        self.manual_button.setEnabled(False)

        # Get launcher paths
        launcher_paths = self._get_launcher_paths()

        # Start background scan
        self.scanner_thread = ScannerThread(launcher_paths)
        self.scanner_thread.scanProgress.connect(self._on_scan_progress)
        self.scanner_thread.scanComplete.connect(self._on_scan_complete)
        self.scanner_thread.start()

    def _on_scan_progress(self, message: str) -> None:
        """Handle scan progress update."""
        self.loading_label.setText(message)

    def _on_scan_complete(self, modpacks: list[ModpackInfo]) -> None:
        """Handle scan completion."""
        self.modpacks = modpacks

        # Hide loading
        self.loading_container.hide()
        self.progress_bar.stop()
        self.refresh_button.setEnabled(True)
        self.manual_button.setEnabled(True)

        # Populate grid
        self._populate_grid()

        # Force layout update after delays to ensure proper sizing
        QTimer.singleShot(50, self._reflow_cards)
        QTimer.singleShot(150, self._reflow_cards)

        from ..i18n import get_translator

        t = get_translator()

        if self.modpacks:
            InfoBar.success(
                t.t("modpack_select.scan_complete"),
                t.t("modpack_select.scan_complete_msg", count=len(self.modpacks)),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000,
            )
        else:
            InfoBar.warning(
                t.t("modpack_select.no_modpacks"),
                t.t("modpack_select.no_modpacks_msg"),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )

    def _populate_grid(self) -> None:
        """Populate the grid with modpack cards."""
        cols = self._calculate_columns()

        for i, modpack in enumerate(self.modpacks):
            card = ModpackCard(modpack, self.network_manager)
            card.cardClicked.connect(self._on_card_clicked)
            card.cardDoubleClicked.connect(self._on_card_double_clicked)

            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)
            self.modpack_cards.append(card)

    def _get_launcher_paths(self) -> list[tuple[str, Path]]:
        """Get common launcher installation paths."""
        paths: list[tuple[str, Path]] = []

        # Windows paths
        if os.name == "nt":
            userprofile = Path.home()
            appdata = Path(os.getenv("APPDATA", ""))

            # CurseForge
            curseforge_path = userprofile / "curseforge" / "minecraft" / "Instances"
            if curseforge_path.exists():
                paths.append(("CurseForge", curseforge_path))

            # Prism Launcher
            prism_path = appdata / "PrismLauncher" / "instances"
            if prism_path.exists():
                paths.append(("Prism Launcher", prism_path))

            # MultiMC
            multimc_path = appdata / "MultiMC" / "instances"
            if multimc_path.exists():
                paths.append(("MultiMC", multimc_path))

        # Linux/Mac paths
        else:
            home = Path.home()

            # Prism Launcher (Linux)
            prism_linux = home / ".local" / "share" / "PrismLauncher" / "instances"
            if prism_linux.exists():
                paths.append(("Prism Launcher", prism_linux))

            # MultiMC (Linux)
            multimc_linux = home / ".local" / "share" / "multimc" / "instances"
            if multimc_linux.exists():
                paths.append(("MultiMC", multimc_linux))

        return paths

    def _on_card_clicked(self, modpack: ModpackInfo) -> None:
        """Handle card click."""
        # Deselect all cards
        for card in self.modpack_cards:
            card.set_selected(False)

        # Select clicked card
        for card in self.modpack_cards:
            if card.modpack == modpack:
                card.set_selected(True)
                break

        self.selected_modpack = modpack
        self.next_button.setEnabled(True)

    def _on_card_double_clicked(self, modpack: ModpackInfo) -> None:
        """Handle card double click."""
        self.selected_modpack = modpack
        self._on_next_clicked()

    def _on_manual_select(self) -> None:
        """Handle manual folder selection."""
        from ..i18n import get_translator

        t = get_translator()

        folder = QFileDialog.getExistingDirectory(
            self,
            t.t("modpack_select.select_folder"),
            str(Path.home()),
        )

        if folder:
            path = Path(folder)

            # Determine actual modpack path
            minecraft_dir = path / "minecraft"
            if not minecraft_dir.exists():
                minecraft_dir = path / ".minecraft"

            if minecraft_dir.exists():
                modpack_path = path
            elif path.name in ("minecraft", ".minecraft"):
                modpack_path = path.parent
            else:
                modpack_path = path

            # Create modpack info (use scanner thread method)
            info = ModpackInfo(
                name=modpack_path.name, path=modpack_path, launcher="Manual"
            )

            # Try to get more info
            manifest_path = modpack_path / "manifest.json"
            if manifest_path.exists():
                try:
                    logger.info("Reading manifest.json at %s", manifest_path)
                    with open(manifest_path, encoding="utf-8") as f:
                        data = json.load(f)
                        info.name = data.get("name", info.name)
                except Exception as e:
                    logger.error("Error reading manifest.json: %s", e)

            instance_json_path = modpack_path / "minecraftinstance.json"
            if instance_json_path.exists():
                try:
                    logger.info(
                        "Reading minecraftinstance.json at %s", instance_json_path
                    )
                    with open(instance_json_path, encoding="utf-8") as f:
                        data = json.load(f)
                        info.name = data.get("name", info.name)

                        # CurseForge ID 감지 (여러 위치 확인)
                        if data.get("projectID"):
                            info.curseforge_id = data.get("projectID")

                        installed_modpack = data.get("installedModpack")
                        if installed_modpack:
                            info.thumbnail_url = installed_modpack.get(
                                "thumbnailUrl", ""
                            )

                            # 대체 ID 위치 확인
                            if not info.curseforge_id and installed_modpack.get(
                                "addonID"
                            ):
                                info.curseforge_id = installed_modpack.get("addonID")
                            if not info.curseforge_id and installed_modpack.get(
                                "projectID"
                            ):
                                info.curseforge_id = installed_modpack.get("projectID")

                            info.version = installed_modpack.get(
                                "version", info.version
                            )
                except Exception:
                    pass

            self.modpacks.append(info)

            # Add card
            card = ModpackCard(info, self.network_manager)
            card.cardClicked.connect(self._on_card_clicked)
            card.cardDoubleClicked.connect(self._on_card_double_clicked)

            self.modpack_cards.append(card)

            # Reflow all cards
            self._reflow_cards()

            # Select it
            self._on_card_clicked(info)

    def _get_actual_modpack_path(self, path: Path) -> Path:
        """Get the actual modpack path containing mods/config."""
        if (path / "mods").exists() or (path / "config").exists():
            return path

        for minecraft_name in ("minecraft", ".minecraft"):
            minecraft_dir = path / minecraft_name
            if minecraft_dir.exists():
                if (minecraft_dir / "mods").exists() or (
                    minecraft_dir / "config"
                ).exists():
                    return minecraft_dir

        return path

    def _on_next_clicked(self) -> None:
        """Handle next button click."""
        if self.selected_modpack:
            modpack = self.selected_modpack

            # Get actual path where mods/config are located
            actual_path = self._get_actual_modpack_path(modpack.path)

            # Update main window state
            self.main_window.update_state("modpack_path", actual_path)
            self.main_window.update_state("modpack_name", modpack.name)
            self.main_window.update_state("modpack_info", modpack)

            # Emit signal with actual path
            self.modpackSelected.emit(actual_path)

            logger.info(
                "Selected modpack: %s at %s (actual: %s)",
                modpack.name,
                modpack.path,
                actual_path,
            )
