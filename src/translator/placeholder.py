"""Placeholder protection utilities for translation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Placeholder patterns
PATTERNS = {
    # Java format specifiers: %s, %d, %1$s, %2$d, etc.
    "java_format": re.compile(r"%(?:\d+\$)?[sdifxXobeEgGaAcChHnp%]"),
    # Minecraft color codes: §a, §0-§f, §k-§o, §r
    "mc_color_section": re.compile(r"§[0-9a-fk-or]", re.IGNORECASE),
    # Alternative color codes: &a, &0-&f, etc.
    "mc_color_ampersand": re.compile(r"&[0-9a-fk-or]", re.IGNORECASE),
    # Named placeholders: {player}, {item}, etc.
    "named_placeholder": re.compile(r"\{[^}]+\}"),
    # XML-like tags: <b>, </b>, <color=red>, etc.
    "xml_tags": re.compile(r"<[^>]+>"),
    # Newlines and special characters
    "special_chars": re.compile(r"\\[nrt]"),
}


class PlaceholderError(ValueError):
    """Exception raised when placeholder restoration fails."""

    pass


@dataclass
class PlaceholderInfo:
    """Information about a placeholder in text."""

    original: str
    token: str
    pattern_name: str
    position: int


@dataclass
class ProtectedText:
    """Text with placeholders replaced by tokens."""

    original: str
    protected: str
    placeholders: list[PlaceholderInfo] = field(default_factory=list)

    def restore(self, translated: str) -> str:
        """Restore placeholders in translated text.

        Args:
            translated: Translated text with tokens.

        Returns:
            Translated text with original placeholders restored.
        """
        import logging

        logger = logging.getLogger(__name__)
        result = translated

        # Sort by token length (longest first) to avoid partial replacements
        sorted_placeholders = sorted(
            self.placeholders,
            key=lambda p: len(p.token),
            reverse=True,
        )

        missing_tokens = []
        for placeholder in sorted_placeholders:
            if placeholder.token in result:
                result = result.replace(placeholder.token, placeholder.original)
            else:
                missing_tokens.append(placeholder.token)
                logger.error(
                    "Placeholder token '%s' not found in translated text. "
                    "Original: '%s', Translated: '%s'",
                    placeholder.token,
                    self.original,
                    translated,
                )

        # Check for any remaining unrestored tokens or missing tokens
        has_issues = False
        if "⟦PH" in result:
            logger.error(
                "Unrestored placeholder tokens remaining in translation. "
                "Original: '%s', Result: '%s'",
                self.original,
                result,
            )
            has_issues = True

        if missing_tokens:
            logger.error(
                "Missing placeholder tokens: %s. Original: '%s', Translated: '%s'",
                ", ".join(missing_tokens),
                self.original,
                translated,
            )
            has_issues = True

        # Raise exception if there were issues
        if has_issues:
            raise PlaceholderError(
                f"Placeholder validation failed for original text: '{self.original}'"
            )

        return result


class PlaceholderProtector:
    """Protects placeholders during translation.

    Replaces placeholders with unique tokens before translation
    and restores them afterward.
    """

    def __init__(self) -> None:
        """Initialize the protector."""
        self._counter = 0

    def protect(self, text: str) -> ProtectedText:
        """Replace placeholders with tokens.

        Args:
            text: Original text with placeholders.

        Returns:
            Protected text info.
        """
        protected = text
        placeholders: list[PlaceholderInfo] = []

        for pattern_name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                original = match.group(0)

                # Skip if already processed (overlapping patterns)
                if any(
                    p.original == original and p.position == match.start()
                    for p in placeholders
                ):
                    continue

                token = self._generate_token()
                placeholders.append(
                    PlaceholderInfo(
                        original=original,
                        token=token,
                        pattern_name=pattern_name,
                        position=match.start(),
                    )
                )

        # Sort by position (reverse) to replace from end to start
        placeholders.sort(key=lambda p: p.position, reverse=True)

        for placeholder in placeholders:
            protected = (
                protected[: placeholder.position]
                + placeholder.token
                + protected[placeholder.position + len(placeholder.original) :]
            )

        return ProtectedText(
            original=text,
            protected=protected,
            placeholders=placeholders,
        )

    def is_only_placeholders(self, protected_text: ProtectedText) -> bool:
        """Check if protected text contains only placeholder tokens.

        Args:
            protected_text: Protected text to check.

        Returns:
            True if text contains only tokens and whitespace.
        """
        if not protected_text.placeholders:
            return False

        # Remove all tokens and check if anything remains
        temp = protected_text.protected
        for placeholder in protected_text.placeholders:
            temp = temp.replace(placeholder.token, "")

        # If only whitespace remains, it's placeholder-only
        return temp.strip() == ""

    def protect_batch(self, texts: list[str]) -> list[ProtectedText]:
        """Protect placeholders in multiple texts.

        Args:
            texts: List of texts.

        Returns:
            List of protected text info.
        """
        return [self.protect(text) for text in texts]

    def _generate_token(self) -> str:
        """Generate a unique placeholder token.

        Returns:
            Unique token string.
        """
        self._counter += 1
        return f"⟦PH{self._counter}⟧"

    @staticmethod
    def extract_placeholders(text: str) -> list[str]:
        """Extract all placeholders from text.

        Args:
            text: Text to analyze.

        Returns:
            List of found placeholders.
        """
        found: list[str] = []

        for pattern in PATTERNS.values():
            for match in pattern.finditer(text):
                if match.group(0) not in found:
                    found.append(match.group(0))

        return found

    @staticmethod
    def count_placeholders(text: str) -> dict[str, int]:
        """Count placeholders by type.

        Args:
            text: Text to analyze.

        Returns:
            Dictionary of pattern names to counts.
        """
        counts: dict[str, int] = {}

        for name, pattern in PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                counts[name] = len(matches)

        return counts
