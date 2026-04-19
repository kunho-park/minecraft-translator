"""Parser for JavaScript/TypeScript files."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import aiofiles

from .base import BaseParser, DumpError, ParseError

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class JSParser(BaseParser):
    """Parser for JavaScript/TypeScript files.

    Stores the entire file content under a single "content" key
    for safe translation handling.
    """

    file_extensions = (".js", ".ts")

    async def parse(self) -> Mapping[str, str]:
        """Parse a JS/TS file.

        Returns:
            A mapping with the file content under "content" key.

        Raises:
            ParseError: If the file cannot be read.
        """
        self._check_extension()
        logger.info("Parsing JS/TS file: %s", self.path)

        try:
            async with aiofiles.open(
                self.path, encoding="utf-8", errors="replace"
            ) as f:
                content = await f.read()
        except OSError as e:
            raise ParseError(self.path, f"Could not read file: {e}") from e

        logger.debug("Read %d characters from %s", len(content), self.path)
        return {"content": content}

    async def dump(self, data: Mapping[str, str]) -> None:
        """Write content back to a JS/TS file.

        Args:
            data: Mapping with "content" key containing file content.

        Raises:
            DumpError: If writing fails.
        """
        logger.info("Dumping JS/TS file: %s", self.path)

        content = data.get("content", "")

        try:
            async with aiofiles.open(self.path, "w", encoding="utf-8") as f:
                await f.write(content)
        except OSError as e:
            raise DumpError(self.path, f"Could not write file: {e}") from e

        logger.debug("Successfully wrote %d characters to %s", len(content), self.path)
