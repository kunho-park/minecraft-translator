"""Standalone tool to build vanilla Minecraft glossary.

This is a convenience wrapper that can be run directly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.glossary.vanilla_builder import main

if __name__ == "__main__":
    main()
