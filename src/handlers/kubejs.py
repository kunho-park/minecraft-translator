"""KubeJS content handler for extracting translatable strings from JS files."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import aiofiles

from .base import ContentHandler

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class KubeJSHandler(ContentHandler):
    """Handler for KubeJS JavaScript files.

    Extracts translatable strings from method calls like:
    - .displayName("text")
    - .formattedDisplayName("text")
    - Text.yellow("text")
    - Component.green("text")
    - addTooltip('id', 'text')
    """

    name: ClassVar[str] = "kubejs"
    priority: ClassVar[int] = 20  # High priority for KubeJS files

    # Path patterns for KubeJS files
    path_patterns: ClassVar[tuple[str, ...]] = (
        "/kubejs/",
        "\\kubejs\\",
    )

    extensions: ClassVar[tuple[str, ...]] = (".js", ".ts")

    # Methods that take translatable text as first argument
    DISPLAY_METHODS = ("displayName", "formattedDisplayName")

    # Color methods for Text/Component
    COLOR_METHODS = (
        "black",
        "darkBlue",
        "darkGreen",
        "darkAqua",
        "darkRed",
        "darkPurple",
        "gold",
        "gray",
        "darkGray",
        "blue",
        "green",
        "aqua",
        "red",
        "lightPurple",
        "yellow",
        "white",
        "of",
    )

    # Methods that take translatable text as second argument
    SECOND_ARG_METHODS = ("addTooltip",)

    def __init__(self) -> None:
        """Initialize the handler and compile regex patterns."""
        super().__init__()
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for extraction."""
        # Pattern 1: .displayName("...") - method call with string
        self._display_pattern = re.compile(
            rf"\.({'|'.join(self.DISPLAY_METHODS)})\s*\(\s*"
            rf"(['\"`])((?:[^\\\n]|\\.)*?)\2\s*\)",
            re.MULTILINE,
        )

        # Pattern 2: Text.yellow("...") / Component.blue("...")
        self._text_component_pattern = re.compile(
            rf"((?:Text|Component)\.({'|'.join(self.COLOR_METHODS)}))\s*\(\s*"
            rf"(['\"`])((?:[^\\\n]|\\.)*?)\3\s*\)",
            re.MULTILINE,
        )

        # Pattern 3: addTooltip('id', 'text', ...)
        self._second_arg_pattern = re.compile(
            rf"({'|'.join(self.SECOND_ARG_METHODS)})\s*\("
            rf"([^,]+?),\s*(['\"`])((?:[^\\]|\\.)*?)\3(\s*(?:,[^)]*)?)\)",
            re.DOTALL,
        )

    def can_handle(self, path: Path) -> bool:
        """Check if this is a KubeJS JavaScript file.

        Args:
            path: Path to check.

        Returns:
            True if this is a KubeJS JS file.
        """
        if path.suffix.lower() not in self.extensions:
            return False

        path_str = str(path).replace("\\", "/").lower()
        return any(p.lower().replace("\\", "/") in path_str for p in self.path_patterns)

    def _should_skip(self, text: str) -> bool:
        """Check if text should be skipped from translation.

        Args:
            text: Text to check.

        Returns:
            True if should skip.
        """
        if not text or not text.strip():
            return True
        # Skip template literals with ${...}
        if "${" in text and "}" in text:
            return True
        return False

    async def extract(self, path: Path) -> Mapping[str, str]:
        """Extract translatable strings from KubeJS file.

        Args:
            path: Path to the JS file.

        Returns:
            Mapping of keys to translatable text.
        """
        try:
            async with aiofiles.open(path, encoding="utf-8", errors="replace") as f:
                content = await f.read()
        except OSError as e:
            logger.error("Failed to read %s: %s", path, e)
            return {}

        entries: dict[str, str] = {}
        file_key = path.stem

        # Extract from display methods: .displayName("...")
        for match in self._display_pattern.finditer(content):
            method = match.group(1)
            text = match.group(3)

            if self._should_skip(text):
                continue

            key = f"{file_key}.{method}_{match.start()}"
            entries[key] = text

        # Extract from Text/Component: Text.yellow("...")
        for match in self._text_component_pattern.finditer(content):
            full_method = match.group(1)
            text = match.group(4)

            if self._should_skip(text):
                continue

            key = f"{file_key}.{full_method}_{match.start()}"
            entries[key] = text

        # Extract from second arg methods: addTooltip('id', 'text')
        for match in self._second_arg_pattern.finditer(content):
            method = match.group(1)
            first_arg = match.group(2).strip().strip("'\"")
            text = match.group(4)

            if self._should_skip(text):
                continue

            key = f"{file_key}.{method}_{first_arg}_{match.start()}"
            entries[key] = text

        logger.debug(
            "Extracted %d entries from KubeJS file: %s", len(entries), path.name
        )
        return entries

    async def apply(
        self,
        path: Path,
        translations: Mapping[str, str],
        output_path: Path | None = None,
    ) -> None:
        """Apply translations to KubeJS file.

        Args:
            path: Path to the original file.
            translations: Mapping of keys to translated text.
            output_path: Optional output path.
        """
        target_path = output_path or path

        try:
            async with aiofiles.open(path, encoding="utf-8", errors="replace") as f:
                content = await f.read()
        except OSError as e:
            logger.error("Failed to read %s: %s", path, e)
            return

        file_key = path.stem
        updated_content = content

        # Apply to display methods
        def replace_display(match: re.Match[str]) -> str:
            method = match.group(1)
            quote = match.group(2)
            original = match.group(3)

            if self._should_skip(original):
                return match.group(0)

            key = f"{file_key}.{method}_{match.start()}"
            if key in translations:
                translated = self._escape_for_quote(translations[key], quote)
                return f".{method}({quote}{translated}{quote})"
            return match.group(0)

        updated_content = self._display_pattern.sub(replace_display, updated_content)

        # Apply to Text/Component
        def replace_text_component(match: re.Match[str]) -> str:
            full_method = match.group(1)
            quote = match.group(3)
            original = match.group(4)

            if self._should_skip(original):
                return match.group(0)

            key = f"{file_key}.{full_method}_{match.start()}"
            if key in translations:
                translated = self._escape_for_quote(translations[key], quote)
                return f"{full_method}({quote}{translated}{quote})"
            return match.group(0)

        updated_content = self._text_component_pattern.sub(
            replace_text_component, updated_content
        )

        # Apply to second arg methods
        def replace_second_arg(match: re.Match[str]) -> str:
            method = match.group(1)
            first_arg = match.group(2)
            quote = match.group(3)
            original = match.group(4)
            rest = match.group(5) or ""

            if self._should_skip(original):
                return match.group(0)

            first_arg_clean = first_arg.strip().strip("'\"")
            key = f"{file_key}.{method}_{first_arg_clean}_{match.start()}"
            if key in translations:
                translated = self._escape_for_quote(translations[key], quote)
                return f"{method}({first_arg}, {quote}{translated}{quote}{rest})"
            return match.group(0)

        updated_content = self._second_arg_pattern.sub(
            replace_second_arg, updated_content
        )

        # Write output
        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            async with aiofiles.open(target_path, "w", encoding="utf-8") as f:
                await f.write(updated_content)
            logger.debug("Applied translations to: %s", target_path.name)
        except OSError as e:
            logger.error("Failed to write %s: %s", target_path, e)
            raise

    @staticmethod
    def _escape_for_quote(text: str, quote: str) -> str:
        """Escape text for the given quote character.

        Args:
            text: Text to escape.
            quote: Quote character (' or " or `).

        Returns:
            Escaped text.
        """
        if quote == '"':
            return text.replace("\\", "\\\\").replace('"', '\\"')
        elif quote == "'":
            return text.replace("\\", "\\\\").replace("'", "\\'")
        elif quote == "`":
            return text.replace("\\", "\\\\").replace("`", "\\`")
        return text

    def get_output_path(
        self,
        source_path: Path,
        source_locale: str,
        target_locale: str,
    ) -> Path:
        """KubeJS files are translated in-place (override files).

        Args:
            source_path: Original file path.
            source_locale: Source language locale.
            target_locale: Target language locale.

        Returns:
            Same path (KubeJS is overwritten, not locale-based).
        """
        # KubeJS files are usually language-agnostic
        # Return the same path for in-place modification
        return source_path
