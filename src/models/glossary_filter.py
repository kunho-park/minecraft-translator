"""Glossary filtering utilities for optimizing LLM context."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .glossary import FormattingRule, Glossary, ProperNounRule, TermRule

logger = logging.getLogger(__name__)

_SINGLE_WORD_RE = re.compile(r"\w+$")


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

        combined_text_original = " ".join(texts.values())
        combined_text = combined_text_original.lower()

        word_set = set(re.findall(r"\w+", combined_text))

        filtered_terms = GlossaryFilter._filter_term_rules(
            glossary.term_rules, combined_text, word_set
        )

        filtered_nouns = GlossaryFilter._filter_proper_noun_rules(
            glossary.proper_noun_rules, combined_text, word_set
        )

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
        term_rules: list[TermRule],
        combined_text: str,
        word_set: set[str],
    ) -> list[TermRule]:
        """Filter term rules using word-set lookup + single combined regex.

        Single-word aliases are checked via O(1) set membership.
        Multi-word aliases that pass a cheap substring pre-filter are
        verified in a single compiled regex scan.
        """
        if not term_rules:
            return []

        matched_indices: set[int] = set()
        multi_word_map: dict[str, list[int]] = {}

        for i, term in enumerate(term_rules):
            if not term.aliases:
                continue

            for alias in term.aliases:
                lowered = alias.lower()

                if _SINGLE_WORD_RE.fullmatch(lowered):
                    if lowered in word_set:
                        matched_indices.add(i)
                        break
                else:
                    if lowered in combined_text:
                        multi_word_map.setdefault(lowered, []).append(i)

        if multi_word_map:
            sorted_aliases = sorted(multi_word_map, key=len, reverse=True)
            pattern = re.compile(
                r"\b(?:" + "|".join(re.escape(a) for a in sorted_aliases) + r")\b"
            )
            for m in pattern.finditer(combined_text):
                hit = m.group()
                if hit in multi_word_map:
                    matched_indices.update(multi_word_map[hit])

        return [term_rules[i] for i in sorted(matched_indices)]

    @staticmethod
    def _filter_proper_noun_rules(
        proper_noun_rules: list[ProperNounRule],
        combined_text: str,
        word_set: set[str],
    ) -> list[ProperNounRule]:
        """Filter proper noun rules using word-set lookup + single combined regex.

        Checks both source_like and aliases.
        """
        if not proper_noun_rules:
            return []

        matched_indices: set[int] = set()
        multi_word_map: dict[str, list[int]] = {}

        for i, noun in enumerate(proper_noun_rules):
            candidates = [noun.source_like.lower()] + [a.lower() for a in noun.aliases]

            found = False
            for c in candidates:
                if _SINGLE_WORD_RE.fullmatch(c):
                    if c in word_set:
                        matched_indices.add(i)
                        found = True
                        break
                else:
                    if c in combined_text:
                        multi_word_map.setdefault(c, []).append(i)

            if found:
                continue

        if multi_word_map:
            sorted_aliases = sorted(multi_word_map, key=len, reverse=True)
            pattern = re.compile(
                r"\b(?:" + "|".join(re.escape(a) for a in sorted_aliases) + r")\b"
            )
            for m in pattern.finditer(combined_text):
                hit = m.group()
                if hit in multi_word_map:
                    matched_indices.update(multi_word_map[hit])

        return [proper_noun_rules[i] for i in sorted(matched_indices)]

    @staticmethod
    def _filter_formatting_rules(
        formatting_rules: list[FormattingRule], combined_text: str
    ) -> list[FormattingRule]:
        """Filter formatting rules based on keywords.

        Global rules (is_global=True or empty keywords) are always included.
        Other rules are included only if at least one keyword matches the text.
        """
        if not formatting_rules:
            return []

        filtered = []
        combined_lower = combined_text.lower()

        for rule in formatting_rules:
            if rule.is_global or not rule.keywords:
                filtered.append(rule)
                continue

            if any(kw.lower() in combined_lower for kw in rule.keywords):
                filtered.append(rule)

        return filtered
