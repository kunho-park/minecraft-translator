"""Parser for plain text files with chunking support."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import aiofiles

from .base import BaseParser, DumpError, ParseError

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

# Maximum characters per chunk
MAX_CHUNK_SIZE = 2000


class TextParser(BaseParser):
    """Parser for .txt files with chunking for large files.

    Splits content into manageable chunks at line boundaries
    to facilitate translation of large text files.
    """

    file_extensions = (".txt",)

    async def parse(self) -> Mapping[str, str]:
        """Parse a text file into chunks.

        Returns:
            A mapping of chunk keys to text content.

        Raises:
            ParseError: If the file cannot be read.
        """
        self._check_extension()
        logger.info("Parsing text file: %s", self.path)

        try:
            async with aiofiles.open(
                self.path, encoding="utf-8", errors="replace"
            ) as f:
                content = await f.read()
        except OSError as e:
            raise ParseError(self.path, f"Could not read file: {e}") from e

        result: dict[str, str] = {}
        lines = content.splitlines()
        chunk_idx = 0
        current_chunk: list[str] = []
        current_length = 0

        for line in lines:
            line_length = len(line)

            # Start new chunk if adding this line would exceed limit
            if current_chunk and current_length + line_length > MAX_CHUNK_SIZE:
                result[f"chunk_{chunk_idx}"] = "\n".join(current_chunk)
                chunk_idx += 1
                current_chunk = []
                current_length = 0

            current_chunk.append(line)
            current_length += line_length

        # Save last chunk
        if current_chunk:
            result[f"chunk_{chunk_idx}"] = "\n".join(current_chunk)

        logger.debug("Split %s into %d chunks", self.path, len(result))
        return result

    async def dump(self, data: Mapping[str, str]) -> None:
        """Write chunks back to a text file.

        Args:
            data: Mapping of chunk keys to text content.

        Raises:
            DumpError: If writing fails.
        """
        logger.info("Dumping text file: %s", self.path)

        # Sort keys to maintain order
        sorted_keys = self._sort_chunk_keys(data)

        result: list[str] = []
        for key in sorted_keys:
            result.append(str(data[key]))

        try:
            async with aiofiles.open(self.path, "w", encoding="utf-8") as f:
                await f.write("\n".join(result))
        except OSError as e:
            raise DumpError(self.path, f"Could not write file: {e}") from e

        logger.debug("Successfully wrote %d chunks to %s", len(data), self.path)

    @staticmethod
    def _sort_chunk_keys(data: Mapping[str, str]) -> list[str]:
        """Sort chunk keys in numeric order.

        Args:
            data: Mapping with chunk keys.

        Returns:
            List of sorted keys.
        """

        def get_sort_key(k: str) -> int:
            # Handle chunk_N format
            if k.startswith("chunk_"):
                try:
                    return int(k.split("_")[1])
                except (IndexError, ValueError):
                    pass
            # Handle legacy line_N format
            if k.startswith("line_"):
                try:
                    return int(k.split("_")[1])
                except (IndexError, ValueError):
                    pass
            return 999999

        return sorted(data.keys(), key=get_sort_key)
