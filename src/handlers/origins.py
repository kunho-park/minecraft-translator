"""Origins content handler for extracting translatable strings from origin files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from ..parsers import BaseParser
from .base import ContentHandler

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class OriginsHandler(ContentHandler):
    """Handler for Origins mod data files.

    Extracts translatable strings from origins and powers JSON files:
    - text, title, subtitle, description, name
    """

    name: ClassVar[str] = "origins"
    priority: ClassVar[int] = 12

    path_patterns: ClassVar[tuple[str, ...]] = (
        "/origins/",
        "\\origins\\",
        "/powers/",
        "\\powers\\",
    )

    extensions: ClassVar[tuple[str, ...]] = (".json",)

    TRANSLATABLE_KEYS: ClassVar[frozenset[str]] = frozenset(
        {
            "text",
            "title",
            "subtitle",
            "description",
            "name",
        }
    )

    def _should_translate_key(self, key: str) -> bool:
        """Check if a key should be translated."""
        parts = key.split(".")
        last_part = parts[-1].split("[")[0]
        return last_part in self.TRANSLATABLE_KEYS

    async def extract(self, path: Path) -> Mapping[str, str]:
        """Extract translatable strings from Origins file."""
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
            "Extracted %d entries from Origins file: %s", len(entries), path.name
        )
        return entries

    def _extract_recursive(
        self,
        data: dict[str, object] | list[object] | str,
        entries: dict[str, str],
        prefix: str,
    ) -> None:
        """Recursively extract translatable strings."""
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                self._extract_value(full_key, value, entries)

        elif isinstance(data, list):
            for i, item in enumerate(data):
                full_key = f"{prefix}[{i}]"
                self._extract_value(full_key, item, entries)

    def _extract_value(
        self,
        key: str,
        value: object,
        entries: dict[str, str],
    ) -> None:
        """Extract value if it's translatable."""
        if isinstance(value, str):
            if self._should_translate_key(key) and value.strip():
                entries[key] = value

        elif isinstance(value, dict):
            self._extract_recursive(value, entries, key)

        elif isinstance(value, list):
            for i, item in enumerate(value):
                item_key = f"{key}[{i}]"
                self._extract_value(item_key, item, entries)

    async def apply(
        self,
        path: Path,
        translations: Mapping[str, str],
        output_path: Path | None = None,
    ) -> None:
        """Apply translations to Origins file."""
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
