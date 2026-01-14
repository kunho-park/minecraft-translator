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

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

# Maximum acceptable length ratio (translated / source)
MAX_LENGTH_RATIO = 3.0
MIN_LENGTH_RATIO = 0.2


class TranslationValidator:
    """Validator for checking translation quality and consistency.

    Validates:
    - Placeholder preservation (count and order)
    - Color code preservation
    - Key matching
    - Length ratios
    - Empty translations
    """

    def __init__(self) -> None:
        """Initialize the validator."""
        self.protector = PlaceholderProtector()
        logger.info("Initialized TranslationValidator")

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

        # Pattern to match unrestored placeholder tokens: ⟦PH...⟧ or ⟦PH_xxx⟧
        token_pattern = re.compile(r"⟦PH[^⟧]*⟧")
        tokens = token_pattern.findall(translated)

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

        # Check order for format specifiers
        java_format_pattern = re.compile(r"%(?:\d+\$)?[sdifxXobeEgGaAcChHnp]")
        source_formats = java_format_pattern.findall(source)
        translated_formats = java_format_pattern.findall(translated)

        if source_formats and translated_formats:
            # Check if numbered formats are preserved
            numbered_pattern = re.compile(r"%(\d+)\$[sdifxXobeEgGaAcChHnp]")
            source_numbered = numbered_pattern.findall(source)
            translated_numbered = numbered_pattern.findall(translated)

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

        # Check section symbol color codes
        section_pattern = re.compile(r"§[0-9a-fk-or]", re.IGNORECASE)
        source_sections = section_pattern.findall(source)
        translated_sections = section_pattern.findall(translated)

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

        # Check ampersand color codes
        ampersand_pattern = re.compile(r"&[0-9a-fk-or]", re.IGNORECASE)
        source_ampersands = ampersand_pattern.findall(source)
        translated_ampersands = ampersand_pattern.findall(translated)

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
