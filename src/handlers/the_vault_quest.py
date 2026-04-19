"""The Vault Quest content handler for extracting translatable strings from quest files."""

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


class TheVaultQuestHandler(ContentHandler):
    """Handler for The Vault Quest JSON files.

    Extracts translatable keys from The Vault quest files:
    - name: Quest name
    - descriptionData.description[].text: Quest description text
    """

    name: ClassVar[str] = "the_vault_quest"
    priority: ClassVar[int] = 10  # Standard priority

    path_patterns: ClassVar[tuple[str, ...]] = (
        "/config/the_vault/quest/",
        "\\config\\the_vault\\quest\\",
    )

    extensions: ClassVar[tuple[str, ...]] = (".json",)

    def can_handle(self, path: Path) -> bool:
        """Check if this is a The Vault quest file.

        Args:
            path: Path to check.

        Returns:
            True if this is a The Vault quest file.
        """
        if path.suffix.lower() not in self.extensions:
            return False

        path_str = str(path).replace("\\", "/").lower()
        return any(p.lower().replace("\\", "/") in path_str for p in self.path_patterns)

    async def extract(self, path: Path) -> Mapping[str, str]:
        """Extract translatable strings from The Vault quest file.

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
            # Get flattened data directly from parser
            raw_data = await parser.parse()
        except Exception as e:
            logger.error("Failed to parse %s: %s", path, e)
            return {}

        entries: dict[str, str] = {}

        # Regex for Quest name: quests[0].name
        name_pattern = re.compile(r"^quests\[\d+\]\.name$")
        # Regex for Description text: quests[0].descriptionData.description[0].text
        desc_pattern = re.compile(
            r"^quests\[\d+\]\.descriptionData\.description\[\d+\]\.text$"
        )

        for key, value in raw_data.items():
            if name_pattern.match(key) or desc_pattern.match(key):
                entries[key] = value

        logger.debug(
            "Extracted %d entries from The Vault quest file: %s",
            len(entries),
            path.name,
        )
        return entries

    async def apply(
        self,
        path: Path,
        translations: Mapping[str, str],
        output_path: Path | None = None,
    ) -> None:
        """Apply translations to The Vault quest file.

        Args:
            path: Path to the original file.
            translations: Mapping of keys to translated text.
            output_path: Optional output path.
        """
        target_path = output_path or path

        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        output_parser = BaseParser.create_parser(target_path, original_path=path)
        if output_parser is None:
            logger.warning("No parser found for output: %s", target_path)
            return

        try:
            # Use BaseParser.dump to handle unflattening
            await output_parser.dump(translations)
            logger.debug("Applied translations to: %s", target_path.name)
        except Exception as e:
            logger.error("Failed to write %s: %s", target_path, e)
            raise
