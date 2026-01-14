"""Background worker for modpack scanning."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QThread, Signal

if TYPE_CHECKING:
    from src.scanner import ScanResult

logger = logging.getLogger(__name__)


class ScannerWorker(QThread):
    """Background worker for scanning modpack files.
    
    Runs ModpackScanner in a separate thread to avoid blocking the UI.
    """
    
    # Signals
    scanProgress = Signal(str, int, int)  # message, current, total
    scanComplete = Signal(object)  # ScanResult
    scanError = Signal(str)  # error message
    
    def __init__(
        self,
        modpack_path: Path,
        source_locale: str = "en_us",
        target_locale: str = "ko_kr",
    ) -> None:
        """Initialize scanner worker.
        
        Args:
            modpack_path: Path to modpack directory
            source_locale: Source language locale
            target_locale: Target language locale
        """
        super().__init__()
        self.modpack_path = modpack_path
        self.source_locale = source_locale
        self.target_locale = target_locale
        self._is_cancelled = False
    
    def _progress_callback(
        self, stage: str, current: int, total: int, detail: str
    ) -> None:
        """Progress callback for scanner.
        
        Args:
            stage: Current stage name
            current: Current progress
            total: Total steps
            detail: Detail message
        """
        # Convert to percentage
        if total > 0:
            percent = int((current / total) * 100)
        else:
            percent = 0
        
        message = f"{stage}: {detail}"
        self.scanProgress.emit(message, percent, 100)
    
    def run(self) -> None:
        """Run the scanning operation."""
        try:
            from src.scanner import ModpackScanner
            
            logger.info("Starting modpack scan: %s", self.modpack_path)
            self.scanProgress.emit("모드팩 스캔 시작...", 0, 100)
            
            # Create scanner with progress callback
            scanner = ModpackScanner(
                self.source_locale,
                self.target_locale,
                progress_callback=self._progress_callback,
            )
            
            # Scan modpack
            result = scanner.scan(self.modpack_path)
            
            if self._is_cancelled:
                return
            
            self.scanProgress.emit("스캔 완료!", 100, 100)
            self.scanComplete.emit(result)
            
            logger.info(
                "Scan complete: %d source files, %d target files, total: %d",
                result.total_source_files,
                result.total_target_files,
                len(result.translation_files),
            )
            
        except Exception as e:
            logger.exception("Scanner error: %s", e)
            self.scanError.emit(str(e))
    
    def cancel(self) -> None:
        """Cancel the scanning operation."""
        self._is_cancelled = True
        logger.info("Scanner worker cancelled")
