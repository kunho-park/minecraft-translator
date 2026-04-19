"""Example script for building vanilla glossary.

This shows how to build a vanilla Minecraft glossary from official language files.
"""

import asyncio
from collections import Counter
from pathlib import Path

from src.glossary.vanilla_builder import VanillaGlossaryBuilder


async def main() -> None:
    """Example usage of VanillaGlossaryBuilder."""
    source_file = Path("path/to/minecraft/lang/en_us.json")
    target_file = Path("path/to/minecraft/lang/ko_kr.json")

    print("Building vanilla glossary...")
    print(f"  Source: {source_file}")
    print(f"  Target: {target_file}")
    print()

    builder = VanillaGlossaryBuilder(
        source_lang_file=source_file,
        target_lang_file=target_file,
        source_locale="en_us",
        target_locale="ko_kr",
    )

    glossary = await builder.build()

    print("Glossary built successfully")
    print(f"   Total terms: {len(glossary.term_rules)}")
    print()

    categories = Counter(term.category for term in glossary.term_rules)
    print("Terms by category:")
    for category, count in categories.most_common():
        print(f"  {category}: {count}")
    print()

    print("Sample terms (first 10):")
    for i, term in enumerate(glossary.term_rules[:10], 1):
        alias = term.aliases[0] if term.aliases else "?"
        print(f"  {i}. {alias} -> {term.term_ko}")
        print(f"     Category: {term.category}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
