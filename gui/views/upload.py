"""Upload view for submitting translations to website."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
)

if TYPE_CHECKING:
    from ..app import MainWindow

logger = logging.getLogger(__name__)


class UploadView(QWidget):
    """View for uploading translations to website."""

    uploadRequested = Signal(
        int, str, bool, str
    )  # curseforge_id, version, anonymous, api_url
    skipRequested = Signal()

    def __init__(self, main_window: MainWindow) -> None:
        super().__init__()
        self.main_window = main_window
        self.api_url = "https://mcat.2odk.com/api"
        self._init_ui()

    def _init_ui(self) -> None:
        from ..i18n import get_translator

        t = get_translator()

        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(50, 30, 50, 30)

        # Title and description
        title_layout = QVBoxLayout()
        title_layout.setSpacing(8)

        title = SubtitleLabel(t.t("upload.title"))
        title_layout.addWidget(title)

        desc = BodyLabel(t.t("upload.description"))
        desc.setStyleSheet("color: #888888;")
        title_layout.addWidget(desc)

        layout.addLayout(title_layout)

        # Modpack Info Card
        info_card = CardWidget()
        info_card_layout = QVBoxLayout(info_card)
        info_card_layout.setSpacing(15)
        info_card_layout.setContentsMargins(25, 25, 25, 25)

        info_title = StrongBodyLabel("모드팩 정보")
        info_card_layout.addWidget(info_title)

        info_grid = QGridLayout()
        info_grid.setSpacing(12)
        info_grid.setColumnStretch(1, 1)

        self.info_name_label = BodyLabel("모드팩: -")
        self.info_version_label = BodyLabel("버전: -")
        self.info_id_label = BodyLabel("CurseForge ID: -")

        info_grid.addWidget(self.info_name_label, 0, 0)
        info_grid.addWidget(self.info_version_label, 1, 0)
        info_grid.addWidget(self.info_id_label, 2, 0)

        info_card_layout.addLayout(info_grid)
        layout.addWidget(info_card)

        # Upload Settings Card
        settings_card = CardWidget()
        settings_card_layout = QVBoxLayout(settings_card)
        settings_card_layout.setSpacing(15)
        settings_card_layout.setContentsMargins(25, 25, 25, 25)

        settings_title = StrongBodyLabel("업로드 설정")
        settings_card_layout.addWidget(settings_title)

        # CurseForge ID input
        id_layout = QVBoxLayout()
        id_layout.setSpacing(5)
        id_label = BodyLabel(t.t("upload.curseforge_id"))
        id_layout.addWidget(id_label)
        self.curseforge_id = LineEdit()
        self.curseforge_id.setPlaceholderText("자동 감지됨 - 필요시 수정")
        id_layout.addWidget(self.curseforge_id)
        settings_card_layout.addLayout(id_layout)

        # Version input
        version_layout = QVBoxLayout()
        version_layout.setSpacing(5)
        version_label = BodyLabel(t.t("upload.modpack_version"))
        version_layout.addWidget(version_label)
        self.modpack_version = LineEdit()
        self.modpack_version.setPlaceholderText("자동 감지됨 - 필요시 수정")
        version_layout.addWidget(self.modpack_version)
        settings_card_layout.addLayout(version_layout)

        layout.addWidget(settings_card)

        # Account Card
        account_card = CardWidget()
        account_card_layout = QVBoxLayout(account_card)
        account_card_layout.setSpacing(12)
        account_card_layout.setContentsMargins(25, 25, 25, 25)

        account_title = StrongBodyLabel("계정")
        account_card_layout.addWidget(account_title)

        self.account_status_label = BodyLabel(
            "로그인하면 업로드가 계정에 연결됩니다."
        )
        self.account_status_label.setStyleSheet("color: #888888;")
        account_card_layout.addWidget(self.account_status_label)

        account_btn_layout = QHBoxLayout()
        self.login_button = PushButton("Discord 로그인")
        self.logout_button = PushButton("로그아웃")
        self.logout_button.setVisible(False)
        account_btn_layout.addWidget(self.login_button)
        account_btn_layout.addWidget(self.logout_button)
        account_btn_layout.addStretch()
        account_card_layout.addLayout(account_btn_layout)

        layout.addWidget(account_card)

        # Progress bar (hidden initially)
        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = BodyLabel("")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        self.skip_button = PushButton(t.t("upload.skip_button"))
        self.upload_button = PrimaryPushButton(t.t("upload.upload_button"))

        button_layout.addWidget(self.skip_button)
        button_layout.addStretch()
        button_layout.addWidget(self.upload_button)

        layout.addLayout(button_layout)

        # Connect signals
        self.skip_button.clicked.connect(self.skipRequested.emit)
        self.upload_button.clicked.connect(self._on_upload_clicked)

    def showEvent(self, event: object) -> None:
        super().showEvent(event)
        self._load_modpack_info()
        self._refresh_account_ui()

    def _refresh_account_ui(self) -> None:
        """Update the account card to reflect current login state."""
        from ..config import get_config

        config = get_config()

        if config.get("auth.token"):
            user_name = config.get("auth.user_name", "사용자")
            self.account_status_label.setText(f"{user_name}님으로 로그인됨")
            self.account_status_label.setStyleSheet("color: #4ade80;")
            self.login_button.setVisible(False)
            self.logout_button.setVisible(True)
        else:
            self.account_status_label.setText(
                "로그인하면 업로드가 계정에 연결됩니다."
            )
            self.account_status_label.setStyleSheet("color: #888888;")
            self.login_button.setVisible(True)
            self.logout_button.setVisible(False)

    def _load_modpack_info(self) -> None:
        modpack_info = self.main_window.state.get("modpack_info")

        if modpack_info:
            self.info_name_label.setText(f"모드팩: {modpack_info.name}")
            self.info_version_label.setText(
                f"버전: {modpack_info.version or '알 수 없음'}"
            )

            if modpack_info.curseforge_id:
                self.info_id_label.setText(
                    f"CurseForge ID: {modpack_info.curseforge_id}"
                )
                self.curseforge_id.setText(str(modpack_info.curseforge_id))
                self.curseforge_id.setEnabled(False)
            else:
                self.info_id_label.setText("CurseForge ID: 감지 안됨")
                self.curseforge_id.setEnabled(True)

            if modpack_info.version:
                self.modpack_version.setText(modpack_info.version)
                self.modpack_version.setEnabled(False)
            else:
                self.modpack_version.setEnabled(True)

            logger.info(
                "Auto-filled upload form: %s (ID: %s, Version: %s)",
                modpack_info.name,
                modpack_info.curseforge_id,
                modpack_info.version,
            )
        else:
            self.info_name_label.setText("모드팩: 알 수 없음")
            self.info_version_label.setText("버전: 알 수 없음")
            self.info_id_label.setText("CurseForge ID: 알 수 없음")
            self.curseforge_id.setEnabled(True)
            self.modpack_version.setEnabled(True)

            InfoBar.warning(
                "자동 감지 실패",
                "모드팩 정보를 찾을 수 없습니다. 수동으로 입력해주세요.",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )

    def _on_upload_clicked(self) -> None:
        try:
            curseforge_id = int(self.curseforge_id.text())
            version = self.modpack_version.text()

            from ..config import get_config

            config = get_config()
            anonymous = not bool(config.get("auth.token"))

            if not version:
                self.status_label.setText("모드팩 버전을 입력해주세요.")
                self.status_label.setVisible(True)
                return

            self.upload_button.setEnabled(False)
            self.skip_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.status_label.setText("업로드 중...")
            self.status_label.setVisible(True)

            self.uploadRequested.emit(curseforge_id, version, anonymous, self.api_url)

        except ValueError:
            self.status_label.setText("올바른 CurseForge ID를 입력해주세요.")
            self.status_label.setVisible(True)

    def update_status(self, message: str) -> None:
        self.status_label.setText(message)

    def reset_after_error(self, error_message: str) -> None:
        self.upload_button.setEnabled(True)
        self.skip_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"업로드 실패: {error_message}")
        self.status_label.setVisible(True)
