"""Pydantic models for translation validation."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity level of a validation issue."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationType(str, Enum):
    """Type of validation check."""

    PLACEHOLDER_COUNT = "placeholder_count"
    PLACEHOLDER_ORDER = "placeholder_order"
    COLOR_CODE = "color_code"
    KEY_MISMATCH = "key_mismatch"
    EMPTY_TRANSLATION = "empty_translation"
    UNTRANSLATED = "untranslated"
    FORMAT_STRING = "format_string"
    LENGTH_RATIO = "length_ratio"


class ValidationIssue(BaseModel):
    """A single validation issue found in a translation."""

    issue_type: ValidationType = Field(
        ...,
        description="Type of validation issue",
    )
    severity: ValidationSeverity = Field(
        default=ValidationSeverity.ERROR,
        description="Severity of the issue",
    )
    key: str = Field(
        ...,
        description="Translation key with the issue",
    )
    message: str = Field(
        ...,
        description="Human-readable description of the issue",
    )
    source_value: str | None = Field(
        default=None,
        description="Original source value",
    )
    translated_value: str | None = Field(
        default=None,
        description="Translated value with issue",
    )
    suggestion: str | None = Field(
        default=None,
        description="Suggested fix for the issue",
    )


class ValidationResult(BaseModel):
    """Result of validating a translation."""

    is_valid: bool = Field(
        ...,
        description="Whether the translation passed validation",
    )
    issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="List of validation issues found",
    )
    errors_count: int = Field(
        default=0,
        description="Number of error-level issues",
    )
    warnings_count: int = Field(
        default=0,
        description="Number of warning-level issues",
    )

    @classmethod
    def from_issues(cls, issues: list[ValidationIssue]) -> ValidationResult:
        """Create a validation result from a list of issues.

        Args:
            issues: List of validation issues.

        Returns:
            Validation result.
        """
        errors = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)

        return cls(
            is_valid=errors == 0,
            issues=issues,
            errors_count=errors,
            warnings_count=warnings,
        )

    def get_errors(self) -> list[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    def get_warnings(self) -> list[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]


class ReviewIssue(BaseModel):
    """An issue found during LLM review."""

    key: str = Field(
        ...,
        description="Translation key with the issue",
    )
    issue_type: str = Field(
        ...,
        description="Type of issue (mistranslation, typo, etc.)",
    )
    original: str = Field(
        ...,
        description="Original translated text",
    )
    corrected: str = Field(
        ...,
        description="Corrected translation",
    )
    explanation: str = Field(
        default="",
        description="Explanation of the correction",
    )


class ReviewResult(BaseModel):
    """Result of LLM translation review."""

    reviewed_count: int = Field(
        default=0,
        description="Number of translations reviewed",
    )
    issues_found: list[ReviewIssue] = Field(
        default_factory=list,
        description="Issues found during review",
    )
    corrections_applied: int = Field(
        default=0,
        description="Number of corrections applied",
    )

    @property
    def has_issues(self) -> bool:
        """Check if any issues were found."""
        return len(self.issues_found) > 0

    def get_corrections_dict(self) -> dict[str, str]:
        """Get dictionary of corrections (key -> corrected text)."""
        return {issue.key: issue.corrected for issue in self.issues_found}
