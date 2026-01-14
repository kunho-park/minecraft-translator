"""JSON file parser with support for nested structures and comments."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

import aiofiles

from .base import BaseParser, DumpError, ParseError

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

# Type alias for JSON values (recursive)
type JSONValue = str | int | float | bool | None | list[JSONValue] | dict[str, JSONValue]


class JSONParser(BaseParser):
    """Parser for JSON format files.

    Handles JSON files with optional comments and nested structures.
    Flattens nested JSON to extract translatable strings.
    
    Only processes language files (files in /lang/ folders or with locale codes in name).
    """

    file_extensions = (".json",)

    # Pattern to remove single-line comments from JSON
    COMMENT_PATTERN = re.compile(r"^\s*//.*$|//.*$", re.MULTILINE)
    
    # Common Minecraft locale codes
    LOCALE_PATTERN = re.compile(
        r"(?:^|[/_-])"  # Start or separator
        r"(?:en|ko|ja|zh|de|fr|es|it|pt|ru|pl|nl|sv|no|da|fi|cs|tr|ar|th|vi|id|ms|tl|hi|uk|bg|ro|hr|hu|sk|sl|sr|lt|lv|et|el|he|fa|af)_"  # Language code
        r"(?:us|gb|kr|jp|cn|tw|de|fr|es|mx|br|it|pt|ru|pl|nl|se|no|dk|fi|cz|tr|ar|th|vn|id|my|ph|in|ua|bg|ro|hr|hu|sk|si|rs|lt|lv|ee|gr|il|ir|za)"  # Country code
        r"(?:[/_.\-]|$)",  # Separator or end
        re.IGNORECASE
    )

    async def parse(self) -> Mapping[str, str]:
        """Parse a JSON file and extract translatable strings.

        Returns:
            A flattened mapping of JSON paths to string values.

        Raises:
            ParseError: If the JSON file cannot be parsed.
        """
        self._check_extension()
        logger.info("Parsing JSON file: %s", self.path)

        try:
            async with aiofiles.open(self.path, encoding="utf-8", errors="replace") as f:
                content = await f.read()
        except OSError as e:
            raise ParseError(self.path, f"Could not read file: {e}") from e

        try:
            data = self._load_json_content(content)
        except ValueError as e:
            raise ParseError(self.path, str(e)) from e

        result = self._flatten_json(data)
        logger.debug("Extracted %d translatable strings from %s", len(result), self.path)
        return result

    async def dump(self, data: Mapping[str, str]) -> None:
        """Write translated data back to the JSON file.

        Args:
            data: Flattened mapping of JSON paths to translated values.

        Raises:
            DumpError: If writing fails.
        """
        logger.info("Dumping JSON file: %s", self.path)

        # Read original structure
        source_path = self.original_path if self.original_path else self.path
        try:
            async with aiofiles.open(source_path, encoding="utf-8", errors="replace") as f:
                original_content = await f.read()
        except OSError as e:
            raise DumpError(self.path, f"Could not read original file: {e}") from e

        try:
            original_data = self._load_json_content(original_content)
        except ValueError:
            logger.warning("Could not parse original JSON, using flat data directly")
            original_data = dict(data)

        # Update original structure with translated values
        updated_data = self._unflatten_json(original_data, data)

        # Write to file
        try:
            json_content = json.dumps(updated_data, ensure_ascii=False, indent=4)
            async with aiofiles.open(self.path, "w", encoding="utf-8") as f:
                await f.write(json_content)
        except OSError as e:
            raise DumpError(self.path, f"Could not write file: {e}") from e

        logger.debug("Successfully wrote %d entries to %s", len(data), self.path)

    def _load_json_content(self, content: str) -> dict[str, JSONValue]:
        """Parse JSON content with error recovery.

        Args:
            content: Raw JSON string content.

        Returns:
            Parsed JSON as a dictionary.

        Raises:
            ValueError: If JSON parsing fails after all recovery attempts.
        """
        # Normalize tabs to spaces
        content = re.sub(r"\t", " ", content)

        # Try parsing as-is first
        try:
            result = json.loads(content)
            if isinstance(result, dict):
                return result
            return {"_root": result}
        except json.JSONDecodeError:
            pass

        # Try removing trailing commas
        try:
            logger.debug("Attempting to fix trailing commas in JSON")
            fixed_content = re.sub(r'("(?:\\?.)*?")|,\s*([]}])', r"\1\2", content)
            result = json.loads(fixed_content)
            if isinstance(result, dict):
                return result
            return {"_root": result}
        except json.JSONDecodeError:
            pass

        # Try removing comments
        try:
            logger.debug("Attempting to remove comments from JSON")
            cleaned_content = self.COMMENT_PATTERN.sub("", content)
            result = json.loads(cleaned_content)
            if isinstance(result, dict):
                return result
            return {"_root": result}
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON syntax: {e}") from e

    def _flatten_json(
        self,
        data: JSONValue,
        prefix: str = "",
    ) -> dict[str, str]:
        """Flatten nested JSON structure to extract string values.

        Args:
            data: JSON data to flatten.
            prefix: Current key prefix for nested values.

        Returns:
            Flattened mapping of dot-notation keys to string values.
        """
        result: dict[str, str] = {}

        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, str):
                    result[new_key] = value
                elif isinstance(value, dict | list):
                    result.update(self._flatten_json(value, new_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_key = f"{prefix}[{i}]" if prefix else f"[{i}]"
                if isinstance(item, str):
                    result[new_key] = item
                elif isinstance(item, dict | list):
                    result.update(self._flatten_json(item, new_key))

        return result

    def _unflatten_json(
        self,
        original: dict[str, JSONValue],
        flat_data: Mapping[str, str],
    ) -> dict[str, JSONValue]:
        """Restore flattened data to original JSON structure.

        Args:
            original: Original JSON structure.
            flat_data: Flattened translated data.

        Returns:
            JSON structure with updated values.
        """
        # Deep copy the original
        result = json.loads(json.dumps(original))
        self._update_nested_values(result, flat_data)
        return result

    def _update_nested_values(
        self,
        data: JSONValue,
        flat_data: Mapping[str, str],
        prefix: str = "",
    ) -> None:
        """Recursively update nested values from flattened data.

        Args:
            data: JSON data to update (modified in place).
            flat_data: Flattened translated data.
            prefix: Current key prefix.
        """
        if isinstance(data, dict):
            for key, value in list(data.items()):
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, str):
                    if new_key in flat_data:
                        data[key] = flat_data[new_key]
                elif isinstance(value, dict | list):
                    self._update_nested_values(value, flat_data, new_key)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_key = f"{prefix}[{i}]" if prefix else f"[{i}]"
                if isinstance(item, str):
                    if new_key in flat_data:
                        data[i] = flat_data[new_key]
                elif isinstance(item, dict | list):
                    self._update_nested_values(item, flat_data, new_key)
