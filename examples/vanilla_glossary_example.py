"""Example script for building vanilla glossary.

This shows how to build a vanilla Minecraft glossary from official language files.
"""

from pathlib import Path

from src.glossary.vanilla_builder import VanillaGlossaryBuilder


def main() -> None:
    """Example usage of VanillaGlossaryBuilder."""
    # Example paths (adjust to your actual file locations)
    source_file = Path("path/to/minecraft/lang/en_us.json")
    target_file = Path("path/to/minecraft/lang/ko_kr.json")
    
    # Output path is optional - will auto-generate based on language pair
    # e.g., src/glossary/vanilla_glossary_en_us_ko_kr.json

    print("Building vanilla glossary...")
    print(f"  Source: {source_file}")
    print(f"  Target: {target_file}")
    print()

    # Create builder
    builder = VanillaGlossaryBuilder(
        source_lang_file=source_file,
        target_lang_file=target_file,
        source_locale="en_us",
        target_locale="ko_kr",
    )

    # Build glossary (output path will be auto-generated)
    glossary = builder.build()

    # Print statistics
    print(f"✅ Glossary built successfully!")
    print(f"   Total terms: {len(glossary.term_rules)}")
    print()

    # Show term breakdown by category
    from collections import Counter

    categories = Counter(term.category for term in glossary.term_rules)
    print("Terms by category:")
    for category, count in categories.most_common():
        print(f"  {category}: {count}")
    print()

    # Show sample terms
    print("Sample terms (first 10):")
    for i, term in enumerate(glossary.term_rules[:10], 1):
        print(f"  {i}. {term.aliases[0] if term.aliases else '?'} → {term.term_ko}")
        print(f"     Category: {term.category}")
        print()


if __name__ == "__main__":
    main()
