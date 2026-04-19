"""Translation system for GUI."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class Translator(QObject):
    """Translation manager for GUI text.

    Loads translation files and provides translation lookup.
    """

    languageChanged = Signal(str)  # Emitted when language changes

    def __init__(self) -> None:
        """Initialize translator."""
        super().__init__()
        self.translations_dir = Path(__file__).parent / "translations"
        self.current_language = "ko"
        self._translations: dict[str, Any] = {}
        self._fallback: dict[str, Any] = {}

        # Load default language
        self.load_language("en")  # Fallback
        self._fallback = dict(self._translations)
        self.load_language(self.current_language)

    def load_language(self, language: str) -> bool:
        """Load translation file for a language.

        Args:
            language: Language code (e.g., "ko", "en")

        Returns:
            True if loaded successfully
        """
        translation_file = self.translations_dir / f"{language}.json"

        if not translation_file.exists():
            logger.warning("Translation file not found: %s", translation_file)
            return False

        try:
            with open(translation_file, encoding="utf-8") as f:
                self._translations = json.load(f)

            self.current_language = language
            self.languageChanged.emit(language)
            logger.info("Loaded translations for language: %s", language)
            return True

        except Exception as e:
            logger.error("Failed to load translation file %s: %s", translation_file, e)
            return False

    def get(self, key: str, default: str | None = None, **kwargs: Any) -> str:
        """Get translated text for a key.

        Args:
            key: Translation key (dot-separated path)
            default: Default text if key not found
            **kwargs: Format arguments for the translation

        Returns:
            Translated text
        """
        # Navigate through nested dict
        keys = key.split(".")
        value: Any = self._translations

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Try fallback
                value = self._fallback
                for fk in keys:
                    if isinstance(value, dict) and fk in value:
                        value = value[fk]
                    else:
                        # Return default or key
                        return default if default is not None else key
                break

        if not isinstance(value, str):
            return default if default is not None else key

        # Apply format arguments
        if kwargs:
            try:
                value = value.format(**kwargs)
            except KeyError as e:
                logger.warning("Missing format argument %s for key %s", e, key)

        return value

    def t(self, key: str, default: str | None = None, **kwargs: Any) -> str:
        """Shorthand for get().

        Args:
            key: Translation key
            default: Default text
            **kwargs: Format arguments

        Returns:
            Translated text
        """
        return self.get(key, default, **kwargs)


# Global translator instance
_translator_instance: Translator | None = None


def get_translator() -> Translator:
    """Get global translator instance."""
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = Translator()
    return _translator_instance


def set_language(language: str) -> bool:
    """Set the current language.

    Args:
        language: Language code (e.g., "ko", "en")

    Returns:
        True if language was set successfully
    """
    translator = get_translator()
    return translator.load_language(language)
