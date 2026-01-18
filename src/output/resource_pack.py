"""Resource pack generator for Minecraft translation outputs."""

from __future__ import annotations

import json
import logging
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles

from ..handlers.base import create_default_registry
from .jar_mod import JarModGenerator

if TYPE_CHECKING:
    from ..models import TranslationTask


logger = logging.getLogger(__name__)

# Default resource pack metadata
DEFAULT_PACK_FORMAT = 15  # Minecraft 1.20.x
DEFAULT_DESCRIPTION = "Auto-translated language pack"


@dataclass
class ResourcePackConfig:
    """Configuration for resource pack generation."""

    pack_format: int = DEFAULT_PACK_FORMAT
    description: str = DEFAULT_DESCRIPTION
    pack_name: str = "translations"
    target_locale: str = "ko_kr"


@dataclass
class GenerationResult:
    """Result of output generation."""

    resource_pack_path: Path | None = None
    override_paths: list[Path] = field(default_factory=list)
    override_zip_path: Path | None = None
    jar_mod_paths: list[Path] = field(default_factory=list)
    files_generated: int = 0
    errors: list[str] = field(default_factory=list)


def create_zip_from_directory(source_dir: Path, zip_path: Path) -> None:
    """Create a zip file from a directory.

    Args:
        source_dir: Source directory to zip.
        zip_path: Output zip file path.
    """
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                arc_name = file_path.relative_to(source_dir)
                zf.write(file_path, arc_name)


class ResourcePackGenerator:
    """Generator for Minecraft resource packs containing translations.

    Creates a resource pack with the translated language files
    that can be loaded in Minecraft to apply translations.
    """

    def __init__(self, config: ResourcePackConfig | None = None) -> None:
        """Initialize the generator.

        Args:
            config: Resource pack configuration.
        """
        self.config = config or ResourcePackConfig()
        logger.info("Initialized ResourcePackGenerator")

    async def generate(
        self,
        tasks: list[TranslationTask],
        output_dir: Path,
        create_zip: bool = True,
    ) -> GenerationResult:
        """Generate resource pack from translated tasks.

        Args:
            tasks: List of completed translation tasks.
            output_dir: Output directory for generated files.
            create_zip: Whether to create a zip file.

        Returns:
            Generation result.
        """
        logger.info("Generating resource pack for %d tasks", len(tasks))

        result = GenerationResult()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create resource pack directory structure
        pack_dir = output_dir / "resourcepack"
        assets_dir = pack_dir / "assets"

        # Clean existing pack
        if pack_dir.exists():
            shutil.rmtree(pack_dir)

        pack_dir.mkdir(parents=True)
        assets_dir.mkdir(parents=True)

        # Generate pack.mcmeta
        await self._write_pack_mcmeta(pack_dir)

        # Generate language files
        files_count = 0

        for task in tasks:
            if task.entries:
                try:
                    await self._write_language_file(task, assets_dir)
                    files_count += 1
                except Exception as e:
                    error_msg = f"Failed to write {task.file_pair.namespace}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

        result.files_generated = files_count

        # Create zip if requested
        if create_zip and files_count > 0:
            zip_path = output_dir / f"{self.config.pack_name}.zip"
            create_zip_from_directory(pack_dir, zip_path)
            result.resource_pack_path = zip_path
            logger.info("Created resource pack: %s", zip_path)
        else:
            result.resource_pack_path = pack_dir

        logger.info(
            "Generation complete: %d files, %d errors",
            files_count,
            len(result.errors),
        )

        return result

    async def _write_pack_mcmeta(self, pack_dir: Path) -> None:
        """Write pack.mcmeta file.

        Args:
            pack_dir: Resource pack directory.
        """
        mcmeta = {
            "pack": {
                "pack_format": self.config.pack_format,
                "description": self.config.description,
            }
        }

        mcmeta_path = pack_dir / "pack.mcmeta"
        async with aiofiles.open(mcmeta_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(mcmeta, ensure_ascii=False, indent=2))

    async def _write_language_file(
        self,
        task: TranslationTask,
        assets_dir: Path,
    ) -> None:
        """Write a language file for a task.

        Args:
            task: Translation task with completed entries.
            assets_dir: Assets directory.
        """
        namespace = task.file_pair.namespace or "minecraft"
        lang_dir = assets_dir / namespace / "lang"
        lang_dir.mkdir(parents=True, exist_ok=True)

        # Get output data
        output_data = task.to_output_dict()

        # Write language file
        lang_file = lang_dir / f"{self.config.target_locale}.json"
        async with aiofiles.open(lang_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(output_data, ensure_ascii=False, indent=2))

        logger.debug("Wrote language file: %s", lang_file)


class OverrideGenerator:
    """Generator for override files (config, KubeJS, etc.).

    Creates files that need to directly overwrite modpack files
    rather than being loaded as a resource pack.
    """

    def __init__(self, target_locale: str = "ko_kr") -> None:
        """Initialize the generator.

        Args:
            target_locale: Target language locale.
        """
        self.target_locale = target_locale
        self.registry = create_default_registry()
        logger.info("Initialized OverrideGenerator")

    async def generate(
        self,
        tasks: list[TranslationTask],
        output_dir: Path,
        modpack_root: Path,
    ) -> list[Path]:
        """Generate override files.

        Args:
            tasks: List of completed translation tasks.
            output_dir: Output directory for override files.
            modpack_root: Original modpack root path.

        Returns:
            List of generated file paths.
        """
        logger.info("Generating override files for %d tasks", len(tasks))

        output_dir = Path(output_dir)
        override_dir = output_dir / "overrides"
        override_dir.mkdir(parents=True, exist_ok=True)

        generated_files: list[Path] = []

        for task in tasks:
            # Check if this file should be an override
            if self._should_be_override(task.file_pair.source_path):
                try:
                    file_path = await self._write_override_file(
                        task, override_dir, modpack_root
                    )
                    if file_path:
                        generated_files.append(file_path)
                except Exception as e:
                    logger.error(
                        "Failed to write override for %s: %s",
                        task.file_pair.source_path,
                        e,
                    )

        logger.info("Generated %d override files", len(generated_files))
        return generated_files

    def _should_be_override(self, source_path: Path | str) -> bool:
        """Check if a file should be an override rather than resource pack.

        Args:
            source_path: Source file path.

        Returns:
            True if file should be an override.
        """
        path_str = str(source_path).lower().replace("\\", "/")

        # Files that can't go in resource packs
        override_patterns = [
            "kubejs/",
            "config/",
            "scripts/",
            "/ftbquests/",
        ]

        return any(pattern in path_str for pattern in override_patterns)

    async def _write_override_file(
        self,
        task: TranslationTask,
        override_dir: Path,
        modpack_root: Path,
    ) -> Path | None:
        """Write an override file.

        Args:
            task: Translation task.
            override_dir: Override output directory.
            modpack_root: Original modpack root.

        Returns:
            Path to generated file or None.
        """
        source_path = Path(task.file_pair.source_path)

        # Calculate relative path from modpack root
        try:
            rel_path = source_path.relative_to(modpack_root)
        except ValueError:
            rel_path = source_path.name

        # Replace source locale with target locale in path
        rel_path_str = str(rel_path).replace("en_us", self.target_locale)
        output_path = override_dir / rel_path_str

        # Create parent directories
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = task.to_output_dict()

        # Try to use handler first (preserves structure)
        handler = self.registry.get_handler(source_path)
        if handler:
            try:
                await handler.apply(source_path, output_data, output_path)
                logger.debug("Wrote override file using handler: %s", output_path)
                return output_path
            except Exception as e:
                logger.warning(
                    "Handler failed to apply overrides for %s, falling back to parser: %s",
                    source_path,
                    e,
                )

        # Fallback to parser
        from ..parsers import BaseParser

        parser = BaseParser.create_parser(output_path, source_path)
        if parser is None:
            logger.debug("No parser for override: %s", output_path)
            return None

        await parser.dump(output_data)

        logger.debug("Wrote override file: %s", output_path)
        return output_path


async def generate_outputs(
    tasks: list[TranslationTask],
    output_dir: Path | str,
    modpack_root: Path | str,
    pack_config: ResourcePackConfig | None = None,
    create_zip: bool = True,
    progress_callback: object | None = None,
) -> GenerationResult:
    """Convenience function to generate all outputs.

    Args:
        tasks: List of completed translation tasks.
        output_dir: Output directory.
        modpack_root: Modpack root directory.
        pack_config: Resource pack configuration.
        create_zip: Whether to zip the outputs.
        progress_callback: Optional progress callback.

    Returns:
        Generation result.
    """
    output_dir = Path(output_dir)
    modpack_root = Path(modpack_root)

    # Separate tasks by type
    resource_pack_tasks: list[TranslationTask] = []
    override_tasks: list[TranslationTask] = []
    jar_mod_tasks: list[TranslationTask] = []

    override_gen = OverrideGenerator()

    for task in tasks:
        # Check for Jar Mod tasks first
        if _should_be_jar_mod(task):
            jar_mod_tasks.append(task)
        elif override_gen._should_be_override(task.file_pair.source_path):
            # Skip extracted files for overrides to prevent temporary paths in output
            # (Extracted files are inside JARs, so they can't be overrides unless extracted to system path, which is rare)
            if ".mct_cache" in str(task.file_pair.source_path) or "extracted" in str(
                task.file_pair.source_path
            ):
                logger.debug(
                    "Skipping extracted override candidate: %s",
                    task.file_pair.source_path,
                )
                continue
            override_tasks.append(task)
        else:
            resource_pack_tasks.append(task)

    # Generate resource pack
    pack_gen = ResourcePackGenerator(pack_config)
    result = await pack_gen.generate(
        resource_pack_tasks, output_dir, create_zip=create_zip
    )

    # Generate overrides
    if override_tasks:
        override_paths = await override_gen.generate(
            override_tasks, output_dir, modpack_root
        )
        result.override_paths = override_paths
        result.files_generated += len(override_paths)

        # Zip overrides if requested
        if create_zip and override_paths:
            override_dir = output_dir / "overrides"
            zip_path = (
                output_dir / f"{pack_config.pack_name}_overrides.zip"
                if pack_config
                else output_dir / "overrides.zip"
            )
            create_zip_from_directory(override_dir, zip_path)
            result.override_zip_path = zip_path
            logger.info("Created override zip: %s", zip_path)

    # Generate JAR mods
    if jar_mod_tasks:
        jar_mod_gen = JarModGenerator()
        jar_mod_paths = await jar_mod_gen.generate(
            jar_mod_tasks, output_dir, modpack_root, progress_callback
        )
        result.jar_mod_paths = jar_mod_paths
        result.files_generated += len(jar_mod_paths)

    return result


def _should_be_jar_mod(task: TranslationTask) -> bool:
    """Check if a task should be handled as a JAR modification."""
    source_path_str = str(task.file_pair.source_path).lower().replace("\\", "/")

    # Must be from extracted cache
    if ".mct_cache" not in source_path_str and "extracted" not in source_path_str:
        return False

    # If it's in data/ folder, it usually requires JAR modification
    # (unless it's a datapack, but finding data inside JAR usually implies it's a mod internal data)
    if "/data/" in source_path_str:
        return True

    return False
