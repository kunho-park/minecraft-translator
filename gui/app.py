"""Main application window with navigation."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from .config import get_config
from .i18n import get_translator, set_language

logger = logging.getLogger(__name__)

load_dotenv()


class MainWindow(QMainWindow):
    """Main application window with multi-step navigation."""

    # Signals for step transitions
    stepChanged = Signal(int)  # Current step index

    def __init__(self) -> None:
        """Initialize main window."""
        super().__init__()
        self.config = get_config()
        self.translator = get_translator()
        self.current_step = 0

        # State management
        self.state: dict[str, Any] = {
            "modpack_path": None,
            "output_path": None,
            "scan_result": None,
            "selected_files": [],
            "pipeline_config": {},
            "pipeline_result": None,
        }

        self._init_window()
        self._load_views()

    def _init_window(self) -> None:
        """Initialize window properties."""
        app_name = self.translator.t("app.name", "Modpack Translator")
        self.setWindowTitle(
            f"{app_name} - {self.translator.t('app.subtitle', 'Fluent Design')}"
        )
        self.resize(1200, 800)

        # Center window
        screen = self.screen().geometry()
        window_geo = self.frameGeometry()
        window_geo.moveCenter(screen.center())
        self.move(window_geo.topLeft())

        # Create menu bar
        self._create_menu_bar()

        # Check for updates on startup
        from PySide6.QtCore import QTimer

        QTimer.singleShot(1000, lambda: self.check_updates(manual=False))

    def _create_menu_bar(self) -> None:
        """Create menu bar with language selection."""
        menu_bar = self.menuBar()

        # Settings menu
        settings_menu = menu_bar.addMenu(self.translator.t("settings.title"))

        # Update action
        update_action = QAction(self.translator.t("update.checking"), self)
        update_action.triggered.connect(lambda: self.check_updates(manual=True))
        settings_menu.addAction(update_action)
        settings_menu.addSeparator()

        # Language submenu
        language_menu = settings_menu.addMenu(
            self.translator.t("settings.language.title")
        )

        # Korean action
        korean_action = QAction(self.translator.t("settings.language.korean"), self)
        korean_action.setCheckable(True)
        korean_action.setChecked(self.translator.current_language == "ko")
        korean_action.triggered.connect(lambda: self._change_language("ko"))
        language_menu.addAction(korean_action)

        # English action
        english_action = QAction(self.translator.t("settings.language.english"), self)
        english_action.setCheckable(True)
        english_action.setChecked(self.translator.current_language == "en")
        english_action.triggered.connect(lambda: self._change_language("en"))
        language_menu.addAction(english_action)

        # Store actions for updating later
        self._language_actions = {
            "ko": korean_action,
            "en": english_action,
        }

    def _change_language(self, language: str) -> None:
        """Change application language.

        Args:
            language: Language code (e.g., "ko", "en")
        """
        if set_language(language):
            # Update all language actions
            for lang_code, action in self._language_actions.items():
                action.setChecked(lang_code == language)

            # Update window title
            app_name = self.translator.t("app.name", "Modpack Translator")
            self.setWindowTitle(
                f"{app_name} - {self.translator.t('app.subtitle', 'Fluent Design')}"
            )

            # Recreate menu bar with new translations
            self.menuBar().clear()
            self._create_menu_bar()

            # Reload all views with new translations
            self._reload_views()

            logger.info("Language changed to: %s", language)

    def _reload_views(self) -> None:
        """Reload all views to update translations."""
        # Save current step and state
        current_step = self.current_step
        saved_state = dict(self.state)

        # Remove all widgets from stack
        while self.view_stack.count() > 0:
            widget = self.view_stack.widget(0)
            self.view_stack.removeWidget(widget)
            widget.deleteLater()

        # Recreate all views
        from .views.category_select import CategorySelectionView
        from .views.completion import CompletionView
        from .views.modpack_select import ModpackSelectionView
        from .views.retry import RetryView
        from .views.scan_result import ScanResultView
        from .views.translation_progress import TranslationProgressView
        from .views.upload import UploadView
        from .views.welcome import WelcomeView

        self.welcome_view = WelcomeView(self)
        self.modpack_select_view = ModpackSelectionView(self)
        self.scan_result_view = ScanResultView(self)
        self.category_select_view = CategorySelectionView(self)
        self.progress_view = TranslationProgressView(self)
        self.retry_view = RetryView(self)
        self.upload_view = UploadView(self)
        self.completion_view = CompletionView(self)

        self.view_stack.addWidget(self.welcome_view)  # 0
        self.view_stack.addWidget(self.modpack_select_view)  # 1
        self.view_stack.addWidget(self.scan_result_view)  # 2
        self.view_stack.addWidget(self.category_select_view)  # 3
        self.view_stack.addWidget(self.progress_view)  # 4
        self.view_stack.addWidget(self.retry_view)  # 5
        self.view_stack.addWidget(self.upload_view)  # 6
        self.view_stack.addWidget(self.completion_view)  # 7

        # Reconnect signals
        self._connect_view_signals()

        # Restore state
        self.state = saved_state

        # Restore current step
        self.view_stack.setCurrentIndex(current_step)
        self.current_step = current_step

        logger.info("Views reloaded with new language")

    def _load_views(self) -> None:
        """Load all views and connect them."""
        from .views.category_select import CategorySelectionView
        from .views.completion import CompletionView
        from .views.modpack_select import ModpackSelectionView
        from .views.retry import RetryView
        from .views.scan_result import ScanResultView
        from .views.translation_progress import TranslationProgressView
        from .views.upload import UploadView
        from .views.welcome import WelcomeView

        # Create all views
        self.welcome_view = WelcomeView(self)
        self.modpack_select_view = ModpackSelectionView(self)
        self.scan_result_view = ScanResultView(self)
        self.category_select_view = CategorySelectionView(self)
        self.progress_view = TranslationProgressView(self)
        self.retry_view = RetryView(self)
        self.upload_view = UploadView(self)
        self.completion_view = CompletionView(self)

        # Create central widget with stacked layout
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.view_stack = QStackedWidget()
        self.view_stack.addWidget(self.welcome_view)  # 0
        self.view_stack.addWidget(self.modpack_select_view)  # 1
        self.view_stack.addWidget(self.scan_result_view)  # 2
        self.view_stack.addWidget(self.category_select_view)  # 3
        self.view_stack.addWidget(self.progress_view)  # 4
        self.view_stack.addWidget(self.retry_view)  # 5
        self.view_stack.addWidget(self.upload_view)  # 6
        self.view_stack.addWidget(self.completion_view)  # 7

        container_layout.addWidget(self.view_stack)

        # Set central widget (standard QMainWindow approach)
        self.setCentralWidget(container)

        # Connect view signals
        self._connect_view_signals()

    def _connect_view_signals(self) -> None:
        """Connect signals between views."""
        # Welcome -> Modpack Select
        self.welcome_view.translate_card.button.clicked.connect(
            lambda: self.go_to_step(1)
        )

        # Modpack Select -> Scan (with worker)
        self.modpack_select_view.modpackSelected.connect(self._on_modpack_selected)

        # Scan Result -> Category Select
        self.scan_result_view.settingsConfirmed.connect(self._on_settings_confirmed)

        # Category Select -> Translation
        self.category_select_view.filesSelected.connect(self._on_files_selected)

        # Retry signals
        self.retry_view.retryRequested.connect(self._on_retry_requested)
        self.retry_view.skipRequested.connect(self._on_retry_skip)

        # Upload signals
        self.upload_view.uploadRequested.connect(self._on_upload_requested)
        self.upload_view.skipRequested.connect(
            lambda: self.go_to_step(7)
        )  # Skip to completion

    def _on_modpack_selected(self, modpack_path: Path) -> None:
        """Handle modpack selection - start scanning.

        Args:
            modpack_path: Selected modpack path
        """
        from .widgets.loading_dialog import LoadingDialog
        from .workers.scanner_worker import ScannerWorker

        # Store modpack path
        self.state["modpack_path"] = modpack_path

        # Create and start scanner worker
        config = self.state.get("pipeline_config", {})
        source_locale = str(config.get("source_locale", "en_us"))
        target_locale = str(config.get("target_locale", "ko_kr"))

        # Show loading dialog
        self.loading_dialog = LoadingDialog("모드팩 스캔 중", "파일 검색 중...", self)
        self.loading_dialog.show()

        self.scanner_worker = ScannerWorker(modpack_path, source_locale, target_locale)
        self.scanner_worker.scanProgress.connect(self._on_scan_progress)
        self.scanner_worker.scanComplete.connect(self._on_scan_complete)
        self.scanner_worker.scanError.connect(self._on_scan_error)
        self.scanner_worker.start()

        logger.info("Started scanning: %s", modpack_path)

    def _on_scan_progress(self, message: str, current: int, total: int) -> None:
        """Handle scan progress update.

        Args:
            message: Progress message
            current: Current progress value
            total: Total progress value
        """
        logger.debug("Scan progress: %s (%d/%d)", message, current, total)
        if hasattr(self, "loading_dialog") and self.loading_dialog:
            self.loading_dialog.set_message(message)

    def _on_scan_complete(self, scan_result: object) -> None:
        """Handle scan completion.

        Args:
            scan_result: Scan result from worker
        """
        from src.scanner import ScanResult

        # Close loading dialog
        if hasattr(self, "loading_dialog") and self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        result: ScanResult = scan_result  # type: ignore[assignment]
        self.state["scan_result"] = result

        # Update scan result view
        self.scan_result_view.set_scan_result(result)

        # Move to scan result view
        self.go_to_step(2)

        logger.info("Scan complete, showing results")

    def _on_scan_error(self, error: str) -> None:
        """Handle scan error.

        Args:
            error: Error message
        """
        # Close loading dialog
        if hasattr(self, "loading_dialog") and self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        logger.error("Scan error: %s", error)
        # Could show error dialog here

    def _on_settings_confirmed(self, settings: dict[str, object]) -> None:
        """Handle settings confirmation from scan result view.

        Args:
            settings: Pipeline configuration settings
        """
        # Get scan result
        scan_result = self.state.get("scan_result")
        if not scan_result:
            logger.error("No scan result available")
            return

        # Load files into category selection view
        file_pairs = scan_result.all_translation_pairs
        self.category_select_view.load_files(file_pairs)

        # Move to category selection
        self.go_to_step(3)

        logger.info("Loaded %d file pairs into category selection", len(file_pairs))

    def _on_files_selected(self, selected_files: list[object]) -> None:
        """Handle file selection - start translation.

        Args:
            selected_files: Selected language file pairs
        """
        from .workers.translation_worker import TranslationWorker

        modpack_path = Path(str(self.state["modpack_path"]))

        # Create output directory with modpack name and timestamp
        modpack_name = str(self.state.get("modpack_name", modpack_path.name))
        # Sanitize modpack name for filesystem
        safe_modpack_name = "".join(
            c for c in modpack_name if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        if not safe_modpack_name:
            safe_modpack_name = "modpack"

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = (
            modpack_path.parent / "translation_output" / safe_modpack_name / timestamp
        )
        output_path.mkdir(parents=True, exist_ok=True)

        self.state["output_path"] = output_path

        # Create and start translation worker
        self.translation_worker = TranslationWorker(
            modpack_path,
            output_path,
            selected_files,  # type: ignore[arg-type]
            dict(self.state["pipeline_config"]),
        )
        self.translation_worker.progressUpdate.connect(self._on_translation_progress)
        self.translation_worker.translationComplete.connect(
            self._on_translation_complete
        )
        self.translation_worker.translationCancelled.connect(
            self._on_translation_cancelled
        )
        self.translation_worker.translationError.connect(self._on_translation_error)
        self.progress_view.stopRequested.connect(self.translation_worker.cancel)

        # Move to progress view
        self.go_to_step(4)
        self.translation_worker.start()

        logger.info("Started translation")

    def _on_translation_progress(
        self,
        message: str,
        current: int,
        total: int,
        stats: dict[str, object],
    ) -> None:
        """Handle translation progress update.

        Args:
            message: Progress message
            current: Current progress
            total: Total items
            stats: Additional statistics
        """
        self.progress_view.update_progress(message, current, total, stats)

    def _on_translation_complete(self, result: object) -> None:
        """Handle translation completion.

        Args:
            result: Pipeline result
        """
        from src.pipeline import PipelineResult

        pipeline_result: PipelineResult = result  # type: ignore[assignment]

        # Merge with existing result if retrying
        existing_result = self.state.get("pipeline_result")
        if existing_result:
            # Merge retry results with original
            self._merge_pipeline_results(existing_result, pipeline_result)
            pipeline_result = existing_result

        self.state["pipeline_result"] = pipeline_result

        # Check if there are failures
        if pipeline_result.has_failures:
            # Show retry view (don't mark as complete)
            self.retry_view.set_failed_summary(pipeline_result)
            self.go_to_step(5)

            logger.warning(
                "Translation completed with failures: %d/%d successful",
                pipeline_result.translated_entries,
                pipeline_result.total_entries,
            )
        else:
            # All successful - mark as complete
            self.progress_view.complete()

            # Set completion result for later use
            output_path = self.state.get("output_path")
            if output_path:
                self.completion_view.set_result(pipeline_result, output_path)

            # Move to upload view
            logger.info(
                "Translation complete: %d/%d successful - moving to upload view",
                pipeline_result.translated_entries,
                pipeline_result.total_entries,
            )
            self.go_to_step(6)  # Upload View

    def _merge_pipeline_results(self, existing: object, retry: object) -> None:
        """Merge retry results into existing pipeline result.

        Args:
            existing: Existing pipeline result
            retry: Retry pipeline result
        """
        from src.pipeline import PipelineResult

        existing_result: PipelineResult = existing  # type: ignore[assignment]
        retry_result: PipelineResult = retry  # type: ignore[assignment]

        # Update tasks from retry result
        for retry_task in retry_result.tasks:
            # Find matching task in existing result
            for existing_task in existing_result.tasks:
                if (
                    existing_task.file_pair.source_path
                    == retry_task.file_pair.source_path
                ):
                    # Update the existing task with retry results
                    existing_task.entries = retry_task.entries
                    break

        # Update generation result
        if retry_result.generation_result:
            existing_result.generation_result = retry_result.generation_result

        # Recalculate statistics
        existing_result.update_statistics()

        logger.info(
            "Merged retry results: %d/%d successful",
            existing_result.translated_entries,
            existing_result.total_entries,
        )

    def _on_retry_skip(self) -> None:
        """Handle skip request from retry view."""
        # When skipping retry, we want to proceed with whatever results we have
        pipeline_result = self.state.get("pipeline_result")
        output_path = self.state.get("output_path")

        if pipeline_result and output_path:
            # Set result on completion view so it's ready when we get there
            self.completion_view.set_result(pipeline_result, output_path)

        self.go_to_step(6)  # Upload view

    def _on_translation_cancelled(self) -> None:
        """Handle translation cancellation."""
        logger.info("Translation cancelled by user")
        # Go back to main screen (Welcome View)
        self.go_to_step(0)

    def _on_translation_error(self, error: str) -> None:
        """Handle translation error.

        Args:
            error: Error message
        """
        logger.error("Translation error: %s", error)

    def _on_retry_requested(self) -> None:
        """Handle retry request - retry only failed files."""
        from .workers.translation_worker import TranslationWorker

        pipeline_result = self.state.get("pipeline_result")
        if not pipeline_result or not pipeline_result.has_failures:
            logger.warning("No failures to retry")
            return

        # Get failed file pairs
        failed_files = pipeline_result.get_failed_file_pairs()
        if not failed_files:
            logger.warning("No failed files found")
            return

        modpack_path = Path(str(self.state["modpack_path"]))
        output_path = Path(str(self.state["output_path"]))

        # Create and start translation worker with only failed files
        self.translation_worker = TranslationWorker(
            modpack_path,
            output_path,
            failed_files,
            dict(self.state["pipeline_config"]),
            previous_result=pipeline_result,
        )
        self.translation_worker.progressUpdate.connect(self._on_translation_progress)
        self.translation_worker.translationComplete.connect(
            self._on_translation_complete
        )
        self.translation_worker.translationError.connect(self._on_translation_error)

        # Move to progress view and start
        self.go_to_step(4)
        self.translation_worker.start()

        logger.info("Retrying %d failed files", len(failed_files))

    def _on_upload_requested(
        self,
        curseforge_id: int,
        version: str,
        anonymous: bool,
        api_url: str,
    ) -> None:
        """Handle upload request.

        Args:
            curseforge_id: CurseForge modpack ID
            version: Modpack version
            anonymous: Whether to upload anonymously
            api_url: API base URL
        """
        from .workers.upload_worker import UploadWorker

        result = self.state.get("pipeline_result")
        if not result or not result.generation_result:
            logger.error("No translation result to upload")
            return

        gen_result = result.generation_result

        # Prepare translation stats from pipeline result
        translation_stats = {
            "file_count": result.file_count,
            "total_entries": result.total_entries,
            "translated_entries": result.translated_entries,
            "input_tokens": result.total_input_tokens,
            "output_tokens": result.total_output_tokens,
            "total_tokens": result.total_tokens,
            "handler_stats": result.handler_stats,
            "duration_seconds": result.duration_seconds,
        }

        self.upload_worker = UploadWorker(
            curseforge_id=curseforge_id,
            modpack_version=version,
            resource_pack_path=gen_result.resource_pack_path,
            override_path=gen_result.override_zip_path,
            config=dict(self.state["pipeline_config"]),
            api_url=api_url,
            anonymous=anonymous,
            translation_stats=translation_stats,
        )
        self.upload_worker.uploadProgress.connect(self.upload_view.update_status)
        self.upload_worker.uploadComplete.connect(self._on_upload_complete)
        self.upload_worker.uploadError.connect(self._on_upload_error)
        self.upload_worker.start()

        logger.info("Started upload to %s", api_url)

    def _on_upload_complete(self, result: dict[str, object]) -> None:
        """Handle upload completion.

        Args:
            result: Upload result
        """
        logger.info("Upload complete: %s", result)
        # Show completion view (step 7)
        self.go_to_step(7)

    def _on_upload_error(self, error: str) -> None:
        """Handle upload error.

        Args:
            error: Error message
        """
        logger.error("Upload error: %s", error)
        self.upload_view.update_status(f"업로드 실패: {error}")

    def go_to_step(self, step: int) -> None:
        """Navigate to a specific step.

        Args:
            step: Step index to navigate to
        """
        if 0 <= step < self.view_stack.count():
            self.current_step = step
            self.view_stack.setCurrentIndex(step)
            self.stepChanged.emit(step)
            logger.debug("Navigated to step %d", step)

    def next_step(self) -> None:
        """Navigate to next step."""
        if self.current_step < self.view_stack.count() - 1:
            self.go_to_step(self.current_step + 1)

    def previous_step(self) -> None:
        """Navigate to previous step."""
        if self.current_step > 0:
            self.go_to_step(self.current_step - 1)

    def update_state(self, key: str, value: Any) -> None:
        """Update application state.

        Args:
            key: State key
            value: State value
        """
        self.state[key] = value
        logger.debug("State updated: %s = %s", key, type(value).__name__)

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get application state value.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value
        """
        return self.state.get(key, default)

    def check_updates(self, manual: bool = False) -> None:
        """Check for updates.

        Args:
            manual: Whether this is a manual check initiated by user
        """
        from qfluentwidgets import InfoBar, InfoBarPosition

        from .workers.update_worker import UpdateWorker

        if manual:
            InfoBar.info(
                title=self.translator.t("update.checking"),
                content="",
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self,
            )

        self.update_worker = UpdateWorker()
        self.update_worker.updateAvailable.connect(self._on_update_available)
        self.update_worker.noUpdate.connect(lambda: self._on_no_update(manual))
        self.update_worker.updateError.connect(
            lambda e: self._on_update_error(e, manual)
        )
        self.update_worker.start()

    def _on_update_available(
        self, version: str, release_notes: str, download_url: str
    ) -> None:
        """Handle update available.

        Args:
            version: New version string
            release_notes: Release notes
            download_url: Download URL
        """
        from .widgets.update_dialog import UpdateDialog

        dialog = UpdateDialog(version, release_notes, download_url, self)
        dialog.show()

    def _on_no_update(self, manual: bool) -> None:
        """Handle no update available.

        Args:
            manual: Whether this was a manual check
        """
        from qfluentwidgets import InfoBar, InfoBarPosition

        if manual:
            InfoBar.success(
                title=self.translator.t("update.uptodate"),
                content="",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self,
            )

    def _on_update_error(self, error: str, manual: bool) -> None:
        """Handle update check error.

        Args:
            error: Error message
            manual: Whether this was a manual check
        """
        from qfluentwidgets import InfoBar, InfoBarPosition

        if manual:
            InfoBar.error(
                title=self.translator.t("update.error"),
                content=error,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self,
            )
