"""Glossary filtering utilities for optimizing LLM context."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .glossary import Glossary, ProperNounRule, TermRule

logger = logging.getLogger(__name__)


class GlossaryFilter:
    """Filter glossary to only relevant terms for given texts."""

    @staticmethod
    def filter_for_texts(glossary: Glossary, texts: dict[str, str]) -> Glossary:
        """Filter glossary to only include terms/rules relevant to given texts.

        Args:
            glossary: Full glossary
            texts: Dictionary of texts to translate

        Returns:
            Filtered glossary with only relevant terms
        """
        from .glossary import Glossary

        if not glossary:
            return Glossary()

        # Combine all texts for searching
        combined_text = " ".join(texts.values()).lower()

        # Filter term rules
        filtered_terms = GlossaryFilter._filter_term_rules(
            glossary.term_rules, combined_text
        )

        # Filter proper noun rules
        filtered_nouns = GlossaryFilter._filter_proper_noun_rules(
            glossary.proper_noun_rules, combined_text
        )

        # Formatting rules are always included (they're general style rules)
        filtered_rules = glossary.formatting_rules

        filtered_glossary = Glossary(
            term_rules=filtered_terms,
            proper_noun_rules=filtered_nouns,
            formatting_rules=filtered_rules,
        )

        logger.debug(
            "Filtered glossary: %d/%d terms, %d/%d proper nouns, %d formatting rules",
            len(filtered_terms),
            len(glossary.term_rules),
            len(filtered_nouns),
            len(glossary.proper_noun_rules),
            len(filtered_rules),
        )

        return filtered_glossary

    @staticmethod
    def _filter_term_rules(
        term_rules: list[TermRule], combined_text: str
    ) -> list[TermRule]:
        """Filter term rules to only those whose aliases appear in text.

        Args:
            term_rules: All term rules
            combined_text: Combined text to search in (lowercase)

        Returns:
            Filtered term rules
        """
        filtered = []

        for term in term_rules:
            # Check if any alias appears in the text
            for alias in term.aliases:
                # Use word boundaries to avoid partial matches
                pattern = r"\b" + re.escape(alias.lower()) + r"\b"
                if re.search(pattern, combined_text):
                    filtered.append(term)
                    break

        return filtered

    @staticmethod
    def _filter_proper_noun_rules(
        proper_noun_rules: list[ProperNounRule], combined_text: str
    ) -> list[ProperNounRule]:
        """Filter proper noun rules to only those that appear in text.

        Args:
            proper_noun_rules: All proper noun rules
            combined_text: Combined text to search in (lowercase)

        Returns:
            Filtered proper noun rules
        """
        filtered = []

        for noun in proper_noun_rules:
            # Check if source_like appears in text
            pattern = r"\b" + re.escape(noun.source_like.lower()) + r"\b"
            if re.search(pattern, combined_text):
                filtered.append(noun)

        return filtered
