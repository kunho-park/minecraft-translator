"""Glossary builder using LLM for term extraction."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from ..llm import LLMClient
from ..models import (
    FormattingRule,
    Glossary,
    LanguageFilePair,
    ProperNounRule,
    TermRule,
)
from ..parsers import BaseParser
from ..utils import get_language_name

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

logger = logging.getLogger(__name__)

# Maximum entries per LLM request for glossary extraction
MAX_ENTRIES_PER_REQUEST = 100
# Maximum characters per batch to avoid token limits
MAX_CHARS_PER_BATCH = 50000


class GlossaryExtractionResult(BaseModel):
    """Result from LLM glossary extraction."""

    term_rules: list[TermRule] = Field(default_factory=list)
    proper_noun_rules: list[ProperNounRule] = Field(default_factory=list)
    formatting_rules: list[FormattingRule] = Field(default_factory=list)


# System prompts are now dynamically generated based on source/target locales


class GlossaryBuilder:
    """Builder for creating translation glossaries using LLM.

    Supports two modes:
    1. Paired extraction: Analyze source/target pairs to extract existing patterns
    2. Source-only extraction: Analyze source text to suggest translations
    """

    def __init__(
        self,
        llm_client: LLMClient,
        source_locale: str = "en_us",
        target_locale: str = "ko_kr",
        progress_callback: object | None = None,
    ) -> None:
        """Initialize the glossary builder.

        Args:
            llm_client: LLM client for extraction requests.
            source_locale: Source language locale code.
            target_locale: Target language locale code.
            progress_callback: Optional callback for progress updates.
        """
        self.llm_client = llm_client
        self.source_locale = source_locale
        self.target_locale = target_locale
        self.progress_callback = progress_callback

        # Load vanilla glossary if available
        self.vanilla_glossary = self._load_vanilla_glossary()

        # Store modpack-only glossary separately (without vanilla)
        self.modpack_only_glossary: Glossary | None = None

        logger.info(
            "Initialized GlossaryBuilder (%s -> %s)",
            source_locale,
            target_locale,
        )
        if self.vanilla_glossary:
            logger.info(
                "Loaded vanilla glossary with %d terms",
                len(self.vanilla_glossary.term_rules),
            )

    def _load_vanilla_glossary(self) -> Glossary | None:
        """Load vanilla Minecraft glossary for current language pair.

        Returns:
            Vanilla glossary or None if not found
        """
        from pathlib import Path

        # Build filename for current language pair
        filename = f"vanilla_glossary_{self.source_locale}_{self.target_locale}.json"

        # Try multiple locations
        possible_paths = [
            Path("src/glossary/vanilla_glossaries") / filename,
            Path(__file__).parent / "vanilla_glossaries" / filename,
        ]

        for glossary_path in possible_paths:
            if glossary_path.exists():
                try:
                    import json

                    with open(glossary_path, encoding="utf-8") as f:
                        data = json.load(f)

                    from ..models import FormattingRule, ProperNounRule, TermRule

                    glossary = Glossary(
                        term_rules=[
                            TermRule(**term) for term in data.get("term_rules", [])
                        ],
                        proper_noun_rules=[
                            ProperNounRule(**noun)
                            for noun in data.get("proper_noun_rules", [])
                        ],
                        formatting_rules=[
                            FormattingRule(**rule)
                            for rule in data.get("formatting_rules", [])
                        ],
                    )
                    logger.info(
                        "Loaded vanilla glossary from: %s (%s → %s)",
                        glossary_path,
                        self.source_locale,
                        self.target_locale,
                    )
                    return glossary
                except Exception as e:
                    logger.warning("Failed to load vanilla glossary: %s", e)

        logger.info(
            "No vanilla glossary found for %s → %s (looked for: %s)",
            self.source_locale,
            self.target_locale,
            filename,
        )
        return None

    def _build_paired_prompt(self) -> str:
        """Build system prompt for paired extraction."""
        source_lang = get_language_name(self.source_locale, "en")
        target_lang = get_language_name(self.target_locale, "en")

        return f"""You are a Minecraft mod translation expert.
Analyze the given {source_lang}-{target_lang} translation corpus to extract rules for consistent translation.

Output the following rules in JSON format:

1. **term_rules** (Terminology): Common game terms and their translation style
   - term_ko: {target_lang} term (e.g., for items/blocks)
   - preferred_style: Style description
   - aliases: List of {source_lang} source terms
   - category: item/block/ui/entity/effect/biome/other
   - notes: Additional notes

2. **proper_noun_rules** (Proper Nouns): Consistent translations of proper nouns
   - source_like: Original {source_lang} form (e.g., "Nether", "Ender")
   - preferred_ko: Preferred {target_lang} form
   - notes: Translation reasoning

3. **formatting_rules** (Formatting): Style guide
   - rule_name: Rule name
   - description: Rule description
   - examples: Example list"""

    def _build_source_only_prompt(self) -> str:
        """Build system prompt for source-only extraction."""
        source_lang = get_language_name(self.source_locale, "en")
        target_lang = get_language_name(self.target_locale, "en")

        # Language-specific guidance
        lang_specific = ""
        if self.target_locale.startswith("ko"):
            lang_specific = """
Reference official Minecraft Korean translation style:
- Follow official translations for items/blocks
- Preserve placeholders (%s, %d, etc.)
- Preserve color codes (§, &)
- Handle particles correctly: 이(가), 을(를)"""

        return f"""You are a Minecraft mod translation expert.
Analyze the given {source_lang} text to propose rules for consistent {target_lang} translation.

Output the following rules in JSON format:

1. **term_rules** (Terminology): Identified game terms and recommended translations
   - term_ko: Recommended {target_lang} translation
   - preferred_style: Translation style description
   - aliases: List of {source_lang} source terms
   - category: item/block/ui/entity/effect/biome/other
   - notes: Translation reasoning

2. **proper_noun_rules** (Proper Nouns): Identified proper nouns and recommended translations
   - source_like: {source_lang} proper noun
   - preferred_ko: Recommended {target_lang} form (transliteration or translation)
   - notes: Translation reasoning

3. **formatting_rules** (Formatting): Style guide to apply during translation
   - rule_name: Rule name
   - description: Rule description
   - examples: Example list
{lang_specific}"""

    async def build_from_pairs(
        self,
        file_pairs: Sequence[LanguageFilePair],
    ) -> Glossary:
        """Build glossary from EN/KO file pairs.

        Args:
            file_pairs: List of language file pairs.

        Returns:
            Combined glossary from all pairs.
        """
        logger.info("Building glossary from %d file pairs", len(file_pairs))

        # Separate paired and source-only files
        paired = [p for p in file_pairs if p.has_existing_translation]
        source_only = [p for p in file_pairs if not p.has_existing_translation]

        logger.info(
            "Found %d paired files, %d source-only files",
            len(paired),
            len(source_only),
        )

        # Process in parallel
        tasks: list[asyncio.Task[Glossary]] = []

        if paired:
            tasks.append(asyncio.create_task(self._extract_from_paired_files(paired)))

        if source_only:
            tasks.append(
                asyncio.create_task(self._extract_from_source_only_files(source_only))
            )

        if not tasks:
            logger.warning("No files to process for glossary")
            return Glossary()

        results = await asyncio.gather(*tasks)

        # Build modpack-only glossary (without vanilla)
        modpack_glossary = Glossary()
        for glossary in results:
            modpack_glossary = modpack_glossary.merge_with(glossary)

        # Store modpack-only glossary for saving
        self.modpack_only_glossary = modpack_glossary

        logger.info(
            "Built modpack-only glossary with %d terms, %d proper nouns, %d formatting rules",
            len(modpack_glossary.term_rules),
            len(modpack_glossary.proper_noun_rules),
            len(modpack_glossary.formatting_rules),
        )

        # Merge with vanilla glossary for translation use
        if self.vanilla_glossary:
            final_glossary = self.vanilla_glossary.merge_with(modpack_glossary)
            logger.info(
                "Merged with vanilla glossary: %d total terms",
                len(final_glossary.term_rules),
            )
        else:
            final_glossary = modpack_glossary

        return final_glossary

    def _get_token_stats(self) -> dict[str, int]:
        """Get current token usage statistics from LLM client.

        Returns:
            Dictionary with input_tokens, output_tokens, total_tokens
        """
        return self.llm_client.get_token_usage()

    async def _extract_from_paired_files(
        self,
        file_pairs: Sequence[LanguageFilePair],
    ) -> Glossary:
        """Extract glossary from paired EN/KO files.

        Args:
            file_pairs: File pairs with existing translations.

        Returns:
            Extracted glossary.
        """
        logger.info("Extracting from %d paired files", len(file_pairs))

        # Load all data
        all_pairs: list[tuple[str, str]] = []

        for pair in file_pairs:
            try:
                source_data = await self._load_file(pair.source_path)
                target_data = (
                    await self._load_file(pair.target_path) if pair.target_path else {}
                )

                # Match keys
                for key, source_text in source_data.items():
                    if key in target_data:
                        all_pairs.append((source_text, target_data[key]))
            except Exception as e:
                logger.warning("Failed to load pair %s: %s", pair.source_path, e)

        if not all_pairs:
            return Glossary()

        # Split into batches considering both entry count and character count
        batches = self._create_smart_batches(all_pairs)

        logger.info("Created %d batches from %d pairs", len(batches), len(all_pairs))

        total_batches = len(batches)
        completed_batches = 0
        results: list[Glossary | BaseException] = []

        # Use queue-based worker pool for efficient concurrency
        queue: asyncio.Queue[list[tuple[str, str]] | None] = asyncio.Queue()

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
                    result = await self._extract_from_paired_batch(batch)
                    results.append(result)
                    completed_batches += 1

                    if self.progress_callback:
                        try:
                            stats = self._get_token_stats()
                            self.progress_callback(
                                f"영어/한국어 쌍 데이터에서 용어집 추출 중... ({completed_batches}/{total_batches} 배치)",
                                completed_batches,
                                total_batches,
                                stats,
                            )  # type: ignore[misc]
                        except Exception as e:
                            logger.warning("Progress callback failed: %s", e)
                except Exception as e:
                    results.append(e)
                    logger.warning("Batch extraction failed: %s", e)
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

        # Merge results
        glossary = Glossary()
        for result in results:
            if isinstance(result, Glossary):
                glossary = glossary.merge_with(result)
            elif isinstance(result, Exception):
                logger.warning("Batch extraction failed: %s", result)

        return glossary

    def _create_smart_batches(
        self,
        pairs: Sequence[tuple[str, str]],
    ) -> list[list[tuple[str, str]]]:
        """Create batches considering both entry count and character count.

        Args:
            pairs: List of (source, target) text pairs.

        Returns:
            List of batches, each batch is a list of pairs.
        """
        batches: list[list[tuple[str, str]]] = []
        current_batch: list[tuple[str, str]] = []
        current_chars = 0

        for pair in pairs:
            # Estimate characters in this pair (source + target + formatting)
            pair_chars = len(pair[0]) + len(pair[1]) + 10  # +10 for "EN: \nKO: \n---\n"

            # Check if adding this pair would exceed limits
            would_exceed_entries = len(current_batch) >= MAX_ENTRIES_PER_REQUEST
            would_exceed_chars = current_chars + pair_chars > MAX_CHARS_PER_BATCH

            if current_batch and (would_exceed_entries or would_exceed_chars):
                # Start new batch
                batches.append(current_batch)
                current_batch = [pair]
                current_chars = pair_chars
            else:
                # Add to current batch
                current_batch.append(pair)
                current_chars += pair_chars

        # Add final batch
        if current_batch:
            batches.append(current_batch)

        return batches

    async def _extract_from_paired_batch(
        self,
        pairs: Sequence[tuple[str, str]],
        max_retries: int = 2,
    ) -> Glossary:
        """Extract glossary from a batch of EN/KO pairs.

        Args:
            pairs: List of (english, korean) text pairs.
            max_retries: Maximum number of retry attempts.

        Returns:
            Extracted glossary.
        """
        # Format pairs for LLM
        corpus_lines = [f"EN: {en}\nKO: {ko}" for en, ko in pairs]
        corpus_text = "\n---\n".join(corpus_lines)

        prompt = f"""다음 번역 코퍼스를 분석하세요:

{corpus_text}

위 코퍼스에서 용어 규칙, 고유명사 규칙, 포맷팅 규칙을 추출하세요."""

        for attempt in range(max_retries + 1):
            try:
                result = await self.llm_client.structured_output(
                    prompt=prompt,
                    output_schema=GlossaryExtractionResult,
                    system_prompt=self._build_paired_prompt(),
                )

                return Glossary(
                    term_rules=result.term_rules,
                    proper_noun_rules=result.proper_noun_rules,
                    formatting_rules=result.formatting_rules,
                )
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(
                        "Failed to extract from paired batch (attempt %d/%d): %s. Retrying...",
                        attempt + 1,
                        max_retries + 1,
                        str(e)[:200],
                    )
                    await asyncio.sleep(1)
                else:
                    logger.error(
                        "Failed to extract from paired batch after %d attempts: %s",
                        max_retries + 1,
                        str(e)[:200],
                    )

        return Glossary()

    async def _extract_from_source_only_files(
        self,
        file_pairs: Sequence[LanguageFilePair],
    ) -> Glossary:
        """Extract glossary from source-only files.

        Args:
            file_pairs: File pairs without existing translations.

        Returns:
            Suggested glossary.
        """
        logger.info("Extracting from %d source-only files", len(file_pairs))

        # Load all source data
        all_texts: list[str] = []

        for pair in file_pairs:
            try:
                source_data = await self._load_file(pair.source_path)
                all_texts.extend(source_data.values())
            except Exception as e:
                logger.warning("Failed to load %s: %s", pair.source_path, e)

        if not all_texts:
            return Glossary()

        # Split into batches considering character count
        batches = self._create_smart_text_batches(all_texts)

        logger.info("Created %d batches from %d texts", len(batches), len(all_texts))

        total_batches = len(batches)
        completed_batches = 0
        results: list[Glossary | BaseException] = []

        # Use queue-based worker pool for efficient concurrency
        queue: asyncio.Queue[list[str] | None] = asyncio.Queue()

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
                    result = await self._extract_from_english_batch(batch)
                    results.append(result)
                    completed_batches += 1

                    if self.progress_callback:
                        try:
                            stats = self._get_token_stats()
                            self.progress_callback(
                                f"영어에서 용어집 추출 중... ({completed_batches}/{total_batches} 배치)",
                                completed_batches,
                                total_batches,
                                stats,
                            )  # type: ignore[misc]
                        except Exception as e:
                            logger.warning("Progress callback failed: %s", e)
                except Exception as e:
                    results.append(e)
                    logger.warning("Batch extraction failed: %s", e)
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

        # Merge results
        glossary = Glossary()
        for result in results:
            if isinstance(result, Glossary):
                glossary = glossary.merge_with(result)
            elif isinstance(result, Exception):
                logger.warning("Batch extraction failed: %s", result)

        return glossary

    def _create_smart_text_batches(
        self,
        texts: Sequence[str],
    ) -> list[list[str]]:
        """Create text batches considering both entry count and character count.

        Args:
            texts: List of text strings.

        Returns:
            List of batches, each batch is a list of texts.
        """
        batches: list[list[str]] = []
        current_batch: list[str] = []
        current_chars = 0

        for text in texts:
            text_chars = len(text) + 5  # +5 for formatting

            # Check if adding this text would exceed limits
            would_exceed_entries = len(current_batch) >= MAX_ENTRIES_PER_REQUEST
            would_exceed_chars = current_chars + text_chars > MAX_CHARS_PER_BATCH

            if current_batch and (would_exceed_entries or would_exceed_chars):
                # Start new batch
                batches.append(current_batch)
                current_batch = [text]
                current_chars = text_chars
            else:
                # Add to current batch
                current_batch.append(text)
                current_chars += text_chars

        # Add final batch
        if current_batch:
            batches.append(current_batch)

        return batches

    async def _extract_from_english_batch(
        self,
        texts: Sequence[str],
        max_retries: int = 2,
    ) -> Glossary:
        """Extract glossary suggestions from English texts.

        Args:
            texts: List of English texts to analyze.
            max_retries: Maximum number of retry attempts.

        Returns:
            Suggested glossary.
        """
        # Format texts for LLM
        texts_formatted = "\n---\n".join(texts)

        prompt = f"""다음 영어 텍스트를 분석하세요:

{texts_formatted}

위 텍스트에서 마인크래프트 게임 용어, 고유명사를 식별하고,
한국어 번역 시 일관성을 위한 규칙을 제안하세요."""

        for attempt in range(max_retries + 1):
            try:
                result = await self.llm_client.structured_output(
                    prompt=prompt,
                    output_schema=GlossaryExtractionResult,
                    system_prompt=self._build_source_only_prompt(),
                )

                return Glossary(
                    term_rules=result.term_rules,
                    proper_noun_rules=result.proper_noun_rules,
                    formatting_rules=result.formatting_rules,
                )
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(
                        "Failed to extract from English batch (attempt %d/%d): %s. Retrying...",
                        attempt + 1,
                        max_retries + 1,
                        str(e)[:200],  # Truncate long error messages
                    )
                    await asyncio.sleep(1)  # Brief delay before retry
                else:
                    logger.error(
                        "Failed to extract from English batch after %d attempts: %s",
                        max_retries + 1,
                        str(e)[:200],
                    )

        return Glossary()

    async def _load_file(self, path: str | None) -> Mapping[str, str]:
        """Load a language file using the appropriate parser.

        Args:
            path: Path to the file.

        Returns:
            Mapping of keys to values.
        """
        if path is None:
            return {}

        from pathlib import Path as PathLib

        file_path = PathLib(path)

        parser = BaseParser.create_parser(file_path)
        if parser is None:
            logger.debug("No parser for: %s", path)
            return {}

        return await parser.parse()

    async def save_glossary(
        self,
        glossary: Glossary,
        output_path: str,
    ) -> None:
        """Save glossary to a JSON file.

        Args:
            glossary: Glossary to save.
            output_path: Output file path.
        """
        from pathlib import Path as PathLib

        import aiofiles

        path = PathLib(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(glossary.model_dump_json(indent=2))

        logger.info("Saved glossary to: %s", output_path)

    @staticmethod
    async def load_glossary(input_path: str) -> Glossary:
        """Load glossary from a JSON file.

        Args:
            input_path: Input file path.

        Returns:
            Loaded glossary.
        """
        import aiofiles

        async with aiofiles.open(input_path, encoding="utf-8") as f:
            content = await f.read()

        data = json.loads(content)
        return Glossary.model_validate(data)
