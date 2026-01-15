"""Pydantic models for translation tasks and results."""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Mapping


class TranslationStatus(str, Enum):
    """Status of a translation task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class LanguageFilePair(BaseModel):
    """A pair of source and target language files."""

    source_path: Path = Field(
        ...,
        description="Path to source language file (e.g., en_us.json)",
    )
    target_path: Path | None = Field(
        default=None,
        description="Path to existing target language file (e.g., ko_kr.json)",
    )
    namespace: str = Field(
        default="",
        description="Mod namespace (e.g., 'minecraft', 'mekanism')",
    )
    mod_id: str = Field(
        default="",
        description="Mod identifier",
    )

    @property
    def has_existing_translation(self) -> bool:
        """Check if a target translation already exists."""
        return self.target_path is not None and self.target_path.exists()


class TranslationEntry(BaseModel):
    """A single translation entry."""

    key: str = Field(
        ...,
        description="Translation key",
    )
    source_text: str = Field(
        ...,
        description="Original text to translate",
    )
    translated_text: str | None = Field(
        default=None,
        description="Translated text",
    )
    status: TranslationStatus = Field(
        default=TranslationStatus.PENDING,
        description="Translation status",
    )
    error: str | None = Field(
        default=None,
        description="Error message if translation failed",
    )
    previous_error: str | None = Field(
        default=None,
        description="Previous error message for retry context",
    )


class TranslationBatch(BaseModel):
    """A batch of translation entries for processing."""

    entries: list[TranslationEntry] = Field(
        default_factory=list,
        description="Translation entries in this batch",
    )
    batch_id: int = Field(
        default=0,
        description="Batch identifier",
    )

    @property
    def pending_count(self) -> int:
        """Count of pending translations."""
        return sum(1 for e in self.entries if e.status == TranslationStatus.PENDING)

    @property
    def completed_count(self) -> int:
        """Count of completed translations."""
        return sum(1 for e in self.entries if e.status == TranslationStatus.COMPLETED)

    def to_source_dict(self) -> dict[str, str]:
        """Convert to dictionary of source texts."""
        return {e.key: e.source_text for e in self.entries}

    def to_translated_dict(self) -> dict[str, str]:
        """Convert to dictionary of translated texts."""
        return {
            e.key: e.translated_text
            for e in self.entries
            if e.translated_text is not None
        }


class TranslationTask(BaseModel):
    """A complete translation task for a language file."""

    file_pair: LanguageFilePair = Field(
        ...,
        description="Source and target file pair",
    )
    entries: dict[str, TranslationEntry] = Field(
        default_factory=dict,
        description="All translation entries keyed by translation key",
    )
    status: TranslationStatus = Field(
        default=TranslationStatus.PENDING,
        description="Overall task status",
    )
    error: str | None = Field(
        default=None,
        description="Error message if task failed",
    )

    @classmethod
    def from_source_data(
        cls,
        file_pair: LanguageFilePair,
        source_data: Mapping[str, str],
        existing_data: Mapping[str, str] | None = None,
    ) -> TranslationTask:
        """Create a translation task from source data.

        Args:
            file_pair: File pair information.
            source_data: Source language data.
            existing_data: Existing target language data (if any).

        Returns:
            New translation task.
        """
        entries: dict[str, TranslationEntry] = {}
        existing = existing_data or {}

        for key, source_text in source_data.items():
            if key in existing:
                # Already translated
                entries[key] = TranslationEntry(
                    key=key,
                    source_text=source_text,
                    translated_text=existing[key],
                    status=TranslationStatus.COMPLETED,
                )
            else:
                entries[key] = TranslationEntry(
                    key=key,
                    source_text=source_text,
                )

        return cls(file_pair=file_pair, entries=entries)

    @property
    def pending_entries(self) -> list[TranslationEntry]:
        """Get all pending translation entries."""
        return [
            e for e in self.entries.values() if e.status == TranslationStatus.PENDING
        ]

    @property
    def failed_entries(self) -> list[TranslationEntry]:
        """Get all failed translation entries."""
        return [
            e for e in self.entries.values() if e.status == TranslationStatus.FAILED
        ]

    @property
    def failed_count(self) -> int:
        """Count of failed translations."""
        return len(self.failed_entries)

    @property
    def completed_count(self) -> int:
        """Count of completed translations."""
        return sum(
            1 for e in self.entries.values() if e.status == TranslationStatus.COMPLETED
        )

    @property
    def progress(self) -> float:
        """Calculate translation progress (0.0 to 1.0)."""
        if not self.entries:
            return 1.0
        completed = sum(
            1 for e in self.entries.values() if e.status == TranslationStatus.COMPLETED
        )
        return completed / len(self.entries)

    def create_batches(
        self,
        max_entries: int = 50,
        max_chars: int | None = None,
    ) -> list[TranslationBatch]:
        """Split pending entries into batches.

        Batches are created based on character count limit first,
        then entry count limit as a fallback.

        Args:
            max_entries: Maximum entries per batch.
            max_chars: Maximum total characters per batch (key + source_text).
                      If None, only entry count is used.

        Returns:
            List of translation batches.
        """
        pending = self.pending_entries
        return self._create_batches_from_entries(pending, max_entries, max_chars)

    def create_retry_batches(
        self,
        max_entries: int = 50,
        max_chars: int | None = None,
    ) -> list[TranslationBatch]:
        """Split failed entries into batches for retry.

        Args:
            max_entries: Maximum entries per batch.
            max_chars: Maximum total characters per batch.

        Returns:
            List of translation batches.
        """
        failed = self.failed_entries
        return self._create_batches_from_entries(failed, max_entries, max_chars)

    def _create_batches_from_entries(
        self,
        entries: list[TranslationEntry],
        max_entries: int,
        max_chars: int | None,
    ) -> list[TranslationBatch]:
        """Create batches from a list of entries with size limits.

        Args:
            entries: List of entries to batch.
            max_entries: Maximum entries per batch.
            max_chars: Maximum characters per batch (None = no limit).

        Returns:
            List of translation batches.
        """
        if not entries:
            return []

        batches: list[TranslationBatch] = []

        # If no character limit, use simple entry count batching
        if max_chars is None:
            for i in range(0, len(entries), max_entries):
                batch_entries = entries[i : i + max_entries]
                batches.append(
                    TranslationBatch(
                        entries=batch_entries,
                        batch_id=len(batches),
                    )
                )
            return batches

        # Character-based batching
        current_batch: list[TranslationEntry] = []
        current_chars = 0

        for entry in entries:
            # Calculate entry size: key + source_text + some overhead for JSON
            entry_chars = len(entry.key) + len(entry.source_text) + 10

            # If single entry exceeds limit, put it in its own batch
            if entry_chars > max_chars:
                # Flush current batch first
                if current_batch:
                    batches.append(
                        TranslationBatch(
                            entries=current_batch,
                            batch_id=len(batches),
                        )
                    )
                    current_batch = []
                    current_chars = 0

                # Add oversized entry as its own batch
                batches.append(
                    TranslationBatch(
                        entries=[entry],
                        batch_id=len(batches),
                    )
                )
                continue

            # Check if adding this entry would exceed limits
            would_exceed_chars = current_chars + entry_chars > max_chars
            would_exceed_entries = len(current_batch) >= max_entries

            if would_exceed_chars or would_exceed_entries:
                if max_chars:
                    logger.info(
                        f"Batch cut due to limit. Current: {len(current_batch)} items, {current_chars} chars. "
                        f"Next item '{entry.key}' size: {entry_chars}. "
                        f"Limit: {max_entries} items, {max_chars} chars."
                    )
                
                # Flush current batch
                if current_batch:
                    batches.append(
                        TranslationBatch(
                            entries=current_batch,
                            batch_id=len(batches),
                        )
                    )
                current_batch = []
                current_chars = 0

            # Add entry to current batch
            current_batch.append(entry)
            current_chars += entry_chars

        # Don't forget the last batch
        if current_batch:
            batches.append(
                TranslationBatch(
                    entries=current_batch,
                    batch_id=len(batches),
                )
            )

        return batches

    def reset_failed_entries(self) -> int:
        """Reset all failed entries to pending status for retry.

        Returns:
            Number of entries reset.
        """
        count = 0
        for entry in self.entries.values():
            if entry.status == TranslationStatus.FAILED:
                entry.status = TranslationStatus.PENDING
                entry.previous_error = entry.error
                entry.error = None
                count += 1

        # Reset task status if all were failed
        if self.status == TranslationStatus.FAILED:
            self.status = TranslationStatus.PENDING
            self.error = None

        return count

    def to_output_dict(self) -> dict[str, str]:
        """Convert completed translations to output dictionary."""
        return {
            key: entry.translated_text
            for key, entry in self.entries.items()
            if entry.translated_text is not None
        }


class TranslationResult(BaseModel):
    """Result of a translation operation."""

    source_text: str = Field(
        ...,
        description="Original source text",
    )
    translated_text: str = Field(
        ...,
        description="Translated text",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Translation confidence score",
    )
    alternatives: list[str] = Field(
        default_factory=list,
        description="Alternative translations",
    )
