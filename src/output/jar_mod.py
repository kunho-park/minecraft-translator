"""Generator for modifying JAR files with translations."""

from __future__ import annotations

import logging
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..handlers.base import create_default_registry

if TYPE_CHECKING:
    from ..models import TranslationTask

logger = logging.getLogger(__name__)


@dataclass
class JarModConfig:
    """Configuration for JAR modification."""

    target_locale: str = "ko_kr"


class JarModGenerator:
    """Generator for modifying JAR files.

    Copies original JARs and injects translated files into them.
    Used for mods where resource packs or overrides don't work (e.g., Origins data files).
    """

    def __init__(self, config: JarModConfig | None = None) -> None:
        """Initialize the generator.

        Args:
            config: Configuration.
        """
        self.config = config or JarModConfig()
        self.registry = create_default_registry()
        logger.info("Initialized JarModGenerator")

    async def generate(
        self,
        tasks: list[TranslationTask],
        output_dir: Path,
        modpack_root: Path,
    ) -> list[Path]:
        """Generate modified JAR files.

        Args:
            tasks: List of translation tasks.
            output_dir: Output directory.
            modpack_root: Original modpack root directory.

        Returns:
            List of generated JAR file paths.
        """
        logger.info("Generating JAR mods for %d tasks", len(tasks))

        output_dir = Path(output_dir)
        mods_output_dir = output_dir / "mods"
        mods_output_dir.mkdir(parents=True, exist_ok=True)

        # Group tasks by JAR name
        jar_tasks: dict[str, list[TranslationTask]] = {}

        for task in tasks:
            jar_name = self._get_jar_name_from_path(task.file_pair.source_path)
            if jar_name:
                if jar_name not in jar_tasks:
                    jar_tasks[jar_name] = []
                jar_tasks[jar_name].append(task)
            else:
                logger.warning(
                    "Could not determine JAR name for task: %s",
                    task.file_pair.source_path,
                )

        generated_files: list[Path] = []

        for jar_name, tasks in jar_tasks.items():
            try:
                jar_path = await self._process_jar(
                    jar_name, tasks, mods_output_dir, modpack_root
                )
                if jar_path:
                    generated_files.append(jar_path)
            except Exception as e:
                logger.error("Failed to process JAR %s: %s", jar_name, e)

        logger.info("Generated %d modified JARs", len(generated_files))
        return generated_files

    def _get_jar_name_from_path(self, source_path: Path) -> str | None:
        """Extract JAR name from the extracted source path.

        Assumes path structure: .../.mct_cache/extracted/<jar_name>/...
        """
        try:
            parts = source_path.parts
            # Look for 'extracted' folder
            if "extracted" in parts:
                idx = parts.index("extracted")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
        except ValueError:
            pass
        return None

    async def _process_jar(
        self,
        jar_name: str,
        tasks: list[TranslationTask],
        output_dir: Path,
        modpack_root: Path,
    ) -> Path | None:
        """Process a single JAR file.

        1. Copy original JAR to output.
        2. Inject translations.
        """
        original_jar = modpack_root / "mods" / jar_name
        if not original_jar.exists():
            logger.error("Original JAR not found: %s", original_jar)
            return None

        output_jar = output_dir / jar_name

        # Create a mapping of internal path -> translation content
        replacements: dict[str, bytes] = {}

        for task in tasks:
            # Calculate internal path in JAR
            # Source path: .../extracted/jar_name/path/to/file
            # Internal path: path/to/file
            try:
                source_path = task.file_pair.source_path
                parts = source_path.parts
                try:
                    idx = parts.index(jar_name)
                    internal_path = "/".join(
                        parts[idx + 1 :]
                    )  # relative path inside JAR
                except ValueError:
                    # Fallback if jar_name not in parts (unlikely with current logic)
                    # Try to find 'extracted' and take everything after jar name
                    if "extracted" in parts:
                        idx = parts.index("extracted")
                        # parts[idx+1] is jar_name
                        internal_path = "/".join(parts[idx + 2 :])
                    else:
                        logger.warning(
                            "Could not determine internal path for %s", source_path
                        )
                        continue

                # Use handler to generate content to preserve structure
                handler = self.registry.get_handler(source_path)
                if handler:
                    # Create temp file for output
                    # Must preserve suffix so BaseParser can detect file type
                    suffix = source_path.suffix
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=suffix
                    ) as tmp:
                        tmp_path = Path(tmp.name)

                    try:
                        # Close the file so handler can write to it
                        tmp.close()

                        translations = task.to_output_dict()
                        # apply() reads source, patches with translations, writes to tmp_path
                        await handler.apply(source_path, translations, tmp_path)

                        # Read content
                        if tmp_path.exists() and tmp_path.stat().st_size > 0:
                            content = tmp_path.read_bytes()
                            replacements[internal_path] = content
                        else:
                            logger.warning(
                                "Handler produced empty output for %s", source_path
                            )
                    finally:
                        if tmp_path.exists():
                            tmp_path.unlink()
                else:
                    # Fallback: simple JSON dump (only safe for simple key-value files)
                    logger.warning(
                        "No handler found for %s, falling back to simple JSON dump. Structure may be lost.",
                        source_path,
                    )
                    output_data = task.to_output_dict()
                    import json

                    content_str = json.dumps(output_data, ensure_ascii=False, indent=2)
                    replacements[internal_path] = content_str.encode("utf-8")

            except Exception as e:
                logger.error(
                    "Failed to prepare translation for %s: %s",
                    task.file_pair.source_path,
                    e,
                )

        # Rebuild JAR
        # We use a temporary file to rebuild, then move to output
        temp_jar = output_jar.with_suffix(".tmp.jar")

        try:
            with zipfile.ZipFile(original_jar, "r") as source_zip:
                with zipfile.ZipFile(
                    temp_jar, "w", compression=zipfile.ZIP_DEFLATED
                ) as target_zip:
                    # Copy all files from source
                    injected_count = 0
                    for item in source_zip.infolist():
                        # Normalize filename to handle Windows paths in ZIPs
                        normalized_filename = item.filename.replace("\\", "/")

                        # If we have a replacement, write that instead
                        if normalized_filename in replacements:
                            logger.debug(
                                "Injecting translation for %s in %s",
                                normalized_filename,
                                jar_name,
                            )
                            # Use original item (preserves metadata) but write new content
                            target_zip.writestr(item, replacements[normalized_filename])
                            del replacements[normalized_filename]
                            injected_count += 1
                        else:
                            # Copy original
                            target_zip.writestr(item, source_zip.read(item.filename))

                    logger.info("Injected %d files into %s", injected_count, jar_name)

                    # If there are leftovers in replacements (files that didn't exist?), add them
                    # (Though usually we are modifying existing files)
                    if replacements:
                        logger.warning(
                            "Adding %d new files to %s (not found in original JAR): %s",
                            len(replacements),
                            jar_name,
                            list(replacements.keys()),
                        )
                        for path, content in replacements.items():
                            logger.debug("Adding new file %s to %s", path, jar_name)
                            target_zip.writestr(path, content)

            # Move temp to final
            if output_jar.exists():
                output_jar.unlink()
            temp_jar.rename(output_jar)
            logger.info("Created modified JAR: %s", output_jar)
            return output_jar

        except Exception as e:
            if temp_jar.exists():
                temp_jar.unlink()
            raise e
