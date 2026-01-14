"""Configuration management for the GUI application."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class AppConfig(QObject):
    """Application configuration manager.

    Stores and loads user preferences, LLM settings, and launcher paths.
    """

    configChanged = Signal()

    def __init__(self) -> None:
        """Initialize configuration manager."""
        super().__init__()
        self.config_dir = Path(user_config_dir("auto-translate", "mcat"))
        self.config_file = self.config_dir / "config.json"
        self._config: dict[str, Any] = self._load_default_config()
        self.load()

    def _load_default_config(self) -> dict[str, Any]:
        """Get default configuration values."""
        return {
            "theme": "auto",  # auto, light, dark
            "language": "ko",  # ko, en
            "llm": {
                "provider": "ollama",
                "model": "qwen2.5:14b",
                "temperature": 0.1,
                "batch_size": 30,
                "max_concurrent": 15,
                "requests_per_minute": 0,  # 0 = no limit
                "tokens_per_minute": 0,  # 0 = no limit (e.g. 4000000 for 4M TPM)
            },
            "translation": {
                "source_locale": "en_us",
                "target_locale": "ko_kr",
                "skip_glossary": False,
                "skip_review": False,
                "save_glossary": True,
            },
            "paths": {
                "last_modpack": "",
                "last_output": "",
                "launcher_paths": [],
            },
            "upload": {
                "api_url": "https://mct.2odk.com/api",
                "anonymous": True,
                "last_curseforge_id": "",
            },
        }

    def load(self) -> None:
        """Load configuration from file."""
        if not self.config_file.exists():
            logger.info("Config file not found, using defaults")
            return

        try:
            with open(self.config_file, encoding="utf-8") as f:
                loaded_config = json.load(f)
                # Merge with defaults (preserve new keys)
                self._merge_config(loaded_config)
            logger.info("Configuration loaded from %s", self.config_file)
        except Exception as e:
            logger.error("Failed to load config: %s", e)

    def save(self) -> None:
        """Save configuration to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info("Configuration saved to %s", self.config_file)
        except Exception as e:
            logger.error("Failed to save config: %s", e)

    def _merge_config(self, loaded: dict[str, Any]) -> None:
        """Merge loaded config with defaults."""

        def merge_dict(base: dict[str, Any], update: dict[str, Any]) -> None:
            for key, value in update.items():
                if (
                    key in base
                    and isinstance(base[key], dict)
                    and isinstance(value, dict)
                ):
                    merge_dict(base[key], value)
                else:
                    base[key] = value

        merge_dict(self._config, loaded)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key.

        Args:
            key: Configuration key (e.g., "llm.model")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value: Any = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-separated key.

        Args:
            key: Configuration key (e.g., "llm.model")
            value: Value to set
        """
        keys = key.split(".")
        config: Any = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self.configChanged.emit()

    def get_all(self) -> dict[str, Any]:
        """Get all configuration."""
        return dict(self._config)


# Global config instance
_config_instance: AppConfig | None = None


def get_config() -> AppConfig:
    """Get global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance
