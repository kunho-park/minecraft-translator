"""Update checker worker."""

from __future__ import annotations

import json
import logging
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

from PySide6.QtCore import QThread, Signal

from gui import __version__

logger = logging.getLogger(__name__)

GITHUB_REPO = "kunho-park/minecraft-translator"
UPDATE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def parse_version(v: str) -> tuple[int, ...]:
    """Parse version string to tuple of integers.

    Handles simple versions like "1.0.0" or "v2.1.0".
    """
    # Remove 'v' prefix if present
    v = v.lstrip("v")
    # Extract only numbers and dots
    clean_v = re.sub(r"[^0-9.]", "", v)
    try:
        return tuple(map(int, clean_v.split(".")))
    except ValueError:
        return (0, 0, 0)


class UpdateWorker(QThread):
    """Worker thread for checking updates."""

    updateAvailable = Signal(str, str, str)  # version, release_notes, download_url
    updateError = Signal(str)
    noUpdate = Signal()

    def run(self) -> None:
        """Run update check."""
        try:
            logger.info("Checking for updates from %s", UPDATE_URL)
            req = Request(UPDATE_URL)
            req.add_header("Accept", "application/vnd.github.v3+json")
            req.add_header("User-Agent", "Modpack-Translator-GUI")

            with urlopen(req, timeout=10) as response:
                if response.status != 200:
                    raise URLError(f"HTTP {response.status}")

                data = json.loads(response.read().decode())

                latest_tag = data.get("tag_name", "0.0.0")
                latest_version = parse_version(latest_tag)
                current_version = parse_version(__version__)

                logger.info(
                    "Current version: %s, Latest version: %s",
                    current_version,
                    latest_version,
                )

                if latest_version > current_version:
                    release_notes = data.get("body", "")
                    download_url = data.get("html_url", "")
                    self.updateAvailable.emit(latest_tag, release_notes, download_url)
                else:
                    self.noUpdate.emit()

        except Exception as e:
            logger.warning("Failed to check for updates: %s", e)
            self.updateError.emit(str(e))
