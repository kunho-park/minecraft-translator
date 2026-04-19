"""Parser for Minecraft .lang files (legacy key=value format)."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import aiofiles

from .base import BaseParser, DumpError, ParseError

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class LangParser(BaseParser):
    """Parser for Minecraft 1.12 style .lang files.

    Handles key=value format with one entry per line.
    Properly processes JSON escape sequences for special characters.
    """

    file_extensions = (".lang",)

    async def parse(self) -> Mapping[str, str]:
        """Parse a .lang file and extract key-value pairs.

        Returns:
            A mapping of translation keys to values.

        Raises:
            ParseError: If the file cannot be read.
        """
        self._check_extension()
        logger.info("Parsing .lang file: %s", self.path)

        try:
            async with aiofiles.open(
                self.path, encoding="utf-8", errors="replace"
            ) as f:
                text = await f.read()
        except OSError as e:
            raise ParseError(self.path, f"Could not read file: {e}") from e

        mapping: dict[str, str] = {}

        for line_num, line in enumerate(text.splitlines(), start=1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Skip lines without =
            if "=" not in line:
                logger.debug("Skipping line %d (no '=' found): %s", line_num, line[:50])
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Process JSON escape sequences for special characters
            try:
                parsed_value = json.loads(f'"{value}"')
            except json.JSONDecodeError:
                logger.debug(
                    "Could not parse escape sequences on line %d, using raw value",
                    line_num,
                )
                parsed_value = value

            mapping[key] = parsed_value

        logger.debug("Extracted %d entries from %s", len(mapping), self.path)
        return mapping

    async def dump(self, data: Mapping[str, str]) -> None:
        """Write key-value pairs to a .lang file.

        Args:
            data: Mapping of translation keys to values.

        Raises:
            DumpError: If writing fails.
        """
        logger.info("Dumping .lang file: %s", self.path)

        lines: list[str] = []
        for key, value in sorted(data.items()):
            # Escape special characters using JSON encoding
            if isinstance(value, str):
                # json.dumps adds quotes, so we strip them
                escaped_value = json.dumps(value, ensure_ascii=False)[1:-1]
            else:
                escaped_value = str(value)
            lines.append(f"{key}={escaped_value}")

        try:
            async with aiofiles.open(self.path, "w", encoding="utf-8") as f:
                await f.write("\n".join(lines))
        except OSError as e:
            raise DumpError(self.path, f"Could not write file: {e}") from e

        logger.debug("Successfully wrote %d entries to %s", len(data), self.path)
