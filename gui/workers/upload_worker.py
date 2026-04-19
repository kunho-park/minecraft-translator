"""Background worker for uploading translations."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TypedDict

from PySide6.QtCore import QThread, Signal


logger = logging.getLogger(__name__)


class TranslationStatsDict(TypedDict, total=False):
    """번역 통계 정보 (GUI에서 전달용)"""
    file_count: int
    total_entries: int
    translated_entries: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    handler_stats: dict[str, int]
    duration_seconds: float


class UploadWorker(QThread):
    """Background worker for uploading translations to website."""
    
    # Signals
    uploadProgress = Signal(str)  # message
    uploadComplete = Signal(dict)  # result
    uploadError = Signal(str)  # error message
    
    def __init__(
        self,
        curseforge_id: int,
        modpack_version: str,
        resource_pack_path: Path | None,
        override_path: Path | None,
        config: dict[str, object],
        api_url: str,
        anonymous: bool,
        translation_stats: TranslationStatsDict | None = None,
        auth_token: str | None = None,
    ) -> None:
        super().__init__()
        self.curseforge_id = curseforge_id
        self.modpack_version = modpack_version
        self.resource_pack_path = resource_pack_path
        self.override_path = override_path
        self.config = config
        self.api_url = api_url
        self.anonymous = anonymous
        self.translation_stats = translation_stats
        self.auth_token = auth_token
    
    def run(self) -> None:
        """Run the upload operation."""
        try:
            from src.output.uploader import (
                upload_to_website,
                TranslationConfig,
                TranslationStats,
            )
            from gui.i18n import get_translator

            t = get_translator()

            logger.info("Starting upload to %s", self.api_url)
            self.uploadProgress.emit(t.t("upload.preparing_status"))
            
            # Prepare translation config
            translation_config: TranslationConfig = {
                "source_lang": str(self.config.get("source_locale", "en_us")),
                "target_lang": str(self.config.get("target_locale", "ko_kr")),
                "llm_model": str(self.config.get("llm_model", "")),
                "temperature": float(self.config.get("llm_temperature", 0.1)),
                "batch_size": int(self.config.get("batch_size", 30)),
                "used_glossary": not bool(self.config.get("skip_glossary", False)),
                "reviewed": not bool(self.config.get("skip_review", False)),
            }
            
            # Prepare translation stats
            translation_stats: TranslationStats | None = None
            if self.translation_stats:
                translation_stats = TranslationStats(
                    file_count=self.translation_stats.get("file_count", 0),
                    total_entries=self.translation_stats.get("total_entries", 0),
                    translated_entries=self.translation_stats.get("translated_entries", 0),
                    input_tokens=self.translation_stats.get("input_tokens", 0),
                    output_tokens=self.translation_stats.get("output_tokens", 0),
                    total_tokens=self.translation_stats.get("total_tokens", 0),
                    handler_stats=self.translation_stats.get("handler_stats", {}),
                    duration_seconds=self.translation_stats.get("duration_seconds", 0.0),
                )
            
            # Run upload in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                self.uploadProgress.emit(t.t("upload.uploading_status"))
                
                result = loop.run_until_complete(
                    upload_to_website(
                        curseforge_id=self.curseforge_id,
                        modpack_version=self.modpack_version,
                        resource_pack_path=self.resource_pack_path,
                        override_path=self.override_path,
                        translation_config=translation_config,
                        translation_stats=translation_stats,
                        api_url=self.api_url,
                        anonymous=self.anonymous,
                        auth_token=self.auth_token,
                    )
                )
                
                if result["success"]:
                    self.uploadComplete.emit(result)
                    logger.info("Upload successful: %s", result.get("pack_id"))
                else:
                    self.uploadError.emit(result.get("message", "Unknown error"))
                    
            finally:
                loop.close()
                
        except Exception as e:
            logger.exception("Upload error: %s", e)
            self.uploadError.emit(str(e))
