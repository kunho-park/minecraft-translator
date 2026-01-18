"""Pydantic models for translation glossary."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TermRule(BaseModel):
    """A terminology rule for consistent translation.

    Defines how a specific game term should be translated,
    including style preferences and alternative forms.
    """

    term_ko: str = Field(
        ...,
        description="Korean translation of the term",
        examples=["마법 부여대", "주괴"],
    )
    preferred_style: str = Field(
        ...,
        description="Style guide for the term",
        examples=["띄어쓰기 유지", "한글 표기"],
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="English aliases or original terms",
        examples=[["Enchanting Table"], ["Ingot", "ingots"]],
    )
    category: Literal["item", "block", "ui", "entity", "effect", "biome", "other"] = (
        Field(
            default="other",
            description="Category of the term",
        )
    )
    notes: str = Field(
        default="",
        description="Additional notes about the term",
    )

    @field_validator("aliases")
    @classmethod
    def sort_aliases(cls, v: list[str]) -> list[str]:
        """Sort aliases for consistent deduplication."""
        return sorted(list(set(v)))


class ProperNounRule(BaseModel):
    """A proper noun translation rule.

    Defines consistent translations for proper nouns
    like dimension names, mod names, etc.
    """

    source_like: str = Field(
        ...,
        description="Original English proper noun",
        examples=["Nether", "Ender", "Mekanism"],
    )
    preferred_ko: str = Field(
        ...,
        description="Preferred Korean translation",
        examples=["네더", "엔더", "메카니즘"],
    )
    notes: str = Field(
        default="",
        description="Additional notes about usage",
    )


class FormattingRule(BaseModel):
    """A formatting/style rule for translations.

    Defines general style guidelines for the translation,
    such as honorifics, punctuation, etc.
    """

    rule_name: str = Field(
        ...,
        description="Name of the formatting rule",
        examples=["존댓말", "조사 처리", "따옴표"],
    )
    description: str = Field(
        ...,
        description="Description of the rule",
    )
    examples: list[str] = Field(
        default_factory=list,
        description="Example applications of the rule",
    )


class Glossary(BaseModel):
    """Complete glossary for translation consistency.

    Contains all rules needed for consistent translation
    of a Minecraft modpack.
    """

    version: str = Field(
        default="1.0",
        description="Glossary schema version",
    )
    locale_source: str = Field(
        default="en_us",
        description="Source language locale",
    )
    locale_target: str = Field(
        default="ko_kr",
        description="Target language locale",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Glossary creation timestamp",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last update timestamp",
    )
    term_rules: list[TermRule] = Field(
        default_factory=list,
        description="Terminology translation rules",
    )
    proper_noun_rules: list[ProperNounRule] = Field(
        default_factory=list,
        description="Proper noun translation rules",
    )
    formatting_rules: list[FormattingRule] = Field(
        default_factory=list,
        description="Formatting and style rules",
    )

    def merge_with(self, other: Glossary) -> Glossary:
        """Merge another glossary into this one.

        Args:
            other: Glossary to merge.

        Returns:
            New merged glossary.
        """
        # Create sets of existing items for deduplication
        existing_terms = {(t.term_ko, tuple(t.aliases)) for t in self.term_rules}
        existing_nouns = {
            (n.source_like, n.preferred_ko) for n in self.proper_noun_rules
        }
        existing_rules = {r.rule_name for r in self.formatting_rules}

        # Lists for new items
        new_terms: list[TermRule] = []
        new_nouns: list[ProperNounRule] = []
        new_rules: list[FormattingRule] = []

        # Add new items with deduplication
        for t in other.term_rules:
            key = (t.term_ko, tuple(t.aliases))
            if key not in existing_terms:
                existing_terms.add(key)
                new_terms.append(t)

        for n in other.proper_noun_rules:
            key = (n.source_like, n.preferred_ko)
            if key not in existing_nouns:
                existing_nouns.add(key)
                new_nouns.append(n)

        for r in other.formatting_rules:
            key = r.rule_name
            if key not in existing_rules:
                existing_rules.add(key)
                new_rules.append(r)

        return Glossary(
            version=self.version,
            locale_source=self.locale_source,
            locale_target=self.locale_target,
            created_at=self.created_at,
            updated_at=datetime.now(),
            term_rules=[*self.term_rules, *new_terms],
            proper_noun_rules=[*self.proper_noun_rules, *new_nouns],
            formatting_rules=[*self.formatting_rules, *new_rules],
        )

    @property
    def has_rules(self) -> bool:
        """Check if glossary has any rules.

        Returns:
            True if glossary has at least one rule.
        """
        return bool(self.term_rules or self.proper_noun_rules or self.formatting_rules)

    def to_context_string(self) -> str:
        """Convert glossary to a string for LLM context.

        Returns:
            Human-readable glossary summary.
        """
        lines: list[str] = []

        if self.term_rules:
            lines.append("## Term Rules")
            for term in self.term_rules:
                aliases = ", ".join(term.aliases) if term.aliases else "N/A"
                lines.append(f"- {term.term_ko} ({aliases}): {term.notes}")

        if self.proper_noun_rules:
            lines.append("\n## Proper Noun Rules")
            for noun in self.proper_noun_rules:
                lines.append(f"- {noun.source_like} → {noun.preferred_ko}")

        if self.formatting_rules:
            lines.append("\n## Formatting Rules")
            for rule in self.formatting_rules:
                lines.append(f"- {rule.rule_name}: {rule.description}")

        return "\n".join(lines)
