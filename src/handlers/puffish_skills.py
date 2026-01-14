"""PuffishSkills content handler for extracting translatable strings from skill files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from ..parsers import BaseParser
from .base import ContentHandler

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class PuffishSkillsHandler(ContentHandler):
    """Handler for PuffishSkills mod JSON files.

    Extracts translatable strings from puffish_skills/categories:
    - pages, text, title, subtitle, description
    Only processes definitions.json and category.json files.
    """

    name: ClassVar[str] = "puffish_skills"
    priority: ClassVar[int] = 11

    path_patterns: ClassVar[tuple[str, ...]] = (
        "/puffish_skills/categories/",
        "\\puffish_skills\\categories\\",
    )

    extensions: ClassVar[tuple[str, ...]] = (".json",)

    TRANSLATABLE_KEYS: ClassVar[frozenset[str]] = frozenset({
        "pages",
        "text",
        "title",
        "subtitle",
        "description",
    })

    # Only process these specific files
    ALLOWED_FILES: ClassVar[frozenset[str]] = frozenset({
        "definitions.json",
        "category.json",
    })

    def can_handle(self, path: Path) -> bool:
        """Check if this is an allowed PuffishSkills file."""
        if not super().can_handle(path):
            return False

        return path.name in self.ALLOWED_FILES

    def _should_translate_key(self, key: str) -> bool:
        """Check if a key should be translated."""
        parts = key.split(".")
        last_part = parts[-1].split("[")[0]
        return last_part in self.TRANSLATABLE_KEYS

    async def extract(self, path: Path) -> Mapping[str, str]:
        """Extract translatable strings from PuffishSkills file."""
        parser = BaseParser.create_parser(path)
        if parser is None:
            logger.warning("No parser found for: %s", path)
            return {}

        try:
            raw_data = await parser.parse()
        except Exception as e:
            logger.error("Failed to parse %s: %s", path, e)
            return {}

        entries: dict[str, str] = {}
        self._extract_recursive(dict(raw_data), entries, "")

        logger.debug(
            "Extracted %d entries from PuffishSkills file: %s",
            len(entries),
            path.name,
        )
        return entries

    def _extract_recursive(
        self,
        data: object,
        entries: dict[str, str],
        prefix: str,
    ) -> None:
        """Recursively extract translatable strings."""
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                self._extract_recursive(value, entries, full_key)

        elif isinstance(data, str):
            if self._should_translate_key(prefix) and data.strip():
                entries[prefix] = data

        elif isinstance(data, list):
            for i, item in enumerate(data):
                item_key = f"{prefix}[{i}]"
                self._extract_recursive(item, entries, item_key)

    async def apply(
        self,
        path: Path,
        translations: Mapping[str, str],
        output_path: Path | None = None,
    ) -> None:
        """Apply translations to PuffishSkills file."""
        target_path = output_path or path

        parser = BaseParser.create_parser(path)
        if parser is None:
            logger.warning("No parser found for: %s", path)
            return

        try:
            raw_data = await parser.parse()
            data = dict(raw_data)
        except Exception as e:
            logger.error("Failed to parse %s: %s", path, e)
            return

        modified = self._apply_recursive(data, translations, "")

        if not modified:
            logger.debug("No translations applied to: %s", path.name)
            return

        target_path.parent.mkdir(parents=True, exist_ok=True)

        output_parser = BaseParser.create_parser(target_path, original_path=path)
        if output_parser is None:
            logger.warning("No parser found for output: %s", target_path)
            return

        try:
            await output_parser.dump(data)
            logger.debug("Applied translations to: %s", target_path.name)
        except Exception as e:
            logger.error("Failed to write %s: %s", target_path, e)
            raise

    def _apply_recursive(
        self,
        data: dict[str, object],
        translations: Mapping[str, str],
        prefix: str,
    ) -> bool:
        """Recursively apply translations."""
        modified = False

        for key, value in list(data.items()):
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, str):
                if full_key in translations:
                    data[key] = translations[full_key]
                    modified = True

            elif isinstance(value, dict):
                if self._apply_recursive(value, translations, full_key):
                    modified = True

            elif isinstance(value, list):
                if self._apply_list(value, translations, full_key):
                    modified = True

        return modified

    def _apply_list(
        self,
        data: list[object],
        translations: Mapping[str, str],
        prefix: str,
    ) -> bool:
        """Apply translations to list items."""
        modified = False

        for i, item in enumerate(data):
            item_key = f"{prefix}[{i}]"

            if isinstance(item, str):
                if item_key in translations:
                    data[i] = translations[item_key]
                    modified = True

            elif isinstance(item, dict):
                if self._apply_recursive(item, translations, item_key):
                    modified = True

            elif isinstance(item, list):
                if self._apply_list(item, translations, item_key):
                    modified = True

        return modified
