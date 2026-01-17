"""Scanner for finding language files in Minecraft modpacks."""

from __future__ import annotations

import logging
import os
import re
import zipfile
from dataclasses import dataclass, field
from glob import escape as glob_escape
from glob import iglob
from pathlib import Path
from typing import TYPE_CHECKING

from ..handlers.base import create_default_registry
from ..models import LanguageFilePair
from ..parsers import BaseParser

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

# Directories to scan for translation files
DIR_FILTER_WHITELIST = [
    "lang/",
    "assets/",
    "data/",
    "kubejs/",
    "config/",
    "patchouli_books/",
]


@dataclass
class TranslationFile:
    """Information about a translation file."""

    input_path: str
    file_type: (
        str  # config, ftbquests, kubejs, patchouli, resourcepacks, datapacks, mod
    )
    lang_type: str = "source"  # source, target, other
    jar_name: str | None = None
    category: str = ""


@dataclass
class ScanResult:
    """Result of scanning a modpack for language files."""

    modpack_path: Path
    source_locale: str = "en_us"
    target_locale: str = "ko_kr"

    # Found files
    paired_files: list[LanguageFilePair] = field(default_factory=list)
    source_only_files: list[LanguageFilePair] = field(default_factory=list)
    target_only_files: list[Path] = field(default_factory=list)

    # All translation files (for ModpackLoader compatibility)
    translation_files: list[TranslationFile] = field(default_factory=list)

    # Statistics
    total_source_files: int = 0
    total_target_files: int = 0
    total_paired: int = 0

    @property
    def all_translation_pairs(self) -> list[LanguageFilePair]:
        """Get all files that need translation (paired + source-only)."""
        return self.paired_files + self.source_only_files


class ModpackScanner:
    """Scanner for Minecraft modpack language files.

    Scans a modpack directory structure to find translation files
    based on ModpackLoader logic from .etc/modpack/load.py.
    """

    def __init__(
        self,
        source_locale: str = "en_us",
        target_locale: str = "ko_kr",
        progress_callback: Callable[[str, int, int, str], None] | None = None,
    ) -> None:
        """Initialize the scanner.

        Args:
            source_locale: Source language locale code.
            target_locale: Target language locale code.
            progress_callback: Optional callback for progress updates.
        """
        self.source_locale = source_locale.lower()
        self.target_locale = target_locale.lower()
        self.progress_callback = progress_callback
        self.supported_extensions = BaseParser.get_supported_extensions()
        self.handler_registry = create_default_registry()
        self.max_scan_files = 1000000  # Safety limit to prevent OOM

        logger.info(
            "Initialized scanner: %s -> %s",
            self.source_locale,
            self.target_locale,
        )

    def scan(self, modpack_path: Path) -> ScanResult:
        """Scan a modpack for language files.

        Args:
            modpack_path: Path to the modpack root directory.

        Returns:
            Scan result with found files and pairs.
        """
        logger.info("Scanning modpack: %s", modpack_path)

        if not modpack_path.exists():
            logger.error("Modpack path does not exist: %s", modpack_path)
            return ScanResult(modpack_path=modpack_path)

        result = ScanResult(
            modpack_path=modpack_path,
            source_locale=self.source_locale,
            target_locale=self.target_locale,
        )

        # Scan all translation directories (like ModpackLoader)
        self._report_progress(
            "ZIP 파일 추출 중...", 0, 7, "압축 파일들을 추출하고 있습니다..."
        )
        self._extract_all_zip_files(modpack_path)

        self._report_progress(
            "Config 파일 스캔 중...", 1, 7, "config 폴더를 스캔하고 있습니다..."
        )
        self._load_config_files(modpack_path, result)

        self._report_progress(
            "FTB Quests 스캔 중...", 2, 7, "FTB Quests 파일을 스캔하고 있습니다..."
        )
        self._load_ftbquests_files(modpack_path, result)

        self._report_progress(
            "KubeJS 스캔 중...", 3, 7, "kubejs 폴더를 스캔하고 있습니다..."
        )
        self._load_kubejs_files(modpack_path, result)

        self._report_progress(
            "Patchouli 스캔 중...", 4, 7, "patchouli 폴더를 스캔하고 있습니다..."
        )
        self._load_patchouli_files(modpack_path, result)

        self._report_progress(
            "리소스팩 스캔 중...", 5, 7, "리소스팩/데이터팩을 스캔하고 있습니다..."
        )
        self._load_resourcepack_files(modpack_path, result)

        self._report_progress(
            "JAR 파일 스캔 중...", 6, 7, "JAR 파일들을 처리하고 있습니다..."
        )
        self._load_mod_files(modpack_path, result)

        # Build file pairs from translation files
        self._build_file_pairs(result)

        self._report_progress(
            "스캔 완료!",
            7,
            7,
            f"총 {len(result.translation_files)}개 파일 발견",
        )

        logger.info(
            "Scan complete: %d source, %d target, %d paired, total files: %d",
            result.total_source_files,
            result.total_target_files,
            result.total_paired,
            len(result.translation_files),
        )

        return result

    def _report_progress(
        self, stage: str, current: int, total: int, detail: str
    ) -> None:
        """Report progress if callback is set."""
        if self.progress_callback:
            self.progress_callback(stage, current, total, detail)

    @staticmethod
    def _normalize_glob_path(path: Path) -> str:
        """Normalize glob pattern path."""
        path_str = str(path).replace("\\", "/")
        parts = []
        for part in path_str.split("/"):
            if part.startswith("**") or part.startswith("*"):
                parts.append(part)
            else:
                parts.append(glob_escape(part))
        return "/".join(parts)

    def _is_translation_file(self, file_path: str) -> bool:
        """Check if file is a translation candidate."""
        # Check if any handler can handle this file
        path = Path(file_path)
        if self.handler_registry.get_handler(path):
            return True

        return False

    def _safe_iglob(self, pattern: str, recursive: bool = True):
        """Safely iterate over glob results."""
        try:
            return iglob(pattern, recursive=recursive)
        except Exception as e:
            logger.error("Glob failed for pattern %s: %s", pattern, e)
            return []

    def _extract_all_zip_files(self, modpack_path: Path) -> None:
        """Extract ZIP files from modpack."""
        pattern = self._normalize_glob_path(modpack_path / "**" / "*.zip")
        logger.info("Searching for ZIP files with pattern: %s", pattern)

        try:
            # Use iglob to avoid loading all paths into memory
            for zip_path in self._safe_iglob(str(pattern), recursive=True):
                try:
                    self._extract_zip_file(zip_path)
                except Exception as e:
                    logger.error("ZIP 파일 추출 실패 (%s): %s", zip_path, e)
        except Exception as e:
            logger.error("ZIP search failed: %s", e)

    def _extract_zip_file(self, zip_path: str) -> None:
        """Extract a single ZIP file if relevant."""
        try:
            zip_path_lower = zip_path.lower()

            # Only process paxi or openloader ZIPs
            if not ("paxi" in zip_path_lower or "openloader" in zip_path_lower):
                return

            extract_dir = zip_path + ".zip_extracted"
            if os.path.exists(extract_dir):
                return

            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                logger.info("ZIP 파일 추출 중: %s", zip_path)
                zf.extractall(extract_dir)
        except Exception as e:
            logger.error("Failed to extract zip file %s: %s", zip_path, e)

    def _load_config_files(self, modpack_path: Path, result: ScanResult) -> None:
        """Load translation files from config folder (excluding ftbquests)."""
        pattern = self._normalize_glob_path(modpack_path / "config" / "**" / "*.*")
        logger.info("Scanning config files: %s", pattern)

        try:
            for file_path in self._safe_iglob(str(pattern), recursive=True):
                if len(result.translation_files) >= self.max_scan_files:
                    logger.warning("Max file limit reached during config scan")
                    break

                try:
                    if "ftbquests" in file_path.lower():
                        continue
                    if self._is_translation_file(file_path):
                        result.translation_files.append(
                            TranslationFile(
                                input_path=file_path,
                                file_type="config",
                                category="Configuration",
                            )
                        )
                except Exception as e:
                    logger.debug("Failed to process config file %s: %s", file_path, e)
        except Exception as e:
            logger.error("Config scan failed: %s", e)

        count = len([f for f in result.translation_files if f.file_type == "config"])
        logger.info("config 폴더에서 %d개 파일 발견", count)

    def _load_ftbquests_files(self, modpack_path: Path, result: ScanResult) -> None:
        """Load translation files from ftbquests folder."""
        search_paths = [modpack_path / "config" / "ftbquests"]
        ftbquests_extensions = (".snbt", ".nbt")

        for path in search_paths:
            if not path.is_dir():
                continue
            pattern = self._normalize_glob_path(path / "**" / "*.*")
            logger.info("Scanning FTB Quests: %s", pattern)

            try:
                for file_path in self._safe_iglob(str(pattern), recursive=True):
                    if len(result.translation_files) >= self.max_scan_files:
                        logger.warning("Max file limit reached during FTB scan")
                        break

                    try:
                        # Only accept .snbt and .nbt files for ftbquests
                        ext = os.path.splitext(file_path)[1].lower()
                        if ext in ftbquests_extensions and self._is_translation_file(
                            file_path
                        ):
                            result.translation_files.append(
                                TranslationFile(
                                    input_path=file_path,
                                    file_type="ftbquests",
                                    category="FTB Quests",
                                )
                            )
                    except Exception as e:
                        logger.debug("Failed to process FTB file %s: %s", file_path, e)
            except Exception as e:
                logger.error("FTB Quests scan failed: %s", e)

        count = len([f for f in result.translation_files if f.file_type == "ftbquests"])
        logger.info("ftbquests 폴더에서 %d개 파일 발견 (.snbt, .nbt)", count)

    def _load_kubejs_files(self, modpack_path: Path, result: ScanResult) -> None:
        """Load translation files from kubejs folder."""
        pattern = self._normalize_glob_path(modpack_path / "kubejs" / "**" / "*.*")
        logger.info("Scanning KubeJS: %s", pattern)

        try:
            for file_path in self._safe_iglob(str(pattern), recursive=True):
                if len(result.translation_files) >= self.max_scan_files:
                    logger.warning("Max file limit reached during KubeJS scan")
                    break

                try:
                    if self._is_translation_file(file_path):
                        result.translation_files.append(
                            TranslationFile(
                                input_path=file_path,
                                file_type="kubejs",
                                category="KubeJS",
                            )
                        )
                except Exception as e:
                    logger.debug("Failed to process KubeJS file %s: %s", file_path, e)
        except Exception as e:
            logger.error("KubeJS scan failed: %s", e)

        count = len([f for f in result.translation_files if f.file_type == "kubejs"])
        logger.info("kubejs 폴더에서 %d개 파일 발견", count)

    def _load_patchouli_files(self, modpack_path: Path, result: ScanResult) -> None:
        """Load translation files from patchouli_books folder."""
        pattern = self._normalize_glob_path(
            modpack_path / "patchouli_books" / "**" / "*.*"
        )
        logger.info("Scanning Patchouli: %s", pattern)

        try:
            for file_path in self._safe_iglob(str(pattern), recursive=True):
                if len(result.translation_files) >= self.max_scan_files:
                    logger.warning("Max file limit reached during Patchouli scan")
                    break

                try:
                    if self._is_translation_file(file_path):
                        result.translation_files.append(
                            TranslationFile(
                                input_path=file_path,
                                file_type="patchouli",
                                category="Patchouli Books",
                            )
                        )
                except Exception as e:
                    logger.debug(
                        "Failed to process Patchouli file %s: %s", file_path, e
                    )
        except Exception as e:
            logger.error("Patchouli scan failed: %s", e)

        count = len([f for f in result.translation_files if f.file_type == "patchouli"])
        logger.info("patchouli 폴더에서 %d개 파일 발견", count)

    def _load_resourcepack_files(self, modpack_path: Path, result: ScanResult) -> None:
        """Load translation files from resourcepacks and datapacks folders."""
        for folder in ["resourcepacks", "datapacks"]:
            pattern = self._normalize_glob_path(modpack_path / folder / "**" / "*.*")
            logger.info("Scanning %s: %s", folder, pattern)

            try:
                for file_path in self._safe_iglob(str(pattern), recursive=True):
                    if len(result.translation_files) >= self.max_scan_files:
                        logger.warning("Max file limit reached during %s scan", folder)
                        break

                    try:
                        if self._is_translation_file(file_path):
                            result.translation_files.append(
                                TranslationFile(
                                    input_path=file_path,
                                    file_type=folder,
                                    category="Resource/Data Packs",
                                )
                            )
                    except Exception as e:
                        logger.debug(
                            "Failed to process resource pack file %s: %s", file_path, e
                        )
            except Exception as e:
                logger.error("%s scan failed: %s", folder, e)

        count = len(
            [
                f
                for f in result.translation_files
                if f.file_type in ["resourcepacks", "datapacks"]
            ]
        )
        logger.info("리소스팩/데이터팩에서 %d개 파일 발견", count)

    def _load_mod_files(self, modpack_path: Path, result: ScanResult) -> None:
        """Load translation files from mods JAR files."""
        pattern = self._normalize_glob_path(modpack_path / "mods" / "*.jar")
        logger.info("Scanning Mods: %s", pattern)

        try:
            jar_files_found = 0
            for jar_path in self._safe_iglob(str(pattern)):
                jar_files_found += 1
                try:
                    self._extract_from_jar(modpack_path, jar_path, result)
                except Exception as e:
                    logger.error("JAR 파일 처리 실패 (%s): %s", jar_path, e)

            count = len([f for f in result.translation_files if f.file_type == "mod"])
            logger.info(
                "mods 폴더에서 %d개 JAR 파일의 %d개 번역 파일 발견",
                jar_files_found,
                count,
            )
        except Exception as e:
            logger.error("Mod scan failed: %s", e)

    def _extract_from_jar(
        self, modpack_path: Path, jar_path: str, result: ScanResult
    ) -> None:
        """Extract translation files from a JAR file."""
        jar_name = os.path.basename(jar_path)
        mod_display_name = Path(jar_name).stem.split("-")[0].replace("_", " ").title()

        with zipfile.ZipFile(jar_path, "r") as zf:
            extract_dir = modpack_path / "mods" / "extracted" / jar_name
            extract_dir.mkdir(parents=True, exist_ok=True)

            for entry in zf.namelist():
                if self._should_extract_from_jar(entry):
                    try:
                        zf.extract(entry, extract_dir)
                        extracted_path = extract_dir / entry

                        if extracted_path.is_file() and self._is_translation_file(
                            str(extracted_path)
                        ):
                            result.translation_files.append(
                                TranslationFile(
                                    input_path=str(extracted_path),
                                    file_type="mod",
                                    jar_name=jar_name,
                                    category=f"Mod: {mod_display_name}",
                                )
                            )
                    except Exception as e:
                        logger.debug("JAR에서 파일 추출 실패 (%s): %s", entry, e)

    def _should_extract_from_jar(self, entry_path: str) -> bool:
        """Check if JAR entry should be extracted."""
        entry_lower = entry_path.lower()
        ext = os.path.splitext(entry_path)[1].lower()

        if ext not in self.supported_extensions:
            return False

        # Exclude non-translatable directories
        excluded_dirs = [
            "/recipes/",
            "/tags/",
            "/loot_tables/",
            "/advancements/",
            "/structures/",
            "/worldgen/",
            "/dimension/",
            "/dimension_type/",
            "\\recipes\\",
            "\\tags\\",
            "\\loot_tables\\",
            "\\advancements\\",
            "\\structures\\",
            "\\worldgen\\",
            "\\dimension\\",
            "\\dimension_type\\",
        ]

        for excluded in excluded_dirs:
            if excluded in entry_lower:
                return False

        return any(d.lower() in entry_lower for d in DIR_FILTER_WHITELIST)

    def _build_file_pairs(self, result: ScanResult) -> None:
        """Build file pairs from translation files."""
        source_files: dict[str, TranslationFile] = {}
        target_files: dict[str, TranslationFile] = {}

        # First pass: detect all locale codes in the files
        detected_locales: set[str] = set()
        locale_pattern = re.compile(r"[/\\]([a-z]{2}_[a-z]{2})(?:[/\\.]|$)")

        for tf in result.translation_files:
            path_lower = tf.input_path.replace("\\", "/").lower()
            matches = locale_pattern.findall(path_lower)
            detected_locales.update(matches)

        # Remove source and target locales from detected locales
        other_locales = detected_locales - {self.source_locale, self.target_locale}

        if other_locales:
            logger.info(
                "Detected other locales to filter out: %s",
                ", ".join(sorted(list[str](set[str](other_locales)))),
            )

        # Categorize by language
        for tf in result.translation_files:
            base_path = self._get_base_path(tf.input_path)
            path_lower = tf.input_path.replace("\\", "/").lower()

            # Skip files with other locale codes
            if any(locale in path_lower for locale in other_locales):
                logger.debug("Skipping other locale file: %s", tf.input_path)
                continue

            if self.source_locale in path_lower:
                tf.lang_type = "source"
                source_files[base_path] = tf
            elif self.target_locale in path_lower:
                tf.lang_type = "target"
                target_files[base_path] = tf
            else:
                # Default to source for files without locale in path
                # (e.g., config files without lang code)
                tf.lang_type = "source"
                source_files[base_path] = tf

        result.total_source_files = len(source_files)
        result.total_target_files = len(target_files)

        # Build pairs
        matched_targets: set[str] = set()

        for base_path, source_tf in source_files.items():
            source_path = Path(source_tf.input_path)
            namespace, mod_id = self._extract_namespace(source_path, source_tf)

            target_path: Path | None = None
            if base_path in target_files:
                target_path = Path(target_files[base_path].input_path)
                matched_targets.add(base_path)
                result.total_paired += 1

            pair = LanguageFilePair(
                source_path=source_path,
                target_path=target_path,
                namespace=namespace,
                mod_id=mod_id,
            )

            if target_path:
                result.paired_files.append(pair)
            else:
                result.source_only_files.append(pair)

        # Target-only files
        for base_path, target_tf in target_files.items():
            if base_path not in matched_targets:
                result.target_only_files.append(Path(target_tf.input_path))

    def _get_base_path(self, file_path: str) -> str:
        """Get base path without locale for matching."""
        path_normalized = file_path.replace("\\", "/").lower()
        # Remove locale codes to get base path
        # Use a more general pattern to match any locale code (xx_yy format)
        base_path = re.sub(
            r"[/\\]?([a-z]{2}_[a-z]{2})([/\\.])", r"/LOCALE\2", path_normalized
        )
        return base_path

    def _extract_namespace(
        self, file_path: Path, tf: TranslationFile
    ) -> tuple[str, str]:
        """Extract namespace and mod ID from a file path."""
        parts = file_path.parts
        mod_name = None

        # Try to extract clean mod name from jar if available
        if tf.file_type == "mod" and tf.jar_name:
            mod_name = self._clean_mod_name(tf.jar_name)

        # Look for 'assets' directory first (most reliable for resource packs)
        try:
            assets_idx = parts.index("assets")
            if assets_idx + 1 < len(parts):
                namespace = parts[assets_idx + 1]
                # If we have a mod name, use it as mod_id, otherwise use namespace
                return namespace, (mod_name if mod_name else namespace)
        except ValueError:
            pass

        # If no assets directory, but we have a mod name, use it
        if mod_name:
            return mod_name, mod_name

        # Fallback: use file type as namespace
        return tf.file_type, tf.file_type

    def _clean_mod_name(self, jar_name: str) -> str:
        """Extract clean mod name from jar filename."""
        name = Path(jar_name).stem

        # Simple regex to strip version numbers and loaders
        # Matches - or _ followed by (forge, fabric, quilt, neoforge, mc, v digit, or digit)
        # and everything after
        pattern = r"[-_](?:forge|fabric|quilt|neoforge|mc|v?\d).*"
        clean_name = re.sub(pattern, "", name, flags=re.IGNORECASE)

        return clean_name


def scan_modpack(
    modpack_path: Path | str,
    source_locale: str = "en_us",
    target_locale: str = "ko_kr",
    progress_callback: Callable[[str, int, int, str], None] | None = None,
) -> ScanResult:
    """Convenience function to scan a modpack.

    Args:
        modpack_path: Path to the modpack directory.
        source_locale: Source language locale.
        target_locale: Target language locale.
        progress_callback: Optional progress callback.

    Returns:
        Scan result.
    """
    scanner = ModpackScanner(source_locale, target_locale, progress_callback)
    return scanner.scan(Path(modpack_path))
