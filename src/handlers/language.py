"""Language file handler for standard formats."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from ..parsers import BaseParser
from .base import ContentHandler

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class LanguageHandler(ContentHandler):
    """Handler for standard language files (JSON, Lang).

    Strictly filters JSON files to only include those that match
    locale naming patterns (e.g. en_us.json) to avoid processing
    non-language JSON files.
    """

    name: ClassVar[str] = "language"
    priority: ClassVar[int] = 0  # Fallback priority

    def can_handle(self, path: Path) -> bool:
        """Check if file is a language file.

        Args:
            path: Path to the file.

        Returns:
            True if it looks like a language file.
        """
        suffix = path.suffix.lower()
        name = path.name.lower()

        # 1. JSON files: Must look like locale (e.g., en_us.json, ko_kr.json)
        if suffix == ".json":
            # Match strictly: xx_xx.json only (2 letters each)
            return bool(re.match(r"^[a-z]{2}_[a-z]{2}\.json$", name))

        return False

    async def extract(self, path: Path) -> Mapping[str, str]:
        """Extract translatable strings from the file.

        Args:
            path: Path to the file.

        Returns:
            Mapping of keys to translatable text.
        """
        # Delegate to parser
        parser = BaseParser.create_parser(path)
        if not parser:
            return {}
        try:
            return dict(await parser.parse())
        except Exception as e:
            logger.error("Failed to extract %s: %s", path, e)
            return {}

    async def apply(
        self,
        path: Path,
        translations: Mapping[str, str],
        output_path: Path | None = None,
    ) -> None:
        """Apply translations to the file.

        Args:
            path: Path to the original file.
            translations: Mapping of keys to translated text.
            output_path: Optional output path (if different from original).
        """
        target_path = output_path or path
        parser = BaseParser.create_parser(target_path, original_path=path)
        if not parser:
            return

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            await parser.dump(translations)
        except Exception as e:
            logger.error("Failed to apply %s: %s", target_path, e)
            raise
