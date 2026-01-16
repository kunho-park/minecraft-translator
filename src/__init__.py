"""Auto-translate pipeline for Minecraft modpacks."""

from .handlers import ContentHandler, HandlerRegistry
from .handlers.base import create_default_registry
from .llm import LLMClient, LLMConfig, LLMProvider
from .models import Glossary, TranslationTask
from .pipeline import PipelineConfig, PipelineResult, TranslationPipeline, run_pipeline
from .scanner import ModpackScanner, ScanResult, scan_modpack

__version__ = "2.0.4"

__all__ = [
    # Pipeline
    "PipelineConfig",
    "PipelineResult",
    "TranslationPipeline",
    "run_pipeline",
    # Scanner
    "ModpackScanner",
    "ScanResult",
    "scan_modpack",
    # Handlers
    "ContentHandler",
    "HandlerRegistry",
    "create_default_registry",
    # LLM
    "LLMClient",
    "LLMConfig",
    "LLMProvider",
    # Models
    "Glossary",
    "TranslationTask",
]
