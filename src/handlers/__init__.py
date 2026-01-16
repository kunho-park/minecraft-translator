"""Content handlers for extracting and applying translations.

This module provides a unified interface for handling different
file types in Minecraft modpacks. Handlers extract translatable
content and apply translations back to files.
"""

from .base import ContentHandler, HandlerRegistry
from .ftbquests import FTBQuestsHandler
from .language import LanguageHandler
from .origins import OriginsHandler
from .patchouli import PatchouliHandler
from .puffish_skills import PuffishSkillsHandler
from .tconstruct import TConstructHandler

__all__ = [
    "ContentHandler",
    "HandlerRegistry",
    "LanguageHandler",
    # Mod-specific handlers
    "FTBQuestsHandler",
    "OriginsHandler",
    "PatchouliHandler",
    "PuffishSkillsHandler",
    "TConstructHandler",
]
