"""Base parser class and custom exceptions for file parsers."""

from __future__ import annotations

import abc
import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Mapping


logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Base exception for all parser-related errors."""

    pass


class ParseError(ParserError):
    """Exception raised when parsing a file fails."""

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        super().__init__(f"Failed to parse {path}: {message}")


class DumpError(ParserError):
    """Exception raised when writing data to a file fails."""

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        super().__init__(f"Failed to dump to {path}: {message}")


class BaseParser(abc.ABC):
    """Abstract base class for file parsers.

    A parser reads a file and returns a ``{key: value}`` mapping,
    where *key* identifies the source string (e.g., translation key or line number),
    and *value* is the text to be translated.
    """

    #: Supported file extensions (with leading dot)
    file_extensions: ClassVar[tuple[str, ...]] = ()

    #: Registry mapping extensions to parser classes
    _registry: ClassVar[dict[str, type[BaseParser]]] = {}

    def __init__(self, path: Path, original_path: Path | None = None) -> None:
        """Initialize the parser.

        Args:
            path: Path to the file to parse/dump.
            original_path: Optional path to the original file (for dump operations).
        """
        self.path = path
        self.original_path = original_path
        logger.debug("Initialized %s for %s", self.__class__.__name__, path)

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Register subclass in the parser registry."""
        super().__init_subclass__(**kwargs)
        for ext in cls.file_extensions:
            BaseParser._registry[ext.lower()] = cls
            logger.debug("Registered %s for extension %s", cls.__name__, ext)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @abc.abstractmethod
    async def parse(self) -> Mapping[str, str]:
        """Parse the file and return a mapping of translatable strings.

        Returns:
            A mapping from keys to translatable text values.

        Raises:
            ParseError: If parsing fails.
        """

    @abc.abstractmethod
    async def dump(self, data: Mapping[str, str]) -> None:
        """Write the translated data back to the file.

        Args:
            data: A mapping of keys to translated text values.

        Raises:
            DumpError: If writing fails.
        """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _check_extension(self) -> None:
        """Validate that the file has a supported extension.

        Raises:
            ParseError: If the file extension is not supported.
        """
        if (
            self.file_extensions
            and self.path.suffix.lower() not in self.file_extensions
        ):
            raise ParseError(
                self.path,
                f"Unsupported extension '{self.path.suffix}' for {self.__class__.__name__}. "
                f"Expected one of: {', '.join(self.file_extensions)}",
            )

    # ------------------------------------------------------------------
    # Factory Methods
    # ------------------------------------------------------------------
    @classmethod
    def get_parser_by_extension(cls, extension: str) -> type[BaseParser] | None:
        """Get the appropriate parser class for a file extension.

        Args:
            extension: File extension including the dot (e.g., '.json', '.lang').

        Returns:
            The parser class for the extension, or None if not supported.
        """
        return cls._registry.get(extension.lower())

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """Get a list of all supported file extensions.

        Returns:
            List of supported extensions.
        """
        return list(cls._registry.keys())

    @classmethod
    def create_parser(
        cls,
        path: Path,
        original_path: Path | None = None,
    ) -> BaseParser | None:
        """Factory method to create the appropriate parser for a file.

        Args:
            path: Path to the file.
            original_path: Optional path to the original file.

        Returns:
            A parser instance, or None if the extension is not supported.
        """
        parser_cls = cls.get_parser_by_extension(path.suffix)
        if parser_cls is None:
            logger.warning("No parser found for extension: %s", path.suffix)
            return None
        
        # Check if parser has additional filtering (e.g., JSONParser.should_handle)
        if hasattr(parser_cls, "should_handle"):
            if not parser_cls.should_handle(path):
                logger.debug("%s rejected file: %s", parser_cls.__name__, path)
                return None
        
        return parser_cls(path, original_path)
