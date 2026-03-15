"""Translation validator for checking translation quality."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from ..models import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    ValidationType,
)
from ..translator.placeholder import PlaceholderProtector

from ..models.glossary import ProperNounRule, TermRule

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ..models import Glossary

logger = logging.getLogger(__name__)

# Maximum acceptable length ratio (translated / source)
MAX_LENGTH_RATIO = 3.0
MIN_LENGTH_RATIO = 0.2

_UNRESTORED_TOKEN_RE = re.compile(r"⟦PH[^⟧]*⟧")
_JAVA_FORMAT_RE = re.compile(r"%(?:\d+\$)?[sdifxXobeEgGaAcChHnp]")
_NUMBERED_FORMAT_RE = re.compile(r"%(\d+)\$[sdifxXobeEgGaAcChHnp]")
_SECTION_COLOR_RE = re.compile(r"§[0-9a-fk-or]", re.IGNORECASE)
_AMPERSAND_COLOR_RE = re.compile(r"&[0-9a-fk-or]", re.IGNORECASE)


class TranslationValidator:
    """Validator for checking translation quality and consistency.

    Validates:
    - Placeholder preservation (count and order)
    - Color code preservation
    - Key matching
    - Length ratios
    - Empty translations
    - Glossary term consistency
    """

    def __init__(self, glossary: Glossary | None = None) -> None:
        """Initialize the validator.

        Args:
            glossary: Optional glossary for consistency checking.
        """
        self.protector = PlaceholderProtector()
        self.glossary = glossary
        self._compiled_term_patterns: list[
            tuple[TermRule, list[tuple[str, re.Pattern[str]]]]
        ] = []
        self._compiled_noun_patterns: list[
            tuple[ProperNounRule, list[tuple[str, re.Pattern[str]]]]
        ] = []
        if glossary:
            self._precompile_glossary_patterns(glossary)
        logger.info("Initialized TranslationValidator")

    def _precompile_glossary_patterns(self, glossary: Glossary) -> None:
        for term in glossary.term_rules:
            alias_patterns = [
                (a, re.compile(r"\b" + re.escape(a.lower()) + r"\b"))
                for a in term.aliases
            ]
            self._compiled_term_patterns.append((term, alias_patterns))

        for noun in glossary.proper_noun_rules:
            candidates = [(noun.source_like, re.compile(
                r"\b" + re.escape(noun.source_like.lower()) + r"\b"
            ))]
            candidates.extend(
                (a, re.compile(r"\b" + re.escape(a.lower()) + r"\b"))
                for a in noun.aliases
            )
            self._compiled_noun_patterns.append((noun, candidates))

    def validate(
        self,
        source_data: Mapping[str, str],
        translated_data: Mapping[str, str],
    ) -> ValidationResult:
        """Validate translated data against source.

        Args:
            source_data: Original source language data.
            translated_data: Translated data to validate.

        Returns:
            Validation result with any issues found.
        """
        logger.info(
            "Validating %d translations against %d source entries",
            len(translated_data),
            len(source_data),
        )

        issues: list[ValidationIssue] = []

        # Check for missing keys
        for key in source_data:
            if key not in translated_data:
                issues.append(
                    ValidationIssue(
                        issue_type=ValidationType.KEY_MISMATCH,
                        severity=ValidationSeverity.ERROR,
                        key=key,
                        message=f"Translation missing for key: {key}",
                        source_value=source_data[key],
                    )
                )

        # Check each translation
        for key, translated in translated_data.items():
            if key not in source_data:
                issues.append(
                    ValidationIssue(
                        issue_type=ValidationType.KEY_MISMATCH,
                        severity=ValidationSeverity.WARNING,
                        key=key,
                        message=f"Extra key in translation: {key}",
                        translated_value=translated,
                    )
                )
                continue

            source = source_data[key]

            # Check for empty translation
            if not translated or not translated.strip():
                issues.append(
                    ValidationIssue(
                        issue_type=ValidationType.EMPTY_TRANSLATION,
                        severity=ValidationSeverity.ERROR,
                        key=key,
                        message="Translation is empty",
                        source_value=source,
                        translated_value=translated,
                    )
                )
                continue

            # Check for untranslated text (same as source)
            if translated == source and self._looks_like_text(source):
                issues.append(
                    ValidationIssue(
                        issue_type=ValidationType.UNTRANSLATED,
                        severity=ValidationSeverity.WARNING,
                        key=key,
                        message="Translation appears unchanged from source",
                        source_value=source,
                        translated_value=translated,
                    )
                )

            # Check for unrestored placeholder tokens
            token_issues = self._check_placeholder_tokens(key, translated)
            issues.extend(token_issues)

            # Check placeholder preservation
            placeholder_issues = self._check_placeholders(key, source, translated)
            issues.extend(placeholder_issues)

            # Check color codes
            color_issues = self._check_color_codes(key, source, translated)
            issues.extend(color_issues)

            # Check length ratio
            length_issues = self._check_length_ratio(key, source, translated)
            issues.extend(length_issues)

            # Check glossary consistency
            if self.glossary:
                glossary_issues = self._check_glossary_consistency(
                    key, source, translated
                )
                issues.extend(glossary_issues)

        result = ValidationResult.from_issues(issues)
        logger.info(
            "Validation complete: %d errors, %d warnings",
            result.errors_count,
            result.warnings_count,
        )

        return result

    def _check_placeholder_tokens(
        self,
        key: str,
        translated: str,
    ) -> list[ValidationIssue]:
        """Check for unrestored placeholder tokens in translation.

        Args:
            key: Translation key.
            translated: Translated text.

        Returns:
            List of validation issues.
        """
        issues: list[ValidationIssue] = []

        # Check for placeholder restoration errors
        if translated.startswith("[PLACEHOLDER_ERROR]"):
            issues.append(
                ValidationIssue(
                    issue_type=ValidationType.PLACEHOLDER_COUNT,
                    severity=ValidationSeverity.ERROR,
                    key=key,
                    message="Placeholder restoration failed - tokens missing or not properly restored",
                    translated_value=translated.replace("[PLACEHOLDER_ERROR] ", ""),
                    suggestion="LLM did not preserve placeholder tokens correctly. Retranslation required.",
                )
            )
            return issues

        tokens = _UNRESTORED_TOKEN_RE.findall(translated)

        if tokens:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationType.PLACEHOLDER_COUNT,
                    severity=ValidationSeverity.ERROR,
                    key=key,
                    message=f"Unrestored placeholder tokens found: {', '.join(tokens)}",
                    translated_value=translated,
                    suggestion="LLM abbreviated or modified placeholder tokens. Retranslation required.",
                )
            )

        return issues

    def _check_placeholders(
        self,
        key: str,
        source: str,
        translated: str,
    ) -> list[ValidationIssue]:
        """Check if placeholders are preserved.

        Args:
            key: Translation key.
            source: Source text.
            translated: Translated text.

        Returns:
            List of validation issues.
        """
        issues: list[ValidationIssue] = []

        # Check count
        source_counts = self.protector.count_placeholders(source)
        translated_counts = self.protector.count_placeholders(translated)

        for pattern_name, source_count in source_counts.items():
            translated_count = translated_counts.get(pattern_name, 0)

            if translated_count != source_count:
                issues.append(
                    ValidationIssue(
                        issue_type=ValidationType.PLACEHOLDER_COUNT,
                        severity=ValidationSeverity.ERROR,
                        key=key,
                        message=(
                            f"Placeholder count mismatch for {pattern_name}: "
                            f"source={source_count}, translated={translated_count}"
                        ),
                        source_value=source,
                        translated_value=translated,
                        suggestion=f"Ensure all {pattern_name} placeholders are preserved",
                    )
                )

        # Check for extra placeholders in translation
        for pattern_name, translated_count in translated_counts.items():
            if pattern_name not in source_counts:
                issues.append(
                    ValidationIssue(
                        issue_type=ValidationType.PLACEHOLDER_COUNT,
                        severity=ValidationSeverity.ERROR,
                        key=key,
                        message=f"Extra {pattern_name} placeholders in translation",
                        source_value=source,
                        translated_value=translated,
                    )
                )

        source_formats = _JAVA_FORMAT_RE.findall(source)
        translated_formats = _JAVA_FORMAT_RE.findall(translated)

        if source_formats and translated_formats:
            source_numbered = _NUMBERED_FORMAT_RE.findall(source)
            translated_numbered = _NUMBERED_FORMAT_RE.findall(translated)

            if source_numbered != translated_numbered:
                issues.append(
                    ValidationIssue(
                        issue_type=ValidationType.PLACEHOLDER_ORDER,
                        severity=ValidationSeverity.ERROR,
                        key=key,
                        message="Numbered placeholder order changed",
                        source_value=source,
                        translated_value=translated,
                    )
                )

        return issues

    def _check_color_codes(
        self,
        key: str,
        source: str,
        translated: str,
    ) -> list[ValidationIssue]:
        """Check if color codes are preserved.

        Args:
            key: Translation key.
            source: Source text.
            translated: Translated text.

        Returns:
            List of validation issues.
        """
        issues: list[ValidationIssue] = []

        source_sections = _SECTION_COLOR_RE.findall(source)
        translated_sections = _SECTION_COLOR_RE.findall(translated)

        if len(source_sections) != len(translated_sections):
            issues.append(
                ValidationIssue(
                    issue_type=ValidationType.COLOR_CODE,
                    severity=ValidationSeverity.ERROR,
                    key=key,
                    message=(
                        f"Color code count mismatch: "
                        f"source={len(source_sections)}, translated={len(translated_sections)}"
                    ),
                    source_value=source,
                    translated_value=translated,
                )
            )

        source_ampersands = _AMPERSAND_COLOR_RE.findall(source)
        translated_ampersands = _AMPERSAND_COLOR_RE.findall(translated)

        if len(source_ampersands) != len(translated_ampersands):
            issues.append(
                ValidationIssue(
                    issue_type=ValidationType.COLOR_CODE,
                    severity=ValidationSeverity.ERROR,
                    key=key,
                    message=(
                        f"Ampersand color code count mismatch: "
                        f"source={len(source_ampersands)}, translated={len(translated_ampersands)}"
                    ),
                    source_value=source,
                    translated_value=translated,
                )
            )

        return issues

    def _check_length_ratio(
        self,
        key: str,
        source: str,
        translated: str,
    ) -> list[ValidationIssue]:
        """Check if translation length is reasonable.

        Args:
            key: Translation key.
            source: Source text.
            translated: Translated text.

        Returns:
            List of validation issues.
        """
        issues: list[ValidationIssue] = []

        if not source:
            return issues

        ratio = len(translated) / len(source)

        if ratio > MAX_LENGTH_RATIO:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationType.LENGTH_RATIO,
                    severity=ValidationSeverity.WARNING,
                    key=key,
                    message=f"Translation is much longer than source (ratio: {ratio:.1f}x)",
                    source_value=source,
                    translated_value=translated,
                )
            )
        elif ratio < MIN_LENGTH_RATIO:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationType.LENGTH_RATIO,
                    severity=ValidationSeverity.WARNING,
                    key=key,
                    message=f"Translation is much shorter than source (ratio: {ratio:.1f}x)",
                    source_value=source,
                    translated_value=translated,
                )
            )

        return issues

    def _check_glossary_consistency(
        self,
        key: str,
        source: str,
        translated: str,
    ) -> list[ValidationIssue]:
        """Check if translation follows glossary rules.

        Checks:
        - Term rules: if source contains a glossary alias, translation should contain the term_ko
        - Proper noun rules: if source contains source_like/alias, translation should contain preferred_ko

        Args:
            key: Translation key.
            source: Source text.
            translated: Translated text.

        Returns:
            List of validation issues.
        """
        issues: list[ValidationIssue] = []
        if not self.glossary:
            return issues

        source_lower = source.lower()

        for term, alias_patterns in self._compiled_term_patterns:
            alias_found = False
            matched_alias = ""
            for alias, pat in alias_patterns:
                if pat.search(source_lower):
                    alias_found = True
                    matched_alias = alias
                    break

            if alias_found and term.term_ko not in translated:
                issues.append(
                    ValidationIssue(
                        issue_type=ValidationType.GLOSSARY_TERM_MISMATCH,
                        severity=ValidationSeverity.WARNING,
                        key=key,
                        message=(
                            f"Glossary term mismatch: source has '{matched_alias}' "
                            f"but translation doesn't contain '{term.term_ko}'"
                        ),
                        source_value=source,
                        translated_value=translated,
                        suggestion=f"Use glossary term: '{term.term_ko}'",
                    )
                )

        for noun, candidate_patterns in self._compiled_noun_patterns:
            noun_found = False
            matched_noun = ""
            for name, pat in candidate_patterns:
                if pat.search(source_lower):
                    noun_found = True
                    matched_noun = name
                    break

            if noun_found and noun.preferred_ko not in translated:
                issues.append(
                    ValidationIssue(
                        issue_type=ValidationType.GLOSSARY_NOUN_MISMATCH,
                        severity=ValidationSeverity.WARNING,
                        key=key,
                        message=(
                            f"Glossary proper noun mismatch: source has '{matched_noun}' "
                            f"but translation doesn't contain '{noun.preferred_ko}'"
                        ),
                        source_value=source,
                        translated_value=translated,
                        suggestion=f"Use glossary proper noun: '{noun.preferred_ko}'",
                    )
                )

        return issues

    @staticmethod
    def _looks_like_text(text: str) -> bool:
        """Check if text looks like translatable content.

        Args:
            text: Text to check.

        Returns:
            True if text appears to be translatable.
        """
        # Skip if mostly special characters or numbers
        alpha_count = sum(1 for c in text if c.isalpha())
        return alpha_count >= 3

    def fix_issues(
        self,
        source_data: Mapping[str, str],
        translated_data: dict[str, str],
        validation_result: ValidationResult,
    ) -> dict[str, str]:
        """Attempt to automatically fix some validation issues.

        Args:
            source_data: Original source data.
            translated_data: Translated data with issues.
            validation_result: Validation result with issues.

        Returns:
            Fixed translated data.
        """
        fixed_data = dict(translated_data)

        for issue in validation_result.issues:
            if issue.issue_type == ValidationType.KEY_MISMATCH:
                # Add missing keys
                if issue.key in source_data and issue.key not in fixed_data:
                    fixed_data[issue.key] = source_data[issue.key]
                    logger.info("Added missing key: %s", issue.key)

            elif issue.issue_type == ValidationType.EMPTY_TRANSLATION:
                # Use source as fallback for empty translations
                if issue.key in source_data:
                    fixed_data[issue.key] = source_data[issue.key]
                    logger.info("Used source as fallback for: %s", issue.key)

        return fixed_data
