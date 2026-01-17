"""The Vault Quest content handler for extracting translatable strings from quest files."""

from __future__ import annotations

import logging
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
            raw_data = await parser.parse()
        except Exception as e:
            logger.error("Failed to parse %s: %s", path, e)
            return {}

        entries: dict[str, str] = {}
        
        # Ensure it's a dict and has "quests" list
        if isinstance(raw_data, dict) and "quests" in raw_data and isinstance(raw_data["quests"], list):
            for i, quest in enumerate(raw_data["quests"]):
                if not isinstance(quest, dict):
                    continue

                # Extract quest name
                if "name" in quest and isinstance(quest["name"], str):
                    entries[f"quests[{i}].name"] = quest["name"]

                # Extract description
                if "descriptionData" in quest and isinstance(quest["descriptionData"], dict):
                    desc_data = quest["descriptionData"]
                    if "description" in desc_data and isinstance(desc_data["description"], list):
                        for j, desc_part in enumerate(desc_data["description"]):
                            if isinstance(desc_part, dict) and "text" in desc_part and isinstance(desc_part["text"], str):
                                entries[f"quests[{i}].descriptionData.description[{j}].text"] = desc_part["text"]

        logger.debug(
            "Extracted %d entries from The Vault quest file: %s", len(entries), path.name
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

        parser = BaseParser.create_parser(path)
        if parser is None:
            logger.warning("No parser found for: %s", path)
            return

        try:
            raw_data = await parser.parse()
            data = dict(raw_data) # Make a copy/ensure it's dict
        except Exception as e:
            logger.error("Failed to parse %s: %s", path, e)
            return

        modified = False

        if isinstance(data, dict) and "quests" in data and isinstance(data["quests"], list):
            for i, quest in enumerate(data["quests"]):
                if not isinstance(quest, dict):
                    continue

                # Apply quest name
                name_key = f"quests[{i}].name"
                if name_key in translations:
                    quest["name"] = translations[name_key]
                    modified = True

                # Apply description
                if "descriptionData" in quest and isinstance(quest["descriptionData"], dict):
                    desc_data = quest["descriptionData"]
                    if "description" in desc_data and isinstance(desc_data["description"], list):
                        for j, desc_part in enumerate(desc_data["description"]):
                            if not isinstance(desc_part, dict):
                                continue
                            
                            text_key = f"quests[{i}].descriptionData.description[{j}].text"
                            if text_key in translations:
                                desc_part["text"] = translations[text_key]
                                modified = True

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
