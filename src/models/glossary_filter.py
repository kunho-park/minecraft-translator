"""Glossary filtering utilities for optimizing LLM context."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .glossary import FormattingRule, Glossary, ProperNounRule, TermRule

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

        # Combine all texts for searching (keep both original case and lowercase)
        combined_text_original = " ".join(texts.values())
        combined_text = combined_text_original.lower()

        # Filter term rules
        filtered_terms = GlossaryFilter._filter_term_rules(
            glossary.term_rules, combined_text
        )

        # Filter proper noun rules (now checks aliases too)
        filtered_nouns = GlossaryFilter._filter_proper_noun_rules(
            glossary.proper_noun_rules, combined_text
        )

        # Filter formatting rules based on keywords (global rules always included)
        filtered_rules = GlossaryFilter._filter_formatting_rules(
            glossary.formatting_rules, combined_text_original
        )

        filtered_glossary = Glossary(
            term_rules=filtered_terms,
            proper_noun_rules=filtered_nouns,
            formatting_rules=filtered_rules,
        )

        logger.debug(
            "Filtered glossary: %d/%d terms, %d/%d proper nouns, %d/%d formatting rules",
            len(filtered_terms),
            len(glossary.term_rules),
            len(filtered_nouns),
            len(glossary.proper_noun_rules),
            len(filtered_rules),
            len(glossary.formatting_rules),
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
            if not term.aliases:
                continue
            alternatives = "|".join(re.escape(a.lower()) for a in term.aliases)
            pattern = re.compile(r"\b(?:" + alternatives + r")\b")
            if pattern.search(combined_text):
                filtered.append(term)

        return filtered

    @staticmethod
    def _filter_proper_noun_rules(
        proper_noun_rules: list[ProperNounRule], combined_text: str
    ) -> list[ProperNounRule]:
        """Filter proper noun rules to only those that appear in text.

        Checks both source_like and aliases for matches.

        Args:
            proper_noun_rules: All proper noun rules
            combined_text: Combined text to search in (lowercase)

        Returns:
            Filtered proper noun rules
        """
        filtered = []

        for noun in proper_noun_rules:
            candidates = [noun.source_like, *noun.aliases]
            alternatives = "|".join(re.escape(c.lower()) for c in candidates)
            pattern = re.compile(r"\b(?:" + alternatives + r")\b")
            if pattern.search(combined_text):
                filtered.append(noun)

        return filtered

    @staticmethod
    def _filter_formatting_rules(
        formatting_rules: list[FormattingRule], combined_text: str
    ) -> list[FormattingRule]:
        """Filter formatting rules based on keywords.

        Global rules (is_global=True or empty keywords) are always included.
        Other rules are included only if at least one keyword matches the text.

        Args:
            formatting_rules: All formatting rules
            combined_text: Combined text to search in (original case preserved)

        Returns:
            Filtered formatting rules
        """
        filtered = []
        combined_lower = combined_text.lower()

        for rule in formatting_rules:
            # Global rules or rules without keywords are always included
            if rule.is_global or not rule.keywords:
                filtered.append(rule)
                continue

            # Check if any keyword appears in the text (case-insensitive)
            for keyword in rule.keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in combined_lower:
                    filtered.append(rule)
                    break

        return filtered
