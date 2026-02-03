"""LLM-based reviewer for translation quality."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from ..llm import LLMClient
from ..models import Glossary, ReviewIssue, ReviewResult
from ..models.glossary_filter import GlossaryFilter
from ..prompts import build_reviewer_system_prompt, build_reviewer_user_prompt
from ..utils import get_language_name

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

# Maximum entries per review request
MAX_ENTRIES_PER_REQUEST = 50


class ReviewOutput(BaseModel):
    """Output structure for review."""

    issues: list[ReviewIssue] = Field(
        default_factory=list,
        description="List of issues found",
    )


# System prompt is now dynamically generated


class LLMReviewer:
    """LLM-based reviewer for translation quality.

    Reviews translations for:
    - Mistranslations
    - Typos and spelling errors
    - Unnatural expressions
    - Language-specific issues
    - Terminology inconsistencies
    """

    def __init__(
        self,
        llm_client: LLMClient,
        source_locale: str = "en_us",
        target_locale: str = "ko_kr",
        glossary: Glossary | None = None,
        progress_callback: object | None = None,
    ) -> None:
        """Initialize the reviewer.

        Args:
            llm_client: LLM client for review requests.
            source_locale: Source language locale code.
            target_locale: Target language locale code.
            glossary: Optional glossary for consistency checking.
            progress_callback: Optional callback for progress updates.
        """
        self.llm_client = llm_client
        self.source_locale = source_locale
        self.target_locale = target_locale
        self.glossary = glossary
        self.progress_callback = progress_callback
        logger.info(
            "Initialized LLMReviewer (%s -> %s)",
            source_locale,
            target_locale,
        )

    async def review(
        self,
        source_data: Mapping[str, str],
        translated_data: Mapping[str, str],
    ) -> ReviewResult:
        """Review translations for quality issues.

        Args:
            source_data: Original source language data.
            translated_data: Translated data to review.

        Returns:
            Review result with found issues.
        """
        logger.info(
            "Reviewing %d translations",
            len(translated_data),
        )

        # Create pairs for review
        pairs: list[tuple[str, str, str]] = []  # (key, source, translated)

        for key, translated in translated_data.items():
            if key in source_data:
                pairs.append((key, source_data[key], translated))

        if not pairs:
            return ReviewResult(reviewed_count=0)

        # Split into batches
        batches = [
            pairs[i : i + MAX_ENTRIES_PER_REQUEST]
            for i in range(0, len(pairs), MAX_ENTRIES_PER_REQUEST)
        ]

        total_batches = len(batches)
        completed_batches = 0
        results: list[list[ReviewIssue] | BaseException] = []

        # Use queue-based worker pool for efficient concurrency
        queue: asyncio.Queue[list[tuple[str, str, str]] | None] = asyncio.Queue()

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
                    result = await self._review_batch(batch)
                    results.append(result)
                    completed_batches += 1

                    if self.progress_callback:
                        try:
                            self.progress_callback(
                                f"리뷰 중... ({completed_batches}/{total_batches} 배치)",
                                completed_batches,
                                total_batches,
                                {},
                            )  # type: ignore[misc]
                        except Exception as e:
                            logger.warning("Progress callback failed: %s", e)
                except Exception as e:
                    results.append(e)
                    logger.warning("Review batch failed: %s", e)
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

        # Combine results
        all_issues: list[ReviewIssue] = []

        for result in results:
            if isinstance(result, list):
                all_issues.extend(result)
            elif isinstance(result, Exception):
                logger.warning("Review batch failed: %s", result)

        review_result = ReviewResult(
            reviewed_count=len(pairs),
            issues_found=all_issues,
            corrections_applied=0,
        )

        logger.info(
            "Review complete: %d issues found",
            len(all_issues),
        )

        return review_result

    async def _review_batch(
        self,
        pairs: list[tuple[str, str, str]],
    ) -> list[ReviewIssue]:
        """Review a batch of translations.

        Args:
            pairs: List of (key, source, translated) tuples.

        Returns:
            List of issues found.
        """
        prompt = self._build_review_prompt(pairs)

        # Collect texts for glossary filtering (source + translated)
        texts_for_filter = {
            key: f"{source} {translated}" for key, source, translated in pairs
        }

        try:
            result = await self.llm_client.structured_output(
                prompt=prompt,
                output_schema=ReviewOutput,
                system_prompt=self._build_system_prompt(texts=texts_for_filter),
            )
            return result.issues
        except Exception as e:
            logger.error("Batch review failed: %s", e)
            return []

    def _build_review_prompt(
        self,
        pairs: list[tuple[str, str, str]],
    ) -> str:
        """Build the review prompt.

        Args:
            pairs: List of (key, source, translated) tuples.

        Returns:
            Formatted prompt string.
        """
        source_lang = get_language_name(self.source_locale, "en")
        target_lang = get_language_name(self.target_locale, "en")

        return build_reviewer_user_prompt(pairs, source_lang, target_lang)

    def _build_system_prompt(self, texts: dict[str, str] | None = None) -> str:
        """Build the system prompt with filtered glossary context.

        Args:
            texts: Optional texts to filter glossary against.

        Returns:
            System prompt string.
        """
        source_lang = get_language_name(self.source_locale, "en")
        target_lang = get_language_name(self.target_locale, "en")

        glossary_context = ""
        if self.glossary:
            # Filter glossary to only relevant terms if texts provided
            if texts:
                filtered_glossary = GlossaryFilter.filter_for_texts(
                    self.glossary, texts
                )
                if filtered_glossary.has_rules:
                    glossary_context = f"""
## Reference Glossary (Filtered for this batch)
{filtered_glossary.to_context_string()}
"""
            else:
                # Fallback to full glossary (shouldn't happen normally)
                glossary_context = f"""
## Reference Glossary
{self.glossary.to_context_string()}
"""

        return build_reviewer_system_prompt(
            source_lang=source_lang,
            target_lang=target_lang,
            target_locale=self.target_locale,
            glossary_context=glossary_context,
        )

    def apply_corrections(
        self,
        translated_data: dict[str, str],
        review_result: ReviewResult,
    ) -> dict[str, str]:
        """Apply corrections from review to translated data.

        Args:
            translated_data: Original translated data.
            review_result: Review result with corrections.

        Returns:
            Corrected translated data.
        """
        corrected = dict(translated_data)
        corrections = review_result.get_corrections_dict()

        for key, corrected_text in corrections.items():
            if key in corrected:
                logger.debug("Applying correction for: %s", key)
                corrected[key] = corrected_text

        review_result.corrections_applied = len(corrections)
        logger.info("Applied %d corrections", len(corrections))

        return corrected

    async def review_and_correct(
        self,
        source_data: Mapping[str, str],
        translated_data: dict[str, str],
    ) -> tuple[dict[str, str], ReviewResult]:
        """Review translations and apply corrections.

        Args:
            source_data: Original source data.
            translated_data: Translated data to review.

        Returns:
            Tuple of (corrected data, review result).
        """
        review_result = await self.review(source_data, translated_data)

        if review_result.has_issues:
            corrected_data = self.apply_corrections(translated_data, review_result)
            return corrected_data, review_result

        return translated_data, review_result

    def update_glossary(self, glossary: Glossary) -> None:
        """Update the glossary for consistency checking.

        Args:
            glossary: New glossary to use.
        """
        self.glossary = glossary
        logger.info("Updated reviewer glossary")
