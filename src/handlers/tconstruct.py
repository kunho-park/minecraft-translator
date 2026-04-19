"""TConstruct content handler for extracting translatable strings from book files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from ..parsers import BaseParser
from .base import ContentHandler

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class TConstructHandler(ContentHandler):
    """Handler for Tinkers' Construct book JSON files.

    Extracts translatable strings from tconstruct/book:
    - text[].text, text[].title
    - title, text (as string)
    """

    name: ClassVar[str] = "tconstruct"
    priority: ClassVar[int] = 11

    path_patterns: ClassVar[tuple[str, ...]] = (
        "/tconstruct/book/",
        "\\tconstruct\\book\\",
    )

    extensions: ClassVar[tuple[str, ...]] = (".json",)

    TRANSLATABLE_KEYS: ClassVar[frozenset[str]] = frozenset({
        "text",
        "title",
    })

    def _should_translate_key(self, key: str) -> bool:
        """Check if a key should be translated."""
        parts = key.split(".")
        last_part = parts[-1].split("[")[0]
        return last_part in self.TRANSLATABLE_KEYS

    async def extract(self, path: Path) -> Mapping[str, str]:
        """Extract translatable strings from TConstruct file."""
        parser = BaseParser.create_parser(path)
        if parser is None:
            logger.warning("No parser found for: %s", path)
            return {}

        try:
            raw_data = await parser.parse()
            data = dict(raw_data)
        except Exception as e:
            logger.error("Failed to parse %s: %s", path, e)
            return {}

        entries: dict[str, str] = {}

        # Special handling for text array
        if "text" in data and isinstance(data["text"], list):
            for i, text_item in enumerate(data["text"]):
                if isinstance(text_item, dict):
                    for key, value in text_item.items():
                        if key in self.TRANSLATABLE_KEYS and isinstance(value, str) and value.strip():
                            entries[f"text[{i}].{key}"] = value

        # Extract other fields
        self._extract_from_dict(data, entries, "")

        logger.debug("Extracted %d entries from TConstruct file: %s", len(entries), path.name)
        return entries

    def _extract_from_dict(
        self,
        data: dict[str, object],
        entries: dict[str, str],
        prefix: str,
    ) -> None:
        """Extract from dict, handling text array specially."""
        for key, value in data.items():
            # Skip text array (already handled above)
            if key == "text" and isinstance(value, list):
                continue

            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, str):
                if self._should_translate_key(full_key) and value.strip():
                    entries[full_key] = value

            elif isinstance(value, dict):
                self._extract_from_dict(value, entries, full_key)

            elif isinstance(value, list):
                for i, item in enumerate(value):
                    item_key = f"{full_key}[{i}]"
                    if isinstance(item, dict):
                        self._extract_from_dict(item, entries, item_key)
                    elif isinstance(item, str) and self._should_translate_key(full_key):
                        entries[item_key] = item

    async def apply(
        self,
        path: Path,
        translations: Mapping[str, str],
        output_path: Path | None = None,
    ) -> None:
        """Apply translations to TConstruct file."""
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

        modified = False

        # Apply to text array
        if "text" in data and isinstance(data["text"], list):
            for i, text_item in enumerate(data["text"]):
                if isinstance(text_item, dict):
                    for key in list(text_item.keys()):
                        full_key = f"text[{i}].{key}"
                        if full_key in translations:
                            text_item[key] = translations[full_key]
                            modified = True

        # Apply to other fields
        if self._apply_recursive(data, translations, ""):
            modified = True

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
        """Apply translations recursively, skipping text array."""
        modified = False

        for key, value in list(data.items()):
            # Skip text array (already handled)
            if key == "text" and isinstance(value, list):
                continue

            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, str):
                if full_key in translations:
                    data[key] = translations[full_key]
                    modified = True

            elif isinstance(value, dict):
                if self._apply_recursive(value, translations, full_key):
                    modified = True

            elif isinstance(value, list):
                for i, item in enumerate(value):
                    item_key = f"{full_key}[{i}]"
                    if isinstance(item, str) and item_key in translations:
                        data[key][i] = translations[item_key]  # type: ignore[index]
                        modified = True
                    elif isinstance(item, dict):
                        if self._apply_recursive(item, translations, item_key):
                            modified = True

        return modified
