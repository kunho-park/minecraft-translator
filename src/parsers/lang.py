"""Parser for Minecraft .lang files (legacy key=value format)."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import aiofiles

from .base import BaseParser, DumpError, ParseError

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

logger = logging.getLogger(__name__)

PARSE_ESCAPES_DIRECTIVE = "#PARSE_ESCAPES"


class LangParser(BaseParser):
    """Parser for Minecraft 1.12 style .lang files.

    Handles key=value format with one entry per line.
    Properly processes JSON escape sequences for special characters.
    Preserves the ``#PARSE_ESCAPES`` directive on dump when the source
    file declared it (required by BetterQuesting and other 1.12.x mods
    that opt into escape handling explicitly).
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

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                logger.debug("Skipping line %d (no '=' found): %s", line_num, line[:50])
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

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

        directive_source = self.original_path if self.original_path else self.path
        has_parse_escapes = await self._has_parse_escapes_directive(directive_source)

        lines: list[str] = []
        if has_parse_escapes:
            lines.append(PARSE_ESCAPES_DIRECTIVE)
            lines.append("")

        for key, value in sorted(data.items()):
            if isinstance(value, str):
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

    @staticmethod
    async def _has_parse_escapes_directive(source: Path) -> bool:
        """Return True if the first non-blank line declares ``#PARSE_ESCAPES``.

        BetterQuesting and other older mods only honor escape sequences
        (``\\n``, ``\\u0027``, etc.) when this header is present, so the
        dump path must echo it back when the source file had one.
        """
        try:
            async with aiofiles.open(
                source, encoding="utf-8", errors="replace"
            ) as f:
                async for raw_line in f:
                    line = raw_line.strip()
                    if not line:
                        continue
                    return line.upper() == PARSE_ESCAPES_DIRECTIVE
        except (OSError, FileNotFoundError):
            return False
        return False
