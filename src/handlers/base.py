"""Base classes for content handlers."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class ContentHandler(ABC):
    """Abstract base class for content handlers.

    A handler is responsible for:
    1. Determining if it can handle a file (based on path/extension)
    2. Extracting translatable strings from the file
    3. Applying translations back to the file

    Unlike the filter system, handlers integrate parsing and extraction
    into a single step, reducing overhead and complexity.
    """

    #: Handler name for identification
    name: ClassVar[str] = ""

    #: Priority (higher = checked first)
    priority: ClassVar[int] = 0

    #: File extensions this handler supports
    extensions: ClassVar[tuple[str, ...]] = ()

    #: Path patterns this handler matches (substrings)
    path_patterns: ClassVar[tuple[str, ...]] = ()

    def can_handle(self, path: Path) -> bool:
        """Check if this handler can process the given file.

        Args:
            path: Path to the file.

        Returns:
            True if this handler can process the file.
        """
        path_str = str(path).replace("\\", "/").lower()

        # Check path patterns first (more specific)
        if self.path_patterns:
            for pattern in self.path_patterns:
                if pattern.lower() in path_str:
                    return True
            return False

        # Fall back to extension check
        if self.extensions:
            return path.suffix.lower() in self.extensions

        return False

    @abstractmethod
    async def extract(self, path: Path) -> Mapping[str, str]:
        """Extract translatable strings from the file.

        Args:
            path: Path to the file.

        Returns:
            Mapping of keys to translatable text.
        """

    @abstractmethod
    async def apply(
        self,
        path: Path,
        translations: Mapping[str, str],
        output_path: Path | None = None,
    ) -> None:
        """Apply translations to the file.

        Args:
            path: Path to the original file.
            translations: Mapping of keys to translated text.
            output_path: Optional output path (if different from original).
        """

    def get_output_path(
        self,
        source_path: Path,
        source_locale: str,
        target_locale: str,
    ) -> Path:
        """Get the output path for translated file.

        Args:
            source_path: Original file path.
            source_locale: Source language locale.
            target_locale: Target language locale.

        Returns:
            Path for the translated file.
        """
        # Default: replace locale in path
        path_str = str(source_path)
        return Path(path_str.replace(source_locale, target_locale))


class HandlerRegistry:
    """Registry for content handlers.

    Manages handler registration and selection based on file paths.
    Simpler than the filter system - just finds the right handler.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._handlers: list[ContentHandler] = []

    def register(self, handler: ContentHandler) -> None:
        """Register a handler.

        Args:
            handler: Handler to register.
        """
        self._handlers.append(handler)
        # Sort by priority (highest first)
        self._handlers.sort(key=lambda h: h.priority, reverse=True)
        logger.debug(
            "Registered handler: %s (priority=%d)", handler.name, handler.priority
        )

    def get_handler(self, path: Path) -> ContentHandler | None:
        """Get the appropriate handler for a file.

        Args:
            path: Path to the file.

        Returns:
            Handler that can process the file, or None.
        """
        for handler in self._handlers:
            if handler.can_handle(path):
                return handler
        return None

    def get_all_handlers(self, path: Path) -> list[ContentHandler]:
        """Get all handlers that can process a file.

        Useful when multiple handlers might extract different content.

        Args:
            path: Path to the file.

        Returns:
            List of handlers that can process the file.
        """
        return [h for h in self._handlers if h.can_handle(path)]

    @property
    def handlers(self) -> list[ContentHandler]:
        """Get all registered handlers."""
        return list(self._handlers)


def create_default_registry() -> HandlerRegistry:
    """Create a registry with all default handlers.

    Returns:
        Registry with default handlers registered.
    """
    # Import here to avoid circular imports
    from .ftbquests import FTBQuestsHandler
    from .language import LanguageHandler
    from .origins import OriginsHandler
    from .patchouli import PatchouliHandler
    from .puffish_skills import PuffishSkillsHandler
    from .tconstruct import TConstructHandler
    from .the_vault_quest import TheVaultQuestHandler

    registry = HandlerRegistry()

    # Register special handlers (higher priority = checked first)
    registry.register(FTBQuestsHandler())  # priority=15
    registry.register(PatchouliHandler())  # priority=13
    registry.register(OriginsHandler())  # priority=12
    registry.register(PuffishSkillsHandler())  # priority=11
    registry.register(TConstructHandler())  # priority=11
    registry.register(TheVaultQuestHandler())  # priority=10
    registry.register(LanguageHandler())  # priority=9

    logger.info(
        "Created default registry with %d handlers",
        len(registry.handlers),
    )

    return registry
