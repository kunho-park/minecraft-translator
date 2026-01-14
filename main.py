"""Example usage of the translation pipeline."""

import asyncio
import logging
from pathlib import Path

import colorlog

from src import LLMProvider, PipelineConfig, PipelineResult, TranslationPipeline


def setup_logging() -> None:
    """Configure logging with colorlog."""
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        fmt="%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    handler.setFormatter(formatter)

    logger = colorlog.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def print_result_summary(result: PipelineResult) -> None:
    """Print summary of pipeline result.

    Args:
        result: Pipeline result to summarize.
    """
    print("\n" + "=" * 50)
    print("Translation Pipeline Summary")
    print("=" * 50)
    print(f"Duration: {result.duration_seconds:.1f} seconds")
    print(f"Total entries: {result.total_entries}")
    print(f"Translated: {result.translated_entries}")
    print(f"Failed: {result.failed_entries}")
    print(f"Success rate: {result.success_rate * 100:.1f}%")

    if result.generation_result:
        print(f"\nOutput files generated: {result.generation_result.files_generated}")
        if result.generation_result.resource_pack_path:
            print(f"Resource pack: {result.generation_result.resource_pack_path}")
        if result.generation_result.override_paths:
            print(f"Override files: {len(result.generation_result.override_paths)}")


def print_failure_details(result: PipelineResult) -> None:
    """Print details of failed translations.

    Args:
        result: Pipeline result with failures.
    """
    print("\n" + "-" * 50)
    print("Failed Translations Details:")
    print("-" * 50)

    failed_summary = result.get_failed_summary()
    for file_path, count in failed_summary.items():
        print(f"  {file_path}: {count} failed")

    # Show sample errors
    print("\nSample errors:")
    shown = 0
    for task in result.tasks:
        for entry in task.failed_entries:
            if entry.error:
                print(f"  [{entry.key}] {entry.error[:100]}")
                shown += 1
                if shown >= 5:
                    break
        if shown >= 5:
            break


def ask_retry() -> bool:
    """Ask user if they want to retry failed translations.

    Returns:
        True if user wants to retry.
    """
    while True:
        response = input("\n재시도 하시겠습니까? (y/n): ").strip().lower()
        if response in ("y", "yes", "예", "ㅇ"):
            return True
        if response in ("n", "no", "아니오", "ㄴ"):
            return False
        print("y 또는 n으로 답해주세요.")


async def retry_failed_translations(
    pipeline: TranslationPipeline,
    result: PipelineResult,
    modpack_path: Path,
    output_path: Path,
) -> PipelineResult:
    """Interactive retry loop for failed translations.

    Asks user if they want to retry failed translations and continues
    until all succeed or user chooses to stop.

    Args:
        pipeline: Translation pipeline instance.
        result: Previous pipeline result.
        modpack_path: Path to modpack directory.
        output_path: Path for output files.

    Returns:
        Final pipeline result.
    """
    while result.has_failures:
        print_failure_details(result)

        if not ask_retry():
            print("\n재시도를 건너뜁니다.")
            break

        print("\n실패한 번역을 재시도합니다...")
        result = await pipeline.retry_failed(result)
        print_result_summary(result)

    # Regenerate outputs if there were retries
    if result.translated_entries > 0:
        print("\n출력 파일을 재생성합니다...")
        result = await pipeline.regenerate_outputs(result, output_path, modpack_path)

    return result


async def main() -> None:
    """Run the translation pipeline example."""
    setup_logging()

    # Configuration
    config = PipelineConfig(
        # Language settings
        source_locale="en_us",
        target_locale="ko_kr",
        # LLM settings (default: Ollama with gpt-oss:20b)
        llm_provider=LLMProvider.OLLAMA,
        llm_model="gpt-oss:20b",
        llm_temperature=0.1,
        llm_base_url="http://localhost:11434",
        # Concurrency settings
        max_concurrent=1,
        batch_size=30,
        max_batch_chars=8000,  # Character limit per batch (None = no limit)
        # Output settings
        pack_format=15,  # Minecraft 1.20.x
        pack_name="translated_pack",
        create_zip=True,
        # Pipeline options
        skip_glossary=False,
        skip_review=False,
        save_glossary=True,
    )

    # Initialize pipeline
    pipeline = TranslationPipeline(config)

    # Paths
    modpack_path = Path("./test/modpack")
    output_path = Path("./test/output")

    if not modpack_path.exists():
        print(f"Error: Modpack path does not exist: {modpack_path}")
        print("Please provide a valid modpack directory path.")
        return

    # Run pipeline
    result = await pipeline.run(
        modpack_path=modpack_path,
        output_path=output_path,
    )

    # Print initial results
    print_result_summary(result)

    # Handle failures interactively
    if result.has_failures:
        result = await retry_failed_translations(
            pipeline, result, modpack_path, output_path
        )

    # Final summary
    print("\n" + "=" * 50)
    print("Translation Pipeline Complete!")
    print("=" * 50)
    if result.success_rate == 1.0:
        print("모든 번역이 성공적으로 완료되었습니다! ✓")
    else:
        print(f"최종 결과: {result.translated_entries}/{result.total_entries} 완료")
        print(f"실패한 항목: {result.failed_entries}개")


if __name__ == "__main__":
    asyncio.run(main())
