"""FTBQuests content handler for extracting translatable strings from quest files."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from ..parsers import BaseParser
from .base import ContentHandler

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class FTBQuestsHandler(ContentHandler):
    """Handler for FTBQuests SNBT/NBT files.

    Extracts only translatable keys from FTBQuests files:
    - title, name: Quest/chapter names
    - description, text: Descriptions
    - subtitle: Subtitles
    - Lore, Name: Item display components
    """

    name: ClassVar[str] = "ftbquests"
    priority: ClassVar[int] = 15  # Higher than parser, lower than kubejs

    path_patterns: ClassVar[tuple[str, ...]] = (
        "/ftbquests/",
        "\\ftbquests\\",
        "/config/ftbquests/",
        "\\config\\ftbquests\\",
    )

    extensions: ClassVar[tuple[str, ...]] = (".snbt", ".nbt")

    # Keys that should be translated
    TRANSLATABLE_KEYS: ClassVar[frozenset[str]] = frozenset(
        {
            "title",
            "name",
            "description",
            "text",
            "subtitle",
            "quest_desc",
            "quest_subtitle",
            "Lore",
            "Name",
        }
    )

    def can_handle(self, path: Path) -> bool:
        """Check if this is an FTBQuests file.

        Args:
            path: Path to check.

        Returns:
            True if this is an FTBQuests file.
        """
        if path.suffix.lower() not in self.extensions:
            return False

        path_str = str(path).replace("\\", "/").lower()
        return any(p.lower().replace("\\", "/") in path_str for p in self.path_patterns)

    def _should_translate_key(self, key: str) -> bool:
        """Check if a key should be translated.

        Args:
            key: Full key path (e.g., "quests[0].title").

        Returns:
            True if the key should be translated.
        """
        # Get the last part of the key
        parts = key.split(".")
        last_part = parts[-1]

        # Remove array index if present
        if "[" in last_part:
            last_part = last_part.split("[")[0]

        return last_part in self.TRANSLATABLE_KEYS

    def _is_json_structure(self, text: str) -> bool:
        """Check if text is a complete JSON structure (object or array).

        Args:
            text: Text to check.

        Returns:
            True if it's a JSON structure that should not be translated.
        """
        if not text:
            return False
        
        # Check if entire text is wrapped in {} or []
        if (text.startswith("{") and text.endswith("}")) or \
           (text.startswith("[") and text.endswith("]")):
            try:
                json.loads(text)
                return True
            except (json.JSONDecodeError, ValueError):
                pass
        return False

    def _is_json_text(self, text: str) -> bool:
        """Check if text is a JSON text component.

        Args:
            text: Text to check.

        Returns:
            True if it's a JSON text component.
        """
        try:
            if text.startswith('{"') and text.endswith('"}'):
                json.loads(text)
                return True
        except (json.JSONDecodeError, ValueError):
            pass
        return False

    def _extract_json_text(self, json_str: str) -> str:
        """Extract 'text' field from JSON text component.

        Args:
            json_str: JSON string.

        Returns:
            Text content or empty string.
        """
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "text" in data:
                return str(data["text"])
        except (json.JSONDecodeError, ValueError):
            pass
        return ""

    def _rebuild_json_text(self, json_str: str, new_text: str) -> str:
        """Rebuild JSON text component with new text.

        Args:
            json_str: Original JSON string.
            new_text: New text content.

        Returns:
            Updated JSON string.
        """
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "text" in data:
                data["text"] = new_text
                return json.dumps(data, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            pass
        return json_str

    async def extract(self, path: Path) -> Mapping[str, str]:
        """Extract translatable strings from FTBQuests file.

        Args:
            path: Path to the file.

        Returns:
            Mapping of keys to translatable text.
        """
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
            "Extracted %d entries from FTBQuests file: %s", len(entries), path.name
        )
        return entries

    def _extract_recursive(
        self,
        data: dict[str, object] | list[object] | str,
        entries: dict[str, str],
        prefix: str,
    ) -> None:
        """Recursively extract translatable strings.

        Args:
            data: Data to extract from.
            entries: Dictionary to store entries.
            prefix: Current key prefix.
        """
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
        """Extract value if it's translatable.

        Args:
            key: Full key path.
            value: Value to check.
            entries: Dictionary to store entries.
        """
        if isinstance(value, str):
            if self._should_translate_key(key) and value.strip():
                # Skip if entire text is a JSON structure (starts with { or [)
                stripped = value.strip()
                if self._is_json_structure(stripped):
                    logger.debug("Skipping JSON structure for key %s: %s", key, stripped[:100])
                    return
                
                # Handle JSON text components
                if self._is_json_text(value):
                    json_text = self._extract_json_text(value)
                    if json_text.strip():
                        # Store with marker for JSON reconstruction
                        entries[f"{key}::json"] = json_text
                else:
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
        """Apply translations to FTBQuests file.

        Args:
            path: Path to the original file.
            translations: Mapping of keys to translated text.
            output_path: Optional output path.
        """
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

        # Apply translations
        modified = self._apply_recursive(data, translations, "")

        if not modified:
            logger.debug("No translations applied to: %s", path.name)
            return

        # Write output
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
        """Recursively apply translations.

        Args:
            data: Data to modify.
            translations: Translations to apply.
            prefix: Current key prefix.

        Returns:
            True if any translation was applied.
        """
        modified = False

        for key, value in list(data.items()):
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, str):
                # Check for JSON marker
                json_key = f"{full_key}::json"
                if json_key in translations:
                    # Rebuild JSON with translated text
                    data[key] = self._rebuild_json_text(value, translations[json_key])
                    modified = True
                elif full_key in translations:
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
        """Apply translations to list items.

        Args:
            data: List to modify.
            translations: Translations to apply.
            prefix: Current key prefix.

        Returns:
            True if any translation was applied.
        """
        modified = False

        for i, item in enumerate(data):
            item_key = f"{prefix}[{i}]"

            if isinstance(item, str):
                json_key = f"{item_key}::json"
                if json_key in translations:
                    data[i] = self._rebuild_json_text(item, translations[json_key])
                    modified = True
                elif item_key in translations:
                    data[i] = translations[item_key]
                    modified = True

            elif isinstance(item, dict):
                if self._apply_recursive(item, translations, item_key):
                    modified = True

            elif isinstance(item, list):
                if self._apply_list(item, translations, item_key):
                    modified = True

        return modified
