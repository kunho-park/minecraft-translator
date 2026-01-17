"""Main translation pipeline orchestrator."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .glossary import GlossaryBuilder
from .handlers.base import create_default_registry
from .llm import LLMClient, LLMConfig, LLMProvider
from .models import Glossary, TranslationStatus, TranslationTask
from .output import GenerationResult, ResourcePackConfig, generate_outputs
from .reviewer import LLMReviewer
from .scanner import ModpackScanner, ScanResult
from .translator import BatchTranslator
from .validator import TranslationValidator

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the translation pipeline."""

    # Language settings
    source_locale: str = "en_us"
    target_locale: str = "ko_kr"

    # LLM settings
    llm_provider: LLMProvider = LLMProvider.OLLAMA
    llm_model: str = "qwen2.5:14b"
    llm_temperature: float = 0.1
    llm_base_url: str | None = None
    llm_api_key: str | None = None

    # Concurrency settings
    max_concurrent: int = 15
    batch_size: int = 30
    max_batch_chars: int | None = 8000  # Max characters per batch (None = no limit)
    requests_per_minute: int | None = None  # RPM rate limit (None = no limit)
    tokens_per_minute: int | None = (
        None  # TPM rate limit (None = no limit, e.g. 4_000_000)
    )

    # Output settings
    pack_format: int = 15
    pack_name: str = "translations"
    create_zip: bool = True

    # Pipeline options
    skip_glossary: bool = False
    skip_review: bool = False
    save_glossary: bool = True


@dataclass
class PipelineResult:
    """Result of running the translation pipeline."""

    scan_result: ScanResult | None = None
    glossary: Glossary | None = None
    tasks: list[TranslationTask] = field(default_factory=list)
    generation_result: GenerationResult | None = None

    # Statistics
    total_entries: int = 0
    translated_entries: int = 0
    failed_entries: int = 0
    reviewed_entries: int = 0
    file_count: int = 0

    # Handler statistics: {"kubejs": 5, "ftbquests": 10, ...}
    handler_stats: dict[str, int] = field(default_factory=dict)

    # Token usage
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0

    # Timing
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def duration_seconds(self) -> float:
        """Get pipeline duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def success_rate(self) -> float:
        """Calculate translation success rate."""
        if self.total_entries == 0:
            return 1.0
        return self.translated_entries / self.total_entries

    @property
    def has_failures(self) -> bool:
        """Check if there are any failed translations."""
        return self.failed_entries > 0

    def get_failed_summary(self) -> dict[str, int]:
        """Get summary of failed translations per file.

        Returns:
            Dictionary mapping file paths to failure counts.
        """
        summary: dict[str, int] = {}
        for task in self.tasks:
            failed_count = task.failed_count
            if failed_count > 0:
                summary[str(task.file_pair.source_path)] = failed_count
        return summary

    def get_failed_file_pairs(self) -> list[object]:
        """Get list of file pairs that have failed translations.

        Returns:
            List of LanguageFilePair objects with failures.
        """
        failed_pairs = []
        for task in self.tasks:
            if task.failed_count > 0:
                failed_pairs.append(task.file_pair)
        return failed_pairs

    def update_statistics(self) -> None:
        """Recalculate statistics from tasks."""
        self.total_entries = 0
        self.translated_entries = 0
        self.failed_entries = 0

        for task in self.tasks:
            self.total_entries += len(task.entries)
            self.translated_entries += sum(
                1
                for e in task.entries.values()
                if e.status == TranslationStatus.COMPLETED
            )
            self.failed_entries += task.failed_count


class TranslationPipeline:
    """Main orchestrator for the translation pipeline.

    Coordinates all components to translate a Minecraft modpack:
    1. Scan modpack for language files
    2. Build glossary from existing translations (or generate suggestions)
    3. Translate pending entries in batches
    4. Validate translations
    5. Review and correct with LLM
    6. Generate output files (resource pack + overrides)
    """

    def __init__(
        self,
        config: PipelineConfig | None = None,
        progress_callback: object | None = None,
    ) -> None:
        """Initialize the pipeline.

        Args:
            config: Pipeline configuration.
            progress_callback: Optional callback(message, current, total, stats).
        """
        self.config = config or PipelineConfig()
        self.progress_callback = progress_callback

        # Initialize LLM client with token tracking
        llm_config = LLMConfig(
            provider=self.config.llm_provider,
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            base_url=self.config.llm_base_url,
            api_key=self.config.llm_api_key,
            max_concurrent=self.config.max_concurrent,
            requests_per_minute=self.config.requests_per_minute,
            tokens_per_minute=self.config.tokens_per_minute,
        )
        self.llm_client = LLMClient(
            llm_config, token_usage_callback=self._on_token_usage
        )

        # Initialize components
        self.scanner = ModpackScanner(
            self.config.source_locale,
            self.config.target_locale,
        )
        self.glossary_builder = GlossaryBuilder(
            self.llm_client,
            self.config.source_locale,
            self.config.target_locale,
            progress_callback=self.progress_callback,
        )
        self.translator = BatchTranslator(
            self.llm_client,
            source_locale=self.config.source_locale,
            target_locale=self.config.target_locale,
            batch_size=self.config.batch_size,
            max_batch_chars=self.config.max_batch_chars,
            progress_callback=self.progress_callback,
        )
        self.validator = TranslationValidator()
        self.reviewer = LLMReviewer(
            self.llm_client,
            source_locale=self.config.source_locale,
            target_locale=self.config.target_locale,
            progress_callback=self.progress_callback,
        )

        # Initialize handler registry for file processing
        self.handler_registry = create_default_registry()

        logger.info(
            "Initialized TranslationPipeline with %d handlers",
            len(self.handler_registry.handlers),
        )

    def _on_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cumulative_input: int,
        cumulative_output: int,
        cumulative_total: int,
    ) -> None:
        """Handle token usage updates from LLM.

        Args:
            input_tokens: Input tokens for this call
            output_tokens: Output tokens for this call
            total_tokens: Total tokens for this call
            cumulative_input: Cumulative input tokens
            cumulative_output: Cumulative output tokens
            cumulative_total: Cumulative total tokens
        """
        logger.debug(
            "Token usage: +%d input, +%d output, +%d total (누적: %d input, %d output, %d total)",
            input_tokens,
            output_tokens,
            total_tokens,
            cumulative_input,
            cumulative_output,
            cumulative_total,
        )

    def _report_progress(
        self,
        message: str,
        current: int,
        total: int,
        stats: dict[str, object] | None = None,
    ) -> None:
        """Report progress via callback if available.

        Args:
            message: Progress message
            current: Current progress value
            total: Total progress value
            stats: Optional additional statistics
        """
        logger.debug("Progress: %s (%d/%d)", message, current, total)

        # Add token usage to stats if available
        if stats is None:
            stats = {}
        token_usage = self.llm_client.get_token_usage()
        stats.update(
            {
                "input_tokens": token_usage["input_tokens"],
                "output_tokens": token_usage["output_tokens"],
                "total_tokens": token_usage["total_tokens"],
            }
        )

        if self.progress_callback:
            try:
                self.progress_callback(message, current, total, stats)  # type: ignore[misc]
            except Exception as e:
                logger.warning("Progress callback failed: %s", e)
        else:
            logger.warning("No progress callback set!")

    async def run(
        self,
        modpack_path: Path | str,
        output_path: Path | str,
        glossary_path: Path | str | None = None,
        selected_files: list[object] | None = None,
    ) -> PipelineResult:
        """Run the complete translation pipeline.

        Args:
            modpack_path: Path to the modpack directory.
            output_path: Path for output files.
            glossary_path: Optional path to existing glossary.
            selected_files: Optional list of selected LanguageFilePair to translate.
                          If None, scans and translates all files.

        Returns:
            Pipeline result with all outputs and statistics.
        """
        modpack_path = Path(modpack_path)
        output_path = Path(output_path)

        result = PipelineResult()
        result.start_time = datetime.now()

        logger.info("Starting translation pipeline")
        logger.info("Modpack: %s", modpack_path)
        logger.info("Output: %s", output_path)

        try:
            # Step 1: Prepare file pairs
            if selected_files:
                # Use provided selected files
                logger.info("Using %d pre-selected files", len(selected_files))
                file_pairs = selected_files  # type: ignore[assignment]

                # Create minimal scan result
                from .scanner import ScanResult

                result.scan_result = ScanResult(
                    modpack_path=modpack_path,
                    source_locale=self.config.source_locale,
                    target_locale=self.config.target_locale,
                )
                result.scan_result.paired_files = [
                    fp
                    for fp in file_pairs
                    if fp.target_path  # type: ignore[attr-defined]
                ]
                result.scan_result.source_only_files = [
                    fp
                    for fp in file_pairs
                    if not fp.target_path  # type: ignore[attr-defined]
                ]
            else:
                # Step 1: Scan modpack
                logger.info("Step 1: Scanning modpack...")
                result.scan_result = self.scanner.scan(modpack_path)
                file_pairs = result.scan_result.all_translation_pairs

            if not file_pairs:
                logger.warning("No language files found!")
                return result

            logger.info(
                "Processing %d files",
                len(file_pairs),
            )

            # Step 2: Build or load glossary
            if glossary_path and Path(glossary_path).exists():
                logger.info("Step 2: Loading existing glossary...")
                self._report_progress(
                    "용어집 로드 중...",
                    0,
                    len(file_pairs),  # type: ignore[arg-type]
                )
                result.glossary = await GlossaryBuilder.load_glossary(
                    str(glossary_path)
                )
            elif not self.config.skip_glossary:
                logger.info("Step 2: Building glossary...")
                self._report_progress(
                    f"용어집 생성 중... ({len(file_pairs)}개 파일 분석)",  # type: ignore[arg-type]
                    0,
                    len(file_pairs),  # type: ignore[arg-type]
                )
                result.glossary = await self.glossary_builder.build_from_pairs(
                    file_pairs  # type: ignore[arg-type]
                )

                self._report_progress(
                    f"용어집 생성 완료 ({len(result.glossary.term_rules)}개 용어)",
                    len(file_pairs),  # type: ignore[arg-type]
                    len(file_pairs),  # type: ignore[arg-type]
                )

                # Save glossary if configured (modpack-only, without vanilla)
                if self.config.save_glossary and result.glossary:
                    glossary_output = output_path / "glossary.json"
                    # Save modpack-only glossary (excluding vanilla)
                    glossary_to_save = (
                        self.glossary_builder.modpack_only_glossary
                        if self.glossary_builder.modpack_only_glossary
                        else result.glossary
                    )
                    await self.glossary_builder.save_glossary(
                        glossary_to_save, str(glossary_output)
                    )
                    logger.info(
                        "Saved modpack-only glossary (vanilla glossary excluded)"
                    )
            else:
                logger.info("Step 2: Skipping glossary (disabled)")

            # Update translator and reviewer with glossary
            if result.glossary:
                self.translator.update_glossary(result.glossary)
                self.reviewer.update_glossary(result.glossary)

            # Step 3: Create translation tasks
            logger.info("Step 3: Creating translation tasks...")
            self._report_progress(
                "번역 작업 준비 중...",
                0,
                len(file_pairs),  # type: ignore[arg-type]
            )
            result.tasks = await self._create_tasks(file_pairs, result)  # type: ignore[arg-type]

            # Step 4: Translate
            logger.info("Step 4: Translating...")
            total_entries = sum(len(task.entries) for task in result.tasks)
            self._report_progress(
                f"번역 시작... (총 {total_entries}개 항목)",
                0,
                total_entries,
                {"total": total_entries, "completed": 0, "failed": 0},
            )
            await self._translate_tasks(result.tasks, result)

            # Update statistics
            for task in result.tasks:
                result.total_entries += len(task.entries)
                result.translated_entries += sum(
                    1
                    for e in task.entries.values()
                    if e.status == TranslationStatus.COMPLETED
                )
                result.failed_entries += sum(
                    1
                    for e in task.entries.values()
                    if e.status == TranslationStatus.FAILED
                )

            success_rate = (
                (result.translated_entries / result.total_entries * 100)
                if result.total_entries > 0
                else 0
            )
            self._report_progress(
                f"번역 완료: {result.translated_entries}/{result.total_entries} ({success_rate:.1f}%)",
                result.translated_entries,
                result.total_entries,
                {
                    "total": result.total_entries,
                    "completed": result.translated_entries,
                    "failed": result.failed_entries,
                    "success_rate": f"{success_rate:.1f}%",
                },
            )

            # # Step 4.5: Retry failed translations (up to 2 attempts)
            # retry_count = 0
            # max_retries = 2
            # while result.failed_entries > 0 and retry_count < max_retries:
            #     retry_count += 1
            #     logger.info(
            #         "Step 4.5: Retrying %d failed translations (attempt %d/%d)...",
            #         result.failed_entries,
            #         retry_count,
            #         max_retries,
            #     )
            #     self._report_progress(
            #         f"실패한 번역 재시도 중... ({retry_count}/{max_retries} 시도, {result.failed_entries}개)",
            #         0,
            #         result.failed_entries,
            #         {
            #             "total": result.total_entries,
            #             "completed": result.translated_entries,
            #             "failed": result.failed_entries,
            #             "phase": "retry",
            #         },
            #     )

            #     # Reset failed entries and retry
            #     total_reset = 0
            #     for task in result.tasks:
            #         reset_count = task.reset_failed_entries()
            #         total_reset += reset_count

            #     if total_reset == 0:
            #         break

            #     # Re-translate only tasks with pending entries
            #     await self._translate_tasks(result.tasks, result)

            #     # Recalculate statistics
            #     result.total_entries = 0
            #     result.translated_entries = 0
            #     result.failed_entries = 0
            #     for task in result.tasks:
            #         result.total_entries += len(task.entries)
            #         result.translated_entries += sum(
            #             1
            #             for e in task.entries.values()
            #             if e.status == TranslationStatus.COMPLETED
            #         )
            #         result.failed_entries += sum(
            #             1
            #             for e in task.entries.values()
            #             if e.status == TranslationStatus.FAILED
            #         )

            #     success_rate = (
            #         (result.translated_entries / result.total_entries * 100)
            #         if result.total_entries > 0
            #         else 0
            #     )
            #     self._report_progress(
            #         f"재시도 완료: {result.translated_entries}/{result.total_entries} ({success_rate:.1f}%)",
            #         result.translated_entries,
            #         result.total_entries,
            #         {
            #             "total": result.total_entries,
            #             "completed": result.translated_entries,
            #             "failed": result.failed_entries,
            #             "success_rate": f"{success_rate:.1f}%",
            #         },
            #     )

            # Step 5: Validate
            logger.info("Step 5: Validating translations...")
            self._report_progress(
                "번역 검증 중...",
                result.translated_entries,
                result.total_entries,
                {
                    "total": result.total_entries,
                    "completed": result.translated_entries,
                    "failed": result.failed_entries,
                },
            )
            await self._validate_tasks(result.tasks)

            # Step 6: Review (if enabled)
            if not self.config.skip_review:
                logger.info("Step 6: Reviewing translations...")
                self._report_progress(
                    f"번역 리뷰 중... (총 {result.translated_entries}개 항목)",
                    0,
                    result.translated_entries,
                    {
                        "total": result.translated_entries,
                        "phase": "review",
                    },
                )
                result.reviewed_entries = await self._review_tasks(result.tasks)
                self._report_progress(
                    f"리뷰 완료: {result.reviewed_entries}개 항목 검토됨",
                    result.reviewed_entries,
                    result.translated_entries,
                    {
                        "total": result.translated_entries,
                        "reviewed": result.reviewed_entries,
                        "phase": "review_complete",
                    },
                )
            else:
                logger.info("Step 6: Skipping review (disabled)")

            # Step 7: Generate outputs
            logger.info("Step 7: Generating outputs...")
            self._report_progress(
                "출력 파일 생성 중...",
                result.translated_entries,
                result.total_entries,
                {
                    "total": result.total_entries,
                    "completed": result.translated_entries,
                    "phase": "generating",
                },
            )
            pack_config = ResourcePackConfig(
                pack_format=self.config.pack_format,
                pack_name=self.config.pack_name,
                target_locale=self.config.target_locale,
            )

            result.generation_result = await generate_outputs(
                result.tasks,
                output_path,
                modpack_path,
                pack_config,
                create_zip=self.config.create_zip,
            )

            logger.info("Pipeline completed successfully!")

        except Exception as e:
            logger.exception("Pipeline failed: %s", e)
            raise

        finally:
            result.end_time = datetime.now()

            # Save token usage statistics
            token_usage = self.llm_client.get_token_usage()
            result.total_input_tokens = token_usage["input_tokens"]
            result.total_output_tokens = token_usage["output_tokens"]
            result.total_tokens = token_usage["total_tokens"]

            logger.info(
                "Pipeline finished in %.1f seconds",
                result.duration_seconds,
            )
            logger.info(
                "Results: %d/%d translated (%.1f%% success rate)",
                result.translated_entries,
                result.total_entries,
                result.success_rate * 100,
            )
            logger.info(
                "Token usage: %d input, %d output, %d total",
                result.total_input_tokens,
                result.total_output_tokens,
                result.total_tokens,
            )

        return result

    async def _create_tasks(
        self,
        file_pairs: list[object] | ScanResult,
        result: PipelineResult | None = None,
    ) -> list[TranslationTask]:
        """Create translation tasks from file pairs or scan result.

        Uses content handlers to extract translatable content.
        Handlers automatically select the best extraction method based on file type.

        Args:
            file_pairs: List of LanguageFilePair or ScanResult with file pairs.
            result: Optional PipelineResult to update handler statistics.

        Returns:
            List of translation tasks.
        """
        from .scanner import ScanResult

        tasks: list[TranslationTask] = []
        handler_counts: dict[str, int] = {}

        # Handle both list and ScanResult
        if isinstance(file_pairs, ScanResult):
            pairs = file_pairs.all_translation_pairs
        else:
            pairs = file_pairs  # type: ignore[assignment]

        for pair in pairs:
            try:
                # Get handler for this file
                handler = self.handler_registry.get_handler(pair.source_path)
                if handler is None:
                    logger.warning("No handler for: %s", pair.source_path)
                    continue

                # Track handler usage
                handler_name = handler.name
                handler_counts[handler_name] = handler_counts.get(handler_name, 0) + 1

                logger.debug(
                    "Using handler '%s' for: %s",
                    handler.name,
                    pair.source_path.name,
                )

                # Extract source data using handler
                source_data = await handler.extract(pair.source_path)

                # Load existing translation if available
                existing_data: dict[str, str] | None = None
                if pair.target_path and pair.target_path.exists():
                    target_handler = self.handler_registry.get_handler(pair.target_path)
                    if target_handler:
                        existing_data = dict(
                            await target_handler.extract(pair.target_path)
                        )

                # Create task
                task = TranslationTask.from_source_data(
                    pair, dict(source_data), existing_data
                )
                tasks.append(task)

            except Exception as e:
                logger.error("Failed to create task for %s: %s", pair.source_path, e)

        # Update result with handler statistics
        if result is not None:
            result.handler_stats = handler_counts
            result.file_count = len(tasks)

        return tasks

    async def _translate_tasks(
        self, tasks: list[TranslationTask], result: PipelineResult
    ) -> None:
        """Translate all tasks.

        Args:
            tasks: List of translation tasks.
            result: Pipeline result to update statistics.
        """
        # Filter tasks that need translation
        tasks_to_translate = [task for task in tasks if task.pending_entries]
        total_tasks = len(tasks_to_translate)

        if not tasks_to_translate:
            return

        # Calculate total batches across all tasks
        total_batches = sum(
            len(
                task.create_batches(
                    max_entries=self.translator.batch_size,
                    max_chars=self.translator.max_batch_chars,
                )
            )
            for task in tasks_to_translate
        )
        completed_batches = 0

        # Translate with progress tracking
        completed = 0
        total_entries = sum(len(task.entries) for task in tasks)
        completed_entries = 0
        failed_entries = 0

        # Create custom progress callback for translator
        def batch_progress_callback(
            message: str, current: int, total: int, stats: dict[str, object]
        ) -> None:
            nonlocal completed_batches
            # This is called for each batch completion
            completed_batches += 1

            # Calculate success rate
            current_total = completed_entries + failed_entries
            success_rate = "0%"
            if current_total > 0:
                rate = (completed_entries / current_total) * 100
                success_rate = f"{rate:.1f}%"

            self._report_progress(
                f"번역 중... ({completed_batches}/{total_batches} 배치, {completed}/{total_tasks} 파일)",
                completed_batches,
                total_batches,
                {
                    "total": total_entries,
                    "completed": completed_entries,
                    "failed": failed_entries,
                    "success_rate": success_rate,
                    "batches": completed_batches,
                    "total_batches": total_batches,
                },
            )

        # Temporarily replace translator's progress callback
        original_callback = self.translator.progress_callback
        self.translator.progress_callback = batch_progress_callback

        # Use queue-based worker pool for efficient concurrency
        queue: asyncio.Queue[TranslationTask | None] = asyncio.Queue()

        # Put all tasks into the queue
        for task in tasks_to_translate:
            await queue.put(task)

        # Worker function
        async def worker() -> None:
            nonlocal completed, completed_entries, failed_entries
            while True:
                task = await queue.get()
                if task is None:
                    queue.task_done()
                    break
                try:
                    await self.translator.translate_task(task)
                    completed += 1

                    # Count completed/failed entries
                    task_completed = sum(
                        1
                        for e in task.entries.values()
                        if e.status == TranslationStatus.COMPLETED
                    )
                    task_failed = sum(
                        1
                        for e in task.entries.values()
                        if e.status == TranslationStatus.FAILED
                    )
                    completed_entries += task_completed
                    failed_entries += task_failed

                    # Report progress after each file completes
                    current_total = completed_entries + failed_entries
                    success_rate = (
                        f"{(completed_entries / current_total * 100):.1f}%"
                        if current_total > 0
                        else "0%"
                    )
                    self._report_progress(
                        f"번역 중... ({completed_batches}/{total_batches} 배치, {completed}/{total_tasks} 파일)",
                        completed_batches,
                        total_batches,
                        {
                            "total": total_entries,
                            "completed": completed_entries,
                            "failed": failed_entries,
                            "success_rate": success_rate,
                            "batches": completed_batches,
                            "total_batches": total_batches,
                        },
                    )
                except Exception as e:
                    completed += 1
                    failed_entries += len(task.entries)
                    logger.error("Task translation failed: %s", e)

                    current_total = completed_entries + failed_entries
                    success_rate = (
                        f"{(completed_entries / current_total * 100):.1f}%"
                        if current_total > 0
                        else "0%"
                    )
                    self._report_progress(
                        f"번역 중... ({completed}/{total_tasks} 파일) - 오류 발생",
                        completed_entries,
                        total_entries,
                        {
                            "total": total_entries,
                            "completed": completed_entries,
                            "failed": failed_entries,
                            "success_rate": success_rate,
                            "error": str(e),
                        },
                    )
                finally:
                    queue.task_done()

        # Start workers (limit to reasonable number for file-level parallelism)
        # Use fewer workers than max_concurrent since each task spawns its own workers
        num_workers = min(self.config.max_concurrent, len(tasks_to_translate))
        workers = [asyncio.create_task(worker()) for _ in range(num_workers)]

        # Wait for all tasks to be processed
        await queue.join()

        # Signal workers to stop
        for _ in range(num_workers):
            await queue.put(None)

        # Wait for workers to finish
        await asyncio.gather(*workers)

        # Restore original callback
        self.translator.progress_callback = original_callback

    async def _validate_tasks(self, tasks: list[TranslationTask]) -> None:
        """Validate all tasks.

        Args:
            tasks: List of translation tasks.
        """
        for task in tasks:
            if task.status != TranslationStatus.COMPLETED:
                continue

            # Get source and translated data
            source_data = {e.key: e.source_text for e in task.entries.values()}
            translated_data = task.to_output_dict()

            # Validate
            validation_result = self.validator.validate(source_data, translated_data)

            if not validation_result.is_valid:
                logger.warning(
                    "Validation issues in %s: %d errors, %d warnings",
                    task.file_pair.source_path,
                    validation_result.errors_count,
                    validation_result.warnings_count,
                )

                # Attempt to fix some issues
                fixed_data = self.validator.fix_issues(
                    source_data, dict(translated_data), validation_result
                )

                # Update task entries
                for key, value in fixed_data.items():
                    if key in task.entries:
                        task.entries[key].translated_text = value

    async def _review_tasks(self, tasks: list[TranslationTask]) -> int:
        """Review all tasks with LLM.

        Args:
            tasks: List of translation tasks.

        Returns:
            Number of reviewed entries.
        """
        reviewed_count = 0
        completed_tasks = [t for t in tasks if t.status == TranslationStatus.COMPLETED]
        total_tasks = len(completed_tasks)

        # Calculate total review batches (50 entries per batch)
        total_batches = sum(
            (len(t.entries) + 49) // 50  # Ceiling division
            for t in completed_tasks
        )

        completed_batches = 0
        current_task = 0

        # Create custom progress callback for reviewer
        def batch_progress_callback(
            message: str, current: int, total: int, stats: dict[str, object]
        ) -> None:
            nonlocal completed_batches
            completed_batches += 1

            self._report_progress(
                f"리뷰 중... ({completed_batches}/{total_batches} 배치, {current_task}/{total_tasks} 파일)",
                completed_batches,
                total_batches,
                {
                    "reviewed": reviewed_count,
                    "current_task": current_task,
                    "total_tasks": total_tasks,
                    "batches": completed_batches,
                    "total_batches": total_batches,
                    "phase": "reviewing",
                },
            )

        # Temporarily replace reviewer's progress callback
        original_callback = self.reviewer.progress_callback
        self.reviewer.progress_callback = batch_progress_callback

        for task in completed_tasks:
            current_task += 1

            # Get source and translated data
            source_data = {e.key: e.source_text for e in task.entries.values()}
            translated_data = dict(task.to_output_dict())

            # Review and correct
            corrected_data, review_result = await self.reviewer.review_and_correct(
                source_data, translated_data
            )

            reviewed_count += review_result.reviewed_count

            # Update task entries with corrections
            for key, value in corrected_data.items():
                if key in task.entries:
                    task.entries[key].translated_text = value

        # Restore original callback
        self.reviewer.progress_callback = original_callback

        return reviewed_count

    async def retry_failed(self, result: PipelineResult) -> PipelineResult:
        """Retry all failed translations.

        This method resets failed entries and re-attempts translation.
        Does NOT regenerate outputs - call generate_outputs separately if needed.

        Args:
            result: Previous pipeline result with failed translations.

        Returns:
            Updated pipeline result.
        """
        if not result.has_failures:
            logger.info("No failed translations to retry")
            return result

        logger.info("Retrying %d failed translations...", result.failed_entries)

        # Reset failed entries to pending
        total_reset = 0
        for task in result.tasks:
            reset_count = task.reset_failed_entries()
            total_reset += reset_count

        logger.info("Reset %d entries for retry", total_reset)

        # Re-translate
        await self._translate_tasks(result.tasks, result)

        # Validate
        logger.info("Validating retried translations...")
        await self._validate_tasks(result.tasks)

        # Review (if enabled)
        if not self.config.skip_review:
            logger.info("Reviewing retried translations...")
            await self._review_tasks(result.tasks)

        # Update statistics
        result.update_statistics()

        logger.info(
            "Retry completed: %d/%d translated (%.1f%% success rate)",
            result.translated_entries,
            result.total_entries,
            result.success_rate * 100,
        )

        return result

    async def regenerate_outputs(
        self,
        result: PipelineResult,
        output_path: Path | str,
        modpack_path: Path | str,
    ) -> PipelineResult:
        """Regenerate output files from existing results.

        Call this after retry_failed() to update output files.

        Args:
            result: Pipeline result with translations.
            output_path: Path for output files.
            modpack_path: Path to the modpack directory.

        Returns:
            Updated pipeline result with new generation result.
        """
        output_path = Path(output_path)
        modpack_path = Path(modpack_path)

        logger.info("Regenerating outputs...")

        pack_config = ResourcePackConfig(
            pack_format=self.config.pack_format,
            pack_name=self.config.pack_name,
            target_locale=self.config.target_locale,
        )

        result.generation_result = await generate_outputs(
            result.tasks,
            output_path,
            modpack_path,
            pack_config,
            create_zip=self.config.create_zip,
        )

        logger.info("Output regeneration completed")
        return result


async def run_pipeline(
    modpack_path: str,
    output_path: str,
    glossary_path: str | None = None,
    **config_kwargs: object,
) -> PipelineResult:
    """Convenience function to run the translation pipeline.

    Args:
        modpack_path: Path to the modpack directory.
        output_path: Path for output files.
        glossary_path: Optional path to existing glossary.
        **config_kwargs: Additional configuration options.

    Returns:
        Pipeline result.
    """
    config = PipelineConfig(**config_kwargs)  # type: ignore[arg-type]
    pipeline = TranslationPipeline(config)

    return await pipeline.run(modpack_path, output_path, glossary_path)
