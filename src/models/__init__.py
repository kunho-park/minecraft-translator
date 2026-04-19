"""Pydantic models for translation pipeline."""

from .glossary import (
    FormattingRule,
    Glossary,
    ProperNounRule,
    TermRule,
)
from .translation import (
    LanguageFilePair,
    TranslationBatch,
    TranslationEntry,
    TranslationResult,
    TranslationStatus,
    TranslationTask,
)
from .validation import (
    ReviewIssue,
    ReviewResult,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    ValidationType,
)

__all__ = [
    # Glossary
    "FormattingRule",
    "Glossary",
    "ProperNounRule",
    "TermRule",
    # Translation
    "LanguageFilePair",
    "TranslationBatch",
    "TranslationEntry",
    "TranslationResult",
    "TranslationStatus",
    "TranslationTask",
    # Validation
    "ReviewIssue",
    "ReviewResult",
    "ValidationIssue",
    "ValidationResult",
    "ValidationSeverity",
    "ValidationType",
]
