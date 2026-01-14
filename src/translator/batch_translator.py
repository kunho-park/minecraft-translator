"""Batch translator with glossary support and placeholder protection."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from src.llm import LLMClient
from src.models import (
    Glossary,
    TranslationBatch,
    TranslationEntry,
    TranslationStatus,
    TranslationTask,
)
from src.models.glossary_filter import GlossaryFilter
from src.utils import get_language_name

from .placeholder import PlaceholderError, PlaceholderProtector, ProtectedText

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Default limits for batching
DEFAULT_BATCH_SIZE = 30
DEFAULT_MAX_BATCH_CHARS = 8000  # ~2000 tokens for typical LLM


class TranslationOutput(BaseModel):
    """Output structure for batch translation."""

    translations: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of keys to translated texts",
    )


SYSTEM_PROMPT_TEMPLATE = """You are a Minecraft mod translation expert.
Translate {source_lang} text to {target_lang}.

## CRITICAL: Placeholder Protection Rules
1. **NEVER translate or modify placeholders marked with ⟦PH_xxx⟧**
2. **Copy placeholders EXACTLY as they appear** - including all characters between ⟦ and ⟧
3. **Do NOT abbreviate**: ⟦PH_0_java_format⟧ must stay as ⟦PH_0_java_format⟧, NOT ⟦PH...⟧
4. **Preserve placeholder position** in the translated text
5. **Example**: 
   - Input: "Kill the ⟦PH_0_named_placeholder⟧"
   - Output: "⟦PH_0_named_placeholder⟧을(를) 처치하세요"
   - WRONG: "⟦PH...⟧을(를) 처치하세요"

## Translation Rules
1. Translate game terminology consistently
2. Use natural {target_lang} expressions
{target_specific_rules}

{glossary_context}

## Output Format
Return translations as a JSON dictionary.
Keys must match input exactly, values should be translated {target_lang} text with **ALL placeholders preserved exactly**."""


class BatchTranslator:
    """Translator that processes texts in batches with glossary support.

    Uses placeholder protection to preserve format codes during translation.
    Batches are split based on both entry count and character limits.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        source_locale: str = "en_us",
        target_locale: str = "ko_kr",
        glossary: Glossary | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_batch_chars: int | None = DEFAULT_MAX_BATCH_CHARS,
        progress_callback: object | None = None,
    ) -> None:
        """Initialize the translator.

        Args:
            llm_client: LLM client for translation.
            source_locale: Source language locale code.
            target_locale: Target language locale code.
            glossary: Optional glossary for consistent translation.
            batch_size: Maximum entries per batch.
            max_batch_chars: Maximum characters per batch (None = no limit).
            progress_callback: Optional callback for progress updates.
        """
        self.llm_client = llm_client
        self.source_locale = source_locale
        self.target_locale = target_locale
        self.glossary = glossary
        self.batch_size = batch_size
        self.max_batch_chars = max_batch_chars
        self.protector = PlaceholderProtector()
        self.progress_callback = progress_callback

        logger.info(
            "Initialized BatchTranslator (%s -> %s) with batch_size=%d, max_chars=%s, glossary=%s",
            source_locale,
            target_locale,
            batch_size,
            max_batch_chars or "unlimited",
            "yes" if glossary else "no",
        )

    async def translate_task(self, task: TranslationTask) -> TranslationTask:
        """Translate all pending entries in a task.

        Args:
            task: Translation task with entries to translate.

        Returns:
            Updated task with translations.
        """
        logger.info(
            "Translating task: %s (%d pending)",
            task.file_pair.source_path,
            len(task.pending_entries),
        )

        task.status = TranslationStatus.IN_PROGRESS

        # Create batches with character limit
        batches = task.create_batches(
            max_entries=self.batch_size,
            max_chars=self.max_batch_chars,
        )
        logger.info(
            "Created %d batches (max %d entries, max %s chars)",
            len(batches),
            self.batch_size,
            self.max_batch_chars or "unlimited",
        )

        # Translate batches with progress tracking using queue
        total_batches = len(batches)
        completed_batches = 0
        # Store results with batch_id for ordering
        batch_results: dict[int, dict[str, str | Exception] | BaseException] = {}

        # Use queue-based worker pool for efficient concurrency
        queue: asyncio.Queue[TranslationBatch | None] = asyncio.Queue()

        # Put all batches into the queue
        for batch in batches:
            await queue.put(batch)

        # Worker function
        async def worker() -> None:
            nonlocal completed_batches
            while True:
                batch = await queue.get()
                if batch is None:
                    queue.task_done()
                    break
                try:
                    result = await self._translate_batch(batch)
                    batch_results[batch.batch_id] = result
                    completed_batches += 1

                    if self.progress_callback:
                        try:
                            self.progress_callback(
                                f"배치 번역 중... ({completed_batches}/{total_batches})",
                                completed_batches,
                                total_batches,
                                {
                                    "batch": completed_batches,
                                    "total_batches": total_batches,
                                },
                            )  # type: ignore[misc]
                        except Exception as e:
                            logger.warning("Progress callback failed: %s", e)
                except Exception as e:
                    batch_results[batch.batch_id] = e
                    logger.error("Batch translation failed: %s", e)
                finally:
                    queue.task_done()

        # Start workers (use LLM client's max_concurrent)
        num_workers = self.llm_client.config.max_concurrent
        workers = [asyncio.create_task(worker()) for _ in range(num_workers)]

        # Wait for all batches to be processed
        await queue.join()

        # Signal workers to stop
        for _ in range(num_workers):
            await queue.put(None)

        # Wait for workers to finish
        await asyncio.gather(*workers)

        # Update task entries with results (using batch_id for ordering)
        for batch in batches:
            result = batch_results.get(batch.batch_id)
            if isinstance(result, Exception):
                logger.error("Batch translation failed: %s", result)
                for entry in batch.entries:
                    entry.status = TranslationStatus.FAILED
                    entry.error = str(result)
            elif isinstance(result, dict):
                for entry in batch.entries:
                    if entry.key in result:
                        val = result[entry.key]
                        if isinstance(val, Exception):
                            entry.status = TranslationStatus.FAILED
                            entry.error = str(val)
                        else:
                            entry.translated_text = val
                            entry.status = TranslationStatus.COMPLETED
                    else:
                        entry.status = TranslationStatus.FAILED
                        entry.error = "Translation not found in response"

        # Update task status
        failed_count = sum(
            1 for e in task.entries.values() if e.status == TranslationStatus.FAILED
        )
        if failed_count == 0:
            task.status = TranslationStatus.COMPLETED
        elif failed_count == len(task.entries):
            task.status = TranslationStatus.FAILED
            task.error = "All translations failed"
        else:
            task.status = TranslationStatus.COMPLETED
            logger.warning("%d translations failed", failed_count)

        logger.info(
            "Task completed: %s (progress: %.1f%%)",
            task.file_pair.source_path,
            task.progress * 100,
        )

        return task

    async def translate_texts(
        self,
        texts: dict[str, str],
    ) -> dict[str, str]:
        """Translate a dictionary of texts.

        Args:
            texts: Dictionary of keys to source texts.

        Returns:
            Dictionary of keys to translated texts.
        """
        if not texts:
            return {}

        # Create task-like structure
        entries = [TranslationEntry(key=k, source_text=v) for k, v in texts.items()]

        # Split into batches
        results: dict[str, str] = {}

        for i in range(0, len(entries), self.batch_size):
            batch_entries = entries[i : i + self.batch_size]
            batch = TranslationBatch(
                entries=batch_entries, batch_id=i // self.batch_size
            )

            batch_result = await self._translate_batch(batch)
            results.update(batch_result)

        return results

    async def _translate_batch(
        self,
        batch: TranslationBatch,
    ) -> dict[str, str | Exception]:
        """Translate a single batch.

        Args:
            batch: Batch of translation entries.

        Returns:
            Dictionary of keys to translated texts (or Exceptions).
        """
        logger.debug(
            "Translating batch %d (%d entries)", batch.batch_id, len(batch.entries)
        )

        # Protect placeholders and filter placeholder-only texts
        protected_texts: dict[str, ProtectedText] = {}
        original_texts: dict[str, str] = {}
        placeholder_only: dict[str, str] = {}

        for entry in batch.entries:
            protected = self.protector.protect(entry.source_text)

            # Check if text contains only placeholders
            if self.protector.is_only_placeholders(protected):
                logger.debug(
                    "Skipping placeholder-only text for key %s: %s",
                    entry.key,
                    entry.source_text[:100],
                )
                placeholder_only[entry.key] = entry.source_text
                continue

            protected_texts[entry.key] = protected
            original_texts[entry.key] = entry.source_text

        # If all texts are placeholder-only, return them as-is
        if not protected_texts:
            if batch.batch_id > 0:
                logger.info(
                    "All texts in batch %d are placeholder-only, skipping translation",
                    batch.batch_id,
                )
            return placeholder_only

        # Build prompt
        texts_for_llm = {key: pt.protected for key, pt in protected_texts.items()}

        prompt = self._build_translation_prompt(texts_for_llm)
        
        # Collect errors from previous attempts
        entry_errors = {
            entry.key: entry.previous_error
            for entry in batch.entries
            if entry.previous_error
        }

        # Pass original texts (not protected) for glossary filtering and errors for context
        system_prompt = self._build_system_prompt(
            texts=original_texts, errors=entry_errors
        )

        try:
            result = await self.llm_client.structured_output(
                prompt=prompt,
                output_schema=TranslationOutput,
                system_prompt=system_prompt,
            )

            # Restore placeholders
            translations: dict[str, str | Exception] = {}
            for key, translated in result.translations.items():
                try:
                    if key in protected_texts:
                        translations[key] = protected_texts[key].restore(translated)
                    else:
                        translations[key] = translated
                except PlaceholderError as e:
                    logger.warning(
                        "Placeholder error for key '%s': %s. Marking as failed for retry.",
                        key,
                        e,
                    )
                    translations[key] = e

            # Add placeholder-only texts (unchanged)
            translations.update(placeholder_only)

            return translations

        except Exception as e:
            logger.error("Batch %d translation failed: %s", batch.batch_id, e)
            raise

    def _build_translation_prompt(self, texts: dict[str, str]) -> str:
        """Build the translation prompt.

        Args:
            texts: Dictionary of keys to source texts.

        Returns:
            Formatted prompt string.
        """
        target_lang = get_language_name(self.target_locale, "native")

        lines = [f"Translate the following texts to {target_lang}:", ""]

        for key, text in texts.items():
            lines.append(f'"{key}": "{text}"')

        lines.append("")
        lines.append(f"Return translated {target_lang} text as JSON for each key.")

        return "\n".join(lines)

    def _build_system_prompt(
        self,
        texts: dict[str, str] | None = None,
        errors: dict[str, str] | None = None,
    ) -> str:
        """Build the system prompt with filtered glossary context.

        Args:
            texts: Optional texts to filter glossary against
            errors: Optional dictionary of previous errors {key: error_message}

        Returns:
            System prompt string.
        """
        source_lang = get_language_name(self.source_locale, "en")
        target_lang = get_language_name(self.target_locale, "en")

        # Language-specific rules (currently only for Korean)
        target_specific_rules = ""
        if self.target_locale.startswith("ko"):
            target_specific_rules = "4. For Korean: use appropriate particles (이/가, 을/를) based on final consonant"
        elif self.target_locale.startswith("ja"):
            target_specific_rules = "4. For Japanese: use appropriate particles (は/が, を/に) and polite forms"

        glossary_context = ""
        if self.glossary:
            # Filter glossary to only relevant terms if texts provided
            if texts:
                filtered_glossary = GlossaryFilter.filter_for_texts(
                    self.glossary, texts
                )
                if filtered_glossary.has_rules:
                    glossary_context = f"""
## Glossary (Filtered for this batch)
{filtered_glossary.to_context_string()}
"""
            else:
                # Fallback to full glossary
                glossary_context = f"""
## Glossary
{self.glossary.to_context_string()}
"""

        # Add previous errors context if available
        if errors:
            error_context = "\n## Previous Translation Errors (Please Fix)\n"
            for key, error in errors.items():
                error_context += f"- Key '{key}': {error}\n"
            glossary_context += error_context

        return SYSTEM_PROMPT_TEMPLATE.format(
            source_lang=source_lang,
            target_lang=target_lang,
            target_specific_rules=target_specific_rules,
            glossary_context=glossary_context,
        )

    def update_glossary(self, glossary: Glossary) -> None:
        """Update the translation glossary.

        Args:
            glossary: New glossary to use.
        """
        self.glossary = glossary
        logger.info("Updated translator glossary")
