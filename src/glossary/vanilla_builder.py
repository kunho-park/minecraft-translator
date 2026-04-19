"""Vanilla Minecraft glossary builder from official language files.

This module creates a base glossary from official Minecraft translations
that can be used as a foundation for all modpack translations.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import aiofiles

from ..models import Glossary, TermRule

logger = logging.getLogger(__name__)


class VanillaGlossaryBuilder:
    """Build glossary from vanilla Minecraft translation files."""

    def __init__(
        self,
        source_lang_file: Path,
        target_lang_file: Path,
        source_locale: str = "en_us",
        target_locale: str = "ko_kr",
    ) -> None:
        """Initialize vanilla glossary builder.

        Args:
            source_lang_file: Path to source language JSON (e.g., en_us.json)
            target_lang_file: Path to target language JSON (e.g., ko_kr.json)
            source_locale: Source locale code
            target_locale: Target locale code
        """
        self.source_lang_file = Path(source_lang_file)
        self.target_lang_file = Path(target_lang_file)
        self.source_locale = source_locale
        self.target_locale = target_locale

        logger.info(
            "Initialized VanillaGlossaryBuilder: %s -> %s",
            source_locale,
            target_locale,
        )

    async def build(self, output_path: Path | None = None) -> Glossary:
        """Build vanilla glossary from language files.

        Args:
            output_path: Optional path to save the glossary JSON.
                        If None, saves to src/glossary/vanilla_glossary_{source}_{target}.json

        Returns:
            Built glossary

        Raises:
            FileNotFoundError: If language files don't exist
            json.JSONDecodeError: If files are not valid JSON
        """
        logger.info("Building vanilla glossary...")

        source_data, target_data = await asyncio.gather(
            self._load_json(self.source_lang_file),
            self._load_json(self.target_lang_file),
        )

        logger.info(
            "Loaded %d source entries, %d target entries",
            len(source_data),
            len(target_data),
        )

        terms = self._extract_terms(source_data, target_data)

        glossary = Glossary(
            term_rules=terms,
            proper_noun_rules=[],
            formatting_rules=[],
        )

        logger.info("Built glossary with %d terms", len(terms))

        if output_path is None:
            output_path = self._get_default_output_path()

        await self._save_glossary(glossary, output_path)

        return glossary

    def _get_default_output_path(self) -> Path:
        """Get default output path based on language pair.

        Returns:
            Path to vanilla_glossaries/vanilla_glossary_{source}_{target}.json
        """
        filename = f"vanilla_glossary_{self.source_locale}_{self.target_locale}.json"

        current_dir = Path(__file__).parent
        vanilla_dir = current_dir / "vanilla_glossaries"
        vanilla_dir.mkdir(parents=True, exist_ok=True)

        return vanilla_dir / filename

    async def _load_json(self, file_path: Path) -> dict[str, str]:
        """Load JSON language file.

        Args:
            file_path: Path to JSON file

        Returns:
            Dictionary of key-value pairs

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Language file not found: {file_path}")

        async with aiofiles.open(file_path, encoding="utf-8") as f:
            raw = await f.read()
        data = json.loads(raw)

        if not isinstance(data, dict):
            raise ValueError(f"Expected dictionary in {file_path}")

        return data

    def _extract_terms(
        self, source_data: dict[str, str], target_data: dict[str, str]
    ) -> list[TermRule]:
        """Extract term rules from language data.

        Args:
            source_data: Source language data
            target_data: Target language data

        Returns:
            List of term rules
        """
        terms: list[TermRule] = []
        categories = {
            "block": "block",
            "item": "item",
            "entity": "entity",
            "effect": "effect",
            "enchantment": "effect",
            "biome": "biome",
            "gui": "ui",
            "menu": "ui",
            "advancements": "ui",
            "subtitles": "other",
            "death": "other",
            "commands": "other",
        }

        # Track added terms to avoid duplicates
        added_terms: set[str] = set()

        for key, source_text in source_data.items():
            # Skip if no matching translation
            if key not in target_data:
                continue

            target_text = target_data[key]

            # Skip empty or identical translations
            if not target_text or source_text == target_text:
                continue

            # Determine category from key
            category = "other"
            for prefix, cat in categories.items():
                if key.startswith(prefix):
                    category = cat
                    break

            # Skip if term already added (case-insensitive)
            target_lower = target_text.lower()
            if target_lower in added_terms:
                continue

            # Create term rule
            term = TermRule(
                term_ko=target_text,
                preferred_style="Official Minecraft translation",
                aliases=[source_text],
                category=category,
                notes=f"From vanilla: {key}",
            )
            terms.append(term)
            added_terms.add(target_lower)

        # Sort by category then by term
        terms.sort(key=lambda t: (t.category, t.term_ko))

        return terms

    async def _save_glossary(self, glossary: Glossary, output_path: Path) -> None:
        """Save glossary to JSON file.

        Args:
            glossary: Glossary to save
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        glossary_dict = {
            "term_rules": [
                {
                    "term_ko": term.term_ko,
                    "preferred_style": term.preferred_style,
                    "aliases": term.aliases,
                    "category": term.category,
                    "notes": term.notes,
                }
                for term in glossary.term_rules
            ],
            "proper_noun_rules": [],
            "formatting_rules": [],
        }
        serialized = json.dumps(glossary_dict, ensure_ascii=False, indent=2)

        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            await f.write(serialized)

        logger.info("Saved vanilla glossary to: %s", output_path)


async def main() -> None:
    """CLI entry point for building vanilla glossary."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build vanilla Minecraft glossary from official language files"
    )
    parser.add_argument(
        "--source",
        "-s",
        required=True,
        type=Path,
        help="Path to source language JSON file (e.g., en_us.json)",
    )
    parser.add_argument(
        "--target",
        "-t",
        required=True,
        type=Path,
        help="Path to target language JSON file (e.g., ko_kr.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output path for vanilla glossary JSON (default: src/glossary/vanilla_glossary_{source}_{target}.json)",
    )
    parser.add_argument(
        "--source-locale",
        default="en_us",
        help="Source locale code (default: en_us)",
    )
    parser.add_argument(
        "--target-locale",
        default="ko_kr",
        help="Target locale code (default: ko_kr)",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    try:
        builder = VanillaGlossaryBuilder(
            args.source,
            args.target,
            args.source_locale,
            args.target_locale,
        )
        glossary = await builder.build(args.output)

        output_path = args.output or builder._get_default_output_path()

        logger.info("Vanilla glossary created successfully")
        logger.info("Location: %s", output_path)
        logger.info(
            "Language pair: %s -> %s", args.source_locale, args.target_locale
        )
        logger.info("Terms: %d", len(glossary.term_rules))
        logger.info(
            "The glossary has been saved and will be automatically used "
            "for all translations with this language pair."
        )

    except Exception:
        logger.exception("Failed to build vanilla glossary")
        return


if __name__ == "__main__":
    asyncio.run(main())
